# Block 0: Primary Camera Interface
# Sony IMX490 HDR camera

import numpy as np
from ..config import SENSOR_PARAMS


class PrimaryCamera:
    """
    Primary HDR camera interface (Sony IMX490).
    
    Specs:
    - Resolution: 1920×1080 @ 60fps
    - HDR: 120dB dynamic range
    - Interface: GMSL2
    - FoV: 90° wide angle
    """
    
    def __init__(self):
        self.config = SENSOR_PARAMS['primary_camera']
        self.resolution = self.config['resolution']
        self.fps = self.config['fps']
        self.hdr_enabled = self.config['hdr_enabled']
        self._initialized = False
    
    def initialize(self):
        """Initialize camera hardware."""
        # TODO: GMSL2 initialization
        self._initialized = True
    
    def capture(self) -> np.ndarray:
        """
        Capture single frame.
        
        Returns:
            RGB frame [H, W, 3] uint8
        """
        if not self._initialized:
            self.initialize()
        
        # TODO: Actual camera capture
        # For now, return placeholder
        h, w = self.resolution[1], self.resolution[0]
        return np.zeros((h, w, 3), dtype=np.uint8)
    
    def set_exposure(self, exposure_ms: float):
        """Set exposure time."""
        pass
    
    def set_gain(self, gain_db: float):
        """Set sensor gain."""
        pass
    
    def get_temperature(self) -> float:
        """Get sensor temperature in Celsius."""
        return 40.0  # Placeholder
    
    def shutdown(self):
        """Clean shutdown."""
        self._initialized = False
