# Block 0: Sensor Health Monitor
# Continuous sensor quality checks

from typing import List
from ..interfaces import FrameMetadata, HealthState
from ..config import SENSOR_PARAMS, EXPECTED_FRAME_DELTA_US


def check_sensor_health(
    metadata: FrameMetadata,
    prev_frames: List[FrameMetadata]
) -> HealthState:
    """
    Continuous sensor health monitoring.
    
    Checks:
    - Temperature
    - FPS jitter
    - Lens blockage (uniformly dark frame)
    
    Args:
        metadata: Current frame metadata
        prev_frames: Previous frame metadata list
        
    Returns:
        HealthState: OK | DEGRADED | FAULT
    """
    health_params = SENSOR_PARAMS['health']
    issues = []
    
    # Temperature check
    if metadata.temperature_c > health_params['thermal_critical_c']:
        issues.append('THERMAL_CRITICAL')
    elif metadata.temperature_c > health_params['thermal_warning_c']:
        issues.append('THERMAL_WARNING')
    
    # FPS jitter check
    if prev_frames:
        frame_delta = metadata.timestamp - prev_frames[-1].timestamp
        expected_delta = EXPECTED_FRAME_DELTA_US
        jitter_ms = abs(frame_delta - expected_delta) / 1000
        
        if jitter_ms > health_params['fps_jitter_tolerance_ms']:
            issues.append('FPS_JITTER')
    
    # Determine health state
    critical_issues = ['THERMAL_CRITICAL', 'LENS_BLOCKED', 'NO_SIGNAL']
    
    if any(issue in critical_issues for issue in issues):
        return HealthState.FAULT
    elif issues:
        return HealthState.DEGRADED
    
    return HealthState.OK


def is_uniformly_dark(frame) -> bool:
    """
    Check if frame is uniformly dark (lens blocked).
    
    Args:
        frame: RGB frame
        
    Returns:
        True if lens appears blocked
    """
    if frame is None:
        return True
    
    # TODO: Implement brightness analysis
    return False


def is_uniformly_bright(frame) -> bool:
    """
    Check if frame is uniformly bright (saturation).
    
    Args:
        frame: RGB frame
        
    Returns:
        True if frame is saturated
    """
    if frame is None:
        return False
    
    # TODO: Implement brightness analysis
    return False
