# Block 1: Hard Initialization
import numpy as np
from ..interfaces import CalibrationResult

def hard_initialization(frame, operator_clicks) -> CalibrationResult:
    """Human-assisted metric scale initialization using rail heads (1435mm gauge)."""
    # Placeholder implementation
    return CalibrationResult(
        intrinsics=np.eye(3),
        extrinsics=(np.eye(3), np.zeros(3)),
        scale_factor=0.001,
        method='HARD_INIT',
        confidence=0.99
    )
