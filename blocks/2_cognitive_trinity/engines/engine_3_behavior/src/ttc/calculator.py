# Engine 3: TTC Calculator
# Time-To-Collision with confidence intervals and early exit

from typing import List, Dict
import numpy as np

from ..interfaces import TTCResult, Prediction

EMERGENCY_THRESHOLD = 1.0  # seconds


def compute_ttc_v2(
    train_state,
    predictions: List[Prediction],
    max_tracks: int = 30
) -> TTCResult:
    """
    Improved TTC with confidence intervals and early exit.
    
    Args:
        train_state: Current train position/velocity
        predictions: List of predictions for all tracks
        max_tracks: Limit for performance
        
    Returns:
        TTCResult with min, mean, max, confidence
    """
    if not predictions:
        return TTCResult(
            min=float('inf'),
            mean=float('inf'),
            max=float('inf'),
            confidence=1.0
        )
    
    # Train state
    train_pos = np.array(train_state.position) if train_state else np.zeros(3)
    train_vel = np.array(train_state.velocity) if train_state else np.array([0, 0, 10])
    
    # Sort by proximity for early exit
    sorted_preds = sorted(
        predictions,
        key=lambda p: distance_to_position(p.trajectories.get('nominal', [{}])[0], train_pos)
    )
    
    ttc_samples = []
    
    for pred in sorted_preds[:max_tracks]:
        for scenario in ['optimistic', 'nominal', 'pessimistic']:
            traj = pred.trajectories.get(scenario, [])
            
            for point in traj:
                t = point.get('timestamp', 0)
                obj_pos = np.array(point.get('position', (0, 0, 10)))
                
                # Train position at time t
                train_future = train_pos + train_vel * t
                
                # Distance at time t
                distance = np.linalg.norm(obj_pos - train_future)
                
                # Safety margin
                margin = get_safety_margin(pred.intent)
                
                if distance < margin:
                    ttc_samples.append(t)
                    
                    # EARLY EXIT for emergency
                    if t < EMERGENCY_THRESHOLD:
                        return TTCResult(
                            min=t,
                            mean=t,
                            max=t,
                            confidence=0.99  # High confidence emergency
                        )
    
    if not ttc_samples:
        return TTCResult(
            min=float('inf'),
            mean=float('inf'),
            max=float('inf'),
            confidence=1.0
        )
    
    # Compute confidence interval
    ttc_min = float(np.min(ttc_samples))
    ttc_mean = float(np.mean(ttc_samples))
    ttc_max = float(np.max(ttc_samples))
    
    # Confidence based on spread
    spread = ttc_max - ttc_min
    confidence = float(np.clip(1.0 - spread / 10.0, 0.3, 1.0))
    
    return TTCResult(
        min=ttc_min,
        mean=ttc_mean,
        max=ttc_max,
        confidence=confidence
    )


def distance_to_position(point: Dict, position: np.ndarray) -> float:
    """Compute distance from trajectory point to position."""
    if not point or 'position' not in point:
        return float('inf')
    obj_pos = np.array(point['position'])
    return float(np.linalg.norm(obj_pos - position))


def get_safety_margin(intent) -> float:
    """Get safety margin based on intent."""
    if intent is None:
        return 5.0
    
    margins = {
        'STATIC': 5.0,
        'LEAVING': 4.0,
        'APPROACHING': 7.5,
        'CROSSING': 10.0
    }
    margin = margins.get(intent.state, 5.0)
    
    if intent.distraction_prob > 0.5:
        margin *= 1.25
    
    return margin
