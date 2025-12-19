"""
STAC-CAPS Pipeline Orchestrator
Connects all blocks and engines for frame processing
"""

import sys
from pathlib import Path
from typing import Dict, Optional, List, Tuple
import numpy as np
import time

# Add blocks to path
BLOCKS_DIR = Path(__file__).parent.parent.parent / "blocks"
sys.path.insert(0, str(BLOCKS_DIR))

from .. import config
from .model_manager import ModelManager


class Pipeline:
    """
    STAC-CAPS Processing Pipeline.
    
    Orchestrates:
    1. Block 0: Sensor Input (frame decode)
    2. Block 1: Calibration (rail geometry)
    3. Engine 1A: Depth estimation
    4. Engine 1B: Semantic detection
    5. Engine 2: Tracking
    6. Engine 3: Behavior prediction
    7. Block 3: 3D Fusion
    8. Block 5: Safety decision
    
    Total target: 50ms per frame (20 FPS)
    """
    
    def __init__(
        self,
        calibration: Dict,
        device: str = "cuda:0",
        fp16: bool = True
    ):
        self.calibration = calibration
        self.device = device
        self.fp16 = fp16
        
        # Computed from calibration
        self.scale_factor = self._compute_scale_factor()
        
        # Model manager
        self.model_manager = ModelManager()
        
        # Lazy-loaded models
        self._depth_model = None
        self._detection_model = None
        self._pose_model = None
        self._reid_model = None
        
        # Engine states
        self._tracker = None
        self._prev_tracks = []
        self._prev_intents = {}
        self._prev_risks = {}
        
        # Last result for API
        self._last_result = None
        
        # Timing stats
        self.timing = {}
    
    def _compute_scale_factor(self) -> float:
        """
        Compute meters/pixel from rail calibration.
        
        Uses track gauge (1435mm) and rail pixel distance.
        """
        left_rail = self.calibration.get("left_rail", [(0, 0), (0, 100)])
        right_rail = self.calibration.get("right_rail", [(100, 0), (100, 100)])
        gauge_mm = self.calibration.get("track_gauge_mm", 1435)
        
        # Use top points for reference
        left_x = left_rail[0][0]
        right_x = right_rail[0][0]
        
        pixel_distance = abs(right_x - left_x)
        
        if pixel_distance == 0:
            return 0.001  # Default 1mm/pixel
        
        # Scale factor: meters per pixel
        scale = (gauge_mm / 1000.0) / pixel_distance
        
        return scale
    
    def _load_models(self):
        """Load all required models."""
        print("Loading models...")
        
        # Load depth model
        if self._depth_model is None:
            try:
                self._depth_model = self.model_manager.load_onnx_model("depth_anything_v2")
                print("  ✓ Depth model loaded")
            except Exception as e:
                print(f"  ✗ Depth model failed: {e}")
        
        # Load detection model
        if self._detection_model is None:
            try:
                self._detection_model = self.model_manager.load_onnx_model("rt_detr")
                print("  ✓ Detection model loaded")
            except Exception as e:
                print(f"  ✗ Detection model failed: {e}")
        
        # Load pose model
        if self._pose_model is None:
            try:
                self._pose_model = self.model_manager.load_onnx_model("rtmpose")
                print("  ✓ Pose model loaded")
            except Exception as e:
                print(f"  ✗ Pose model failed: {e}")
        
        # Load ReID model
        if self._reid_model is None:
            try:
                self._reid_model = self.model_manager.load_onnx_model("osnet")
                print("  ✓ ReID model loaded")
            except Exception as e:
                print(f"  ✗ ReID model failed: {e}")
    
    def process_frame(self, frame: np.ndarray, frame_idx: int = 0) -> Dict:
        """
        Process a single frame through the full pipeline.
        
        Args:
            frame: RGB frame [H, W, 3]
            frame_idx: Frame index
            
        Returns:
            Dict with detections, tracks, predictions, ttc, action
        """
        # Ensure models are loaded
        if self._depth_model is None:
            self._load_models()
        
        total_start = time.time()
        
        # 1. Depth Estimation (22ms budget)
        t0 = time.time()
        depth_map = self._run_depth(frame)
        self.timing["depth"] = (time.time() - t0) * 1000
        
        # 2. Semantic Detection (25ms budget)
        t0 = time.time()
        detections = self._run_detection(frame)
        self.timing["detection"] = (time.time() - t0) * 1000
        
        # 3. Pose Estimation for persons
        t0 = time.time()
        detections = self._add_pose(frame, detections)
        self.timing["pose"] = (time.time() - t0) * 1000
        
        # 4. Tracking (5ms budget)
        t0 = time.time()
        tracks = self._run_tracking(frame, detections)
        self.timing["tracking"] = (time.time() - t0) * 1000
        
        # 5. Behavior Prediction (3ms budget)
        t0 = time.time()
        predictions = self._run_behavior(tracks)
        self.timing["behavior"] = (time.time() - t0) * 1000
        
        # 6. 3D Fusion (3ms budget)
        t0 = time.time()
        objects_3d = self._run_fusion(depth_map, detections, tracks)
        self.timing["fusion"] = (time.time() - t0) * 1000
        
        # 7. Safety Decision (7ms budget)
        t0 = time.time()
        safety = self._run_safety(predictions)
        self.timing["safety"] = (time.time() - t0) * 1000
        
        # Total timing
        self.timing["total"] = (time.time() - total_start) * 1000
        
        # Build result
        result = {
            "frame_idx": frame_idx,
            "detections": detections,
            "tracks": tracks,
            "predictions": predictions,
            "objects_3d": objects_3d,
            "depth_map": depth_map,
            "ttc": safety.get("ttc_min", float("inf")),
            "action": safety.get("action", "CLEAR"),
            "risk_scores": safety.get("risk_scores", {}),
            "timing": self.timing.copy()
        }
        
        self._last_result = result
        return result
    
    def _run_depth(self, frame: np.ndarray) -> np.ndarray:
        """Run depth estimation."""
        if self._depth_model is None:
            return np.ones((frame.shape[0], frame.shape[1]), dtype=np.float32) * 10
        
        # Preprocess
        input_size = (518, 518)
        import cv2
        resized = cv2.resize(frame, input_size)
        normalized = resized.astype(np.float32) / 255.0
        mean = np.array([0.485, 0.456, 0.406])
        std = np.array([0.229, 0.224, 0.225])
        normalized = (normalized - mean) / std
        tensor = normalized.transpose(2, 0, 1)[np.newaxis, ...].astype(np.float32)
        
        # Inference
        input_name = self._depth_model.get_inputs()[0].name
        output = self._depth_model.run(None, {input_name: tensor})[0]
        
        # Postprocess
        depth = output.squeeze()
        depth = cv2.resize(depth, (frame.shape[1], frame.shape[0]))
        
        # Apply scale factor
        depth_meters = depth * self.scale_factor * 100  # Rough scale
        
        return depth_meters
    
    def _run_detection(self, frame: np.ndarray) -> List[Dict]:
        """Run object detection."""
        if self._detection_model is None:
            return []
        
        # Preprocess
        import cv2
        input_size = (640, 640)
        resized = cv2.resize(frame, input_size)
        tensor = resized.astype(np.float32) / 255.0
        tensor = tensor.transpose(2, 0, 1)[np.newaxis, ...].astype(np.float32)
        
        # Inference
        input_name = self._detection_model.get_inputs()[0].name
        outputs = self._detection_model.run(None, {input_name: tensor})
        
        # Parse output (format depends on model)
        detections = self._parse_detections(outputs, frame.shape)
        
        return detections
    
    def _parse_detections(self, outputs, frame_shape) -> List[Dict]:
        """Parse detection model output."""
        detections = []
        
        # This is a placeholder - actual parsing depends on model format
        # For now, return empty list
        
        return detections
    
    def _add_pose(self, frame: np.ndarray, detections: List[Dict]) -> List[Dict]:
        """Add pose estimation for person detections."""
        if self._pose_model is None:
            return detections
        
        for det in detections:
            if det.get("category") == "PERSON":
                # Run pose on crop
                det["pose_keypoints"] = None  # Placeholder
        
        return detections
    
    def _run_tracking(self, frame: np.ndarray, detections: List[Dict]) -> List[Dict]:
        """Run multi-object tracking."""
        tracks = []
        
        # Simple ID assignment for now
        for i, det in enumerate(detections):
            tracks.append({
                "track_id": i,
                "bbox": det.get("bbox", [0, 0, 100, 100]),
                "category": det.get("category", "UNKNOWN"),
                "confidence": det.get("confidence", 0.5),
                "velocity": (0, 0, 0),
                "age": 1
            })
        
        self._prev_tracks = tracks
        return tracks
    
    def _run_behavior(self, tracks: List[Dict]) -> List[Dict]:
        """Run behavior prediction."""
        predictions = []
        
        for track in tracks:
            predictions.append({
                "track_id": track["track_id"],
                "intent": "STATIC",
                "ttc": float("inf"),
                "risk_score": 0.1,
                "distraction_prob": 0.0
            })
        
        return predictions
    
    def _run_fusion(
        self,
        depth_map: np.ndarray,
        detections: List[Dict],
        tracks: List[Dict]
    ) -> List[Dict]:
        """Run 3D fusion."""
        objects_3d = []
        
        for track in tracks:
            bbox = track.get("bbox", [0, 0, 100, 100])
            cx = (bbox[0] + bbox[2]) / 2
            cy = (bbox[1] + bbox[3]) / 2
            
            # Sample depth at center
            if 0 <= int(cy) < depth_map.shape[0] and 0 <= int(cx) < depth_map.shape[1]:
                z = float(depth_map[int(cy), int(cx)])
            else:
                z = 10.0
            
            objects_3d.append({
                "track_id": track["track_id"],
                "position": (cx * self.scale_factor, cy * self.scale_factor, z),
                "bbox_3d": (0, 0, z, 1, 2, 1)  # Placeholder
            })
        
        return objects_3d
    
    def _run_safety(self, predictions: List[Dict]) -> Dict:
        """Run safety decision."""
        if not predictions:
            return {
                "action": "CLEAR",
                "ttc_min": float("inf"),
                "risk_scores": {}
            }
        
        # Find minimum TTC
        ttc_min = min((p["ttc"] for p in predictions), default=float("inf"))
        
        # Aggregate risk
        risk_scores = {p["track_id"]: p["risk_score"] for p in predictions}
        max_risk = max(risk_scores.values(), default=0)
        
        # Decision
        if ttc_min < 1.0 or max_risk > 0.8:
            action = "EMERGENCY"
        elif ttc_min < 2.0:
            action = "SERVICE"
        elif ttc_min < 3.0:
            action = "WARNING"
        elif ttc_min < 5.0:
            action = "CAUTION"
        else:
            action = "CLEAR"
        
        return {
            "action": action,
            "ttc_min": ttc_min,
            "risk_scores": risk_scores
        }
    
    def get_last_result(self) -> Optional[Dict]:
        """Get last processing result."""
        return self._last_result
    
    def get_timing_stats(self) -> Dict:
        """Get timing statistics."""
        return self.timing
