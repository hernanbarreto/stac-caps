# Block 1: Calibration - Data Interfaces
from dataclasses import dataclass
from typing import Tuple, Optional
import numpy as np

@dataclass
class CalibrationResult:
    intrinsics: np.ndarray      # [3, 3] camera matrix K
    extrinsics: Tuple           # (R, t) Rotation, translation
    scale_factor: float         # meters/pixel at rail plane
    method: str                 # HARD_INIT | RAIL_GEOMETRY | LANDMARK
    confidence: float           # [0.0, 1.0]
    landmark_count: int = 0     # Active landmarks in DB

@dataclass
class Landmark:
    descriptor: np.ndarray
    world_pos: Tuple[float, float, float]
    first_seen: float
    observations: int = 1
