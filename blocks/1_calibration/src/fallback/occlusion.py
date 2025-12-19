# Block 1: Occlusion Handler
import numpy as np
from ..interfaces import CalibrationResult

def handle_occlusion(frame, rail_visible, landmark_db) -> CalibrationResult:
    """Fallback calibration when rails are not visible."""
    if landmark_db:
        pose, num_matches = landmark_db.match_and_refine(None, None)
        if num_matches >= 4:
            return CalibrationResult(
                intrinsics=np.eye(3), extrinsics=pose,
                method='LANDMARK_FALLBACK', confidence=min(num_matches / 10, 0.9), scale_factor=0.001
            )
    return CalibrationResult(
        intrinsics=np.eye(3), extrinsics=(np.eye(3), np.zeros(3)),
        method='LAST_KNOWN', confidence=0.5, scale_factor=0.001
    )
