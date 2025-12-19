# Engine 3: Behavior - Entry Point
# Prediction and risk assessment engine

from dataclasses import dataclass
from typing import List, Dict, Optional
import numpy as np

from .interfaces import Prediction, Trajectory, Intent, TTCResult
from .config import ENGINE3_PARAMS


class Engine3Behavior:
    """
    Behavior prediction engine combining:
    - Kinematic trajectory forecasting with acceleration
    - Theory of Mind (ToM) intent inference
    - Risk scoring with confidence intervals
    - Cross-validation with optical flow
    
    Timing: 3 ms per frame
    """
    
    def __init__(self):
        self.params = ENGINE3_PARAMS
        self.prev_intents: Dict[int, List[Intent]] = {}
        self.prev_risks: Dict[int, float] = {}
    
    def process(
        self,
        tracks: List,
        train_state: "TrainState",
        danger_zones: List = None,
        scene_context: str = "OPEN_TRACK",
        optical_flow: np.ndarray = None
    ) -> Dict:
        """
        Process tracks and generate predictions.
        
        Args:
            tracks: List of Track from Engine 2
            train_state: Current train dynamics
            danger_zones: Defined danger areas
            scene_context: PLATFORM | CROSSING | OPEN_TRACK
            optical_flow: Optional optical flow for validation
            
        Returns:
            Dict with predictions, risk_scores, ttc, safety_margin, validation_status
        """
        predictions = []
        risk_scores = {}
        
        for track in tracks:
            # 1. Kinematic prediction (1 ms total)
            trajectories = self._predict_kinematic(track)
            
            # 2. Pose prediction (for persons)
            pose_pred = None
            if track.category == 'PERSON' and hasattr(track, 'smpl_params'):
                pose_pred = self._predict_pose(track)
            
            # 3. Theory of Mind intent (1 ms total)
            intent = self._infer_intent(track, scene_context, train_state)
            
            # 4. Create prediction
            pred = Prediction(
                track_id=track.track_id,
                trajectories=trajectories,
                intent=intent,
                collision_prob=0.0,  # Computed later
                ttc=float('inf'),
                risk_score=0.0,
                validated=False
            )
            
            # 5. Cross-validate with optical flow
            if optical_flow is not None:
                pred.validated = self._cross_validate(
                    trajectories, optical_flow, track
                )
            
            predictions.append(pred)
        
        # 6. Compute TTC with confidence intervals
        ttc_result = self._compute_ttc(train_state, predictions)
        
        # 7. Calculate risk scores
        for pred in predictions:
            risk = self._compute_risk(
                tracks[0] if tracks else None,
                pred.intent,
                ttc_result,
                self.prev_risks.get(pred.track_id)
            )
            risk_scores[pred.track_id] = risk
            pred.risk_score = risk
            self.prev_risks[pred.track_id] = risk
        
        # 8. Determine validation status
        validation_status = self._determine_validation(predictions)
        
        # 9. Compute safety margin
        safety_margin = self._compute_safety_margin(predictions)
        
        return {
            'predictions': predictions,
            'risk_scores': risk_scores,
            'ttc': ttc_result,
            'safety_margin': safety_margin,
            'validation_status': validation_status
        }
    
    def _predict_kinematic(self, track) -> Dict[str, List]:
        """Constant acceleration trajectory prediction. (1 ms)"""
        from .kinematic.predictor import predict_kinematic_v2
        return predict_kinematic_v2(track, self.params['horizons'])
    
    def _predict_pose(self, track) -> Optional[Dict]:
        """SMPL pose-based prediction."""
        from .pose.smpl_predictor import predict_from_pose_v2
        if hasattr(track, 'smpl_params') and hasattr(track, 'smpl_history'):
            return predict_from_pose_v2(
                track.smpl_params,
                track.smpl_history,
                track.velocity
            )
        return None
    
    def _infer_intent(self, track, context: str, train_state) -> Intent:
        """Theory of Mind intent inference."""
        from .tom.intent import infer_intent_v2
        intent_history = self.prev_intents.get(track.track_id, [])
        intent = infer_intent_v2(track, None, context, intent_history, train_state)
        
        # Update history
        if track.track_id not in self.prev_intents:
            self.prev_intents[track.track_id] = []
        self.prev_intents[track.track_id].append(intent)
        self.prev_intents[track.track_id] = self.prev_intents[track.track_id][-5:]
        
        return intent
    
    def _cross_validate(self, trajectories, optical_flow, track) -> bool:
        """Validate prediction with optical flow."""
        from .validation.optical_flow import cross_validate_trajectory
        result = cross_validate_trajectory(trajectories, optical_flow, track)
        return result == 'VALIDATED'
    
    def _compute_ttc(self, train_state, predictions) -> TTCResult:
        """TTC calculation with confidence intervals."""
        from .ttc.calculator import compute_ttc_v2
        return compute_ttc_v2(train_state, predictions, self.params['max_tracks_ttc'])
    
    def _compute_risk(self, track, intent, ttc_result, prev_risk) -> float:
        """Risk score calculation."""
        from .risk.scorer import compute_risk_score_v2
        return compute_risk_score_v2(track, intent, ttc_result, prev_risk)
    
    def _determine_validation(self, predictions) -> str:
        """Determine overall validation status."""
        if not predictions:
            return 'OK'
        validated_count = sum(1 for p in predictions if p.validated)
        if validated_count == len(predictions):
            return 'VALIDATED'
        elif validated_count > 0:
            return 'PARTIAL'
        return 'UNCERTAIN'
    
    def _compute_safety_margin(self, predictions) -> float:
        """Compute adjusted safety margin based on intents."""
        base = self.params['base_safety_margin']
        max_multiplier = 1.0
        
        for pred in predictions:
            if pred.intent.state == 'CROSSING':
                multiplier = 2.0
            elif pred.intent.state == 'APPROACHING':
                multiplier = 1.5
            elif pred.intent.state == 'LEAVING':
                multiplier = 0.8
            else:
                multiplier = 1.0
            
            if pred.intent.distraction_prob > 0.5:
                multiplier *= 1.25
            
            max_multiplier = max(max_multiplier, multiplier)
        
        return base * max_multiplier
