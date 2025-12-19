"""Engine 1B: Semantic - Configuration"""

SEMANTIC_PARAMS = {
    # Category thresholds
    'person_class_id': 0,
    'known_max_class_id': 50,
    
    # Detection
    'confidence_threshold': 0.5,
    'nms_threshold': 0.4,
    
    # Person branch
    'rtmpose_input_size': (256, 192),
    'smpl_params_size': 85,  # β[10] + θ[72] + t[3]
    
    # Known branch
    'ply_library_path': 'assets/ply_library/',
    
    # Unknown branch
    'async_service_host': 'localhost',
    'async_service_port': 5555,
    
    # Timing budget (ms)
    'timing': {
        'detection': 17,
        'person': 8,
        'known': 1,
        'unknown': 1,
        'total': 25
    }
}
