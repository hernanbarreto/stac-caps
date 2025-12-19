# Block 0: Sensor Input - Entry Point
# Camera capture and health monitoring

from dataclasses import dataclass
from typing import Dict, Optional, Tuple
import numpy as np

from .interfaces import FrameMetadata, HealthState
from .config import SENSOR_PARAMS


class SensorManager:
    """
    Sensor input manager for monocular RGB camera.
    
    Features:
    - Primary HDR camera capture (Sony IMX490)
    - Optional secondary telephoto camera
    - Continuous health monitoring
    - ISP pipeline management
    
    Timing: 16 ms per frame (60 fps)
    """
    
    def __init__(self):
        self.params = SENSOR_PARAMS
        self.frame_counter = 0
        self.prev_frames = []
        
        # Components
        self._primary_camera = None
        self._secondary_camera = None
        self._health_monitor = None
    
    def capture(self) -> Dict:
        """
        Capture frame from primary camera.
        
        Returns:
            Dict with 'frame', 'metadata', 'health_status'
        """
        # 1. Capture from camera
        frame = self._capture_primary()
        
        # 2. Generate metadata
        metadata = self._generate_metadata()
        
        # 3. Check sensor health
        health_status = self._check_health(metadata)
        
        # 4. Store for history
        self.prev_frames.append(metadata)
        if len(self.prev_frames) > 5:
            self.prev_frames.pop(0)
        
        self.frame_counter += 1
        
        return {
            'frame': frame,
            'metadata': metadata,
            'health_status': health_status
        }
    
    def _capture_primary(self) -> np.ndarray:
        """Capture from primary HDR camera. (16 ms @ 60fps)"""
        from .camera.primary import PrimaryCamera
        if self._primary_camera is None:
            self._primary_camera = PrimaryCamera()
        return self._primary_camera.capture()
    
    def _capture_secondary(self) -> Optional[np.ndarray]:
        """Capture from secondary telephoto camera (optional)."""
        if not self.params['secondary_camera']['enabled']:
            return None
        from .camera.secondary import SecondaryCamera
        if self._secondary_camera is None:
            self._secondary_camera = SecondaryCamera()
        return self._secondary_camera.capture()
    
    def _generate_metadata(self) -> FrameMetadata:
        """Generate frame metadata."""
        import time
        return FrameMetadata(
            timestamp=time.time() * 1e6,  # microseconds
            frame_id=self.frame_counter,
            exposure_ms=16.0,
            gain_db=0.0,
            temperature_c=40.0,
            hdr_enabled=self.params['primary_camera']['hdr_enabled']
        )
    
    def _check_health(self, metadata: FrameMetadata) -> HealthState:
        """Check sensor health status. (<1 ms)"""
        from .health.monitor import check_sensor_health
        return check_sensor_health(metadata, self.prev_frames)
    
    def initialize(self):
        """Initialize camera and ISP."""
        pass
    
    def shutdown(self):
        """Clean shutdown of sensors."""
        pass
