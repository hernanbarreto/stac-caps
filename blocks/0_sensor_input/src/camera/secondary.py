# Block 0: Secondary Camera Interface
# Optional telephoto camera for long-range detection

import numpy as np
from ..config import SENSOR_PARAMS


class SecondaryCamera:
    """
    Secondary telephoto camera (optional).
    
    Specs:
    - Resolution: 1920×1080 @ 30fps
    - Purpose: Long-range detection (>200m)
    - FoV: 15° telephoto
    """
    
    def __init__(self):
        self.config = SENSOR_PARAMS['secondary_camera']
        self.enabled = self.config['enabled']
        self.resolution = self.config['resolution']
        self.fps = self.config['fps']
        self._initialized = False
    
    def initialize(self):
        """Initialize camera hardware."""
        if not self.enabled:
            return
        # TODO: Secondary camera initialization
        self._initialized = True
    
    def capture(self) -> np.ndarray:
        """
        Capture single frame.
        
        Returns:
            RGB frame [H, W, 3] uint8 or None if disabled
        """
        if not self.enabled:
            return None
        
        if not self._initialized:
            self.initialize()
        
        # TODO: Actual camera capture
        h, w = self.resolution[1], self.resolution[0]
        return np.zeros((h, w, 3), dtype=np.uint8)
    
    def shutdown(self):
        """Clean shutdown."""
        self._initialized = False
