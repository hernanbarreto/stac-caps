# Engine 3: Behavior - Configuration
# System parameters and thresholds

ENGINE3_PARAMS = {
    # Prediction horizons
    'horizons': [1.0, 2.0, 3.0, 4.0, 5.0],  # seconds
    'max_horizon': 5.0,
    
    # Theory of Mind
    'intent_ema_alpha': 0.7,          # Intent smoothing
    'intent_states': ['STATIC', 'LEAVING', 'APPROACHING', 'CROSSING'],
    
    # Risk calculation
    'risk_ema_alpha': 0.7,            # Risk smoothing
    'risk_weights': {
        'ttc': 0.35,
        'intent': 0.25,
        'distraction': 0.15,
        'category': 0.10,
        'quality': 0.15
    },
    
    # TTC
    'max_tracks_ttc': 30,             # Early exit limit
    'emergency_ttc': 1.0,             # seconds
    'warning_ttc': 3.0,               # seconds
    'caution_ttc': 5.0,               # seconds
    
    # Validation
    'validation_threshold': 1.5,       # meters divergence
    
    # Safety margins
    'base_safety_margin': 5.0,         # meters
    'margin_multipliers': {
        'STATIC': 1.0,
        'LEAVING': 0.8,
        'APPROACHING': 1.5,
        'CROSSING': 2.0
    },
    'distraction_multiplier': 1.25,
}

# Category risk weights
CATEGORY_WEIGHTS = {
    'PERSON': 1.0,
    'KNOWN': 0.7,
    'UNKNOWN': 0.3
}

# Intent risk weights
INTENT_WEIGHTS = {
    'STATIC': 0.1,
    'LEAVING': 0.2,
    'APPROACHING': 0.7,
    'CROSSING': 1.0
}

# Timing budget (ms)
TIMING = {
    'kinematic_prediction': 1,
    'smpl_pose': 1,
    'tom_inference': 1,
    'cross_validation': 1,
    'ttc_calculation': 1,
    'risk_scoring': 1,
    'total': 3
}
