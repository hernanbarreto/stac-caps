# Block 0: Sensor Input - Data Interfaces
# FrameMetadata, HealthState, and related structures

from dataclasses import dataclass
from enum import Enum
from typing import Optional
import numpy as np


class HealthState(Enum):
    """Sensor health states."""
    OK = 'OK'               # All parameters normal
    DEGRADED = 'DEGRADED'   # Minor issues (fog, temp warning)
    FAULT = 'FAULT'         # Critical failure (no signal, lens blocked)


@dataclass
class FrameMetadata:
    """
    Metadata for captured frame.
    """
    timestamp: float        # Capture time (µs precision)
    frame_id: int           # Sequential counter
    exposure_ms: float      # Current exposure
    gain_db: float          # Current gain
    temperature_c: float    # Sensor temperature
    hdr_enabled: bool       # HDR mode active


@dataclass
class CameraSpec:
    """Camera hardware specification."""
    resolution: tuple       # (width, height)
    fps: int
    hdr_enabled: bool
    interface: str          # 'GMSL2' | 'Ethernet'
    fov: float              # Field of view (degrees)


@dataclass
class SensorInput:
    """Complete sensor input package."""
    frame: np.ndarray       # [H, W, 3] RGB frame
    metadata: FrameMetadata
    health_status: HealthState


@dataclass
class SecondaryFrame:
    """Optional secondary camera frame."""
    frame: np.ndarray
    metadata: FrameMetadata
    purpose: str = 'long_range'
