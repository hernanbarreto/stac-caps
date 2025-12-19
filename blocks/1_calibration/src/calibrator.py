# Block 1: Calibration - Entry Point
from dataclasses import dataclass
from typing import Optional
import numpy as np
from .interfaces import CalibrationResult
from .config import CALIBRATION_PARAMS

class CalibrationManager:
    """
    Adaptive calibration for monocular vision system.
    Features: Hard initialization, Online learning, Robust fallback
    """
    def __init__(self):
        self.params = CALIBRATION_PARAMS
        self.current_calibration: Optional[CalibrationResult] = None
        self._landmark_db = None
        
    def calibrate(self, frame: np.ndarray, rail_visible: bool = True) -> CalibrationResult:
        """Main calibration pipeline."""
        if self.current_calibration is None:
            return self._hard_initialization(frame)
        elif rail_visible:
            return self._rail_calibration(frame)
        else:
            return self._landmark_fallback(frame)
    
    def _hard_initialization(self, frame) -> CalibrationResult:
        from .initialization.hard_init import hard_initialization
        return hard_initialization(frame, None)
    
    def _rail_calibration(self, frame) -> CalibrationResult:
        return self.current_calibration
    
    def _landmark_fallback(self, frame) -> CalibrationResult:
        from .fallback.occlusion import handle_occlusion
        return handle_occlusion(frame, False, self._landmark_db)
