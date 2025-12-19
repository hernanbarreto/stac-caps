# Block 0: Sensor Input - Configuration
# Camera and health monitoring parameters

SENSOR_PARAMS = {
    'primary_camera': {
        'sensor': 'Sony IMX490',
        'resolution': (1920, 1080),
        'fps': 60,
        'hdr_enabled': True,
        'dynamic_range_db': 120,
        'interface': 'GMSL2',
        'fov': 90  # degrees
    },
    'secondary_camera': {
        'enabled': False,  # Optional
        'resolution': (1920, 1080),
        'fps': 30,
        'fov': 15,  # Telephoto
        'purpose': 'long_range'
    },
    'health': {
        'thermal_warning_c': 80,
        'thermal_critical_c': 85,
        'fps_jitter_tolerance_ms': 5,
        'min_brightness_threshold': 10,
        'max_brightness_threshold': 245
    },
    'isp': {
        'demosaic_method': 'bilinear',
        'denoise_strength': 0.5,
        'hdr_tone_mapping': 'reinhard',
        'white_balance': 'auto',
        'gamma': 2.2
    }
}

# Expected timing
EXPECTED_FRAME_DELTA_US = 16667  # 60 fps = 16.67 ms

# Timing budget (ms)
TIMING = {
    'camera_capture': 16.67,
    'isp_processing': 0,  # On-chip, parallel
    'dma_transfer': 2,
    'health_check': 1,
    'total_effective': 16
}
