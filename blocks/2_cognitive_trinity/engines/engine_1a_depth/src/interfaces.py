"""
Engine 1A: Depth - Data Interfaces

TRACEABILITY:
  - Architecture: engine_1a_depth/arquitectura.svg#comp_input, #comp_output
  - Flow: engine_1a_depth/flujo.svg (Step 1: Input, Step 11: Output)
  - Spec: engine_1a_depth/spec.md → Inputs, Outputs
"""

from dataclasses import dataclass
from typing import Optional
import numpy as np


@dataclass
class DepthInput:
    """
    Input data for Engine 1A.
    
    TRACEABILITY: arquitectura.svg#comp_input
    """
    frame: np.ndarray              # [H, W, 3] RGB frame
    prev_depth: Optional[np.ndarray] = None  # [H, W] previous depth (for temporal smoothing)


@dataclass
class CalibrationInput:
    """
    Calibration data from Layer 1.
    
    TRACEABILITY: arquitectura.svg#comp_calib_input
    """
    intrinsics: np.ndarray         # [3, 3] camera matrix K
    scale_factor: float            # Metric scale from rail calibration
    extrinsics: Optional[np.ndarray] = None  # [4, 4] optional pose


@dataclass
class DepthOutput:
    """
    Output data from Engine 1A.
    
    TRACEABILITY: 
      - arquitectura.svg#comp_output
      - flujo.svg Step 11
      - spec.md → Outputs
    """
    depth_map: np.ndarray          # [H, W] float32 in meters
    point_cloud: np.ndarray        # [H, W, 3] XYZ coordinates
    confidence: np.ndarray         # [H, W] float32 [0.0-1.0]
    max_range: float = 200.0       # Maximum reliable range (meters)
    min_range: float = 0.5         # Minimum reliable range (meters)
    smoothed: bool = True          # Whether temporal smoothing was applied
