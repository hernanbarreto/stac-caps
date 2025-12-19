"""
Engine 1A: Depth - Configuration Parameters

TRACEABILITY:
  - Spec: engine_1a_depth/spec.md → System Limits
"""

DEPTH_PARAMS = {
    # Range limits (meters)
    'max_range': 200.0,
    'min_range': 0.5,
    
    # Inference
    'input_size': (518, 518),      # DepthAnything-v2 input resolution
    
    # Outlier detection (Step 5)
    'outlier_kernel_size': 3,      # Median filter kernel
    'outlier_threshold': 0.2,      # 20% deviation threshold
    
    # Guided filter (Step 6)
    'guided_radius': 2,            # Filter radius in pixels
    'guided_eps': 0.01,            # Regularization epsilon
    
    # Temporal smoothing (Step 7)
    'temporal_alpha': 0.7,         # EMA weight (favor current frame)
    
    # Confidence weights (Step 10)
    'confidence_weights': {
        'range': 0.4,
        'texture': 0.2,
        'edge': 0.2,
        'temporal': 0.2
    },
    
    # Timing budget (ms)
    'timing': {
        'resize': 2,
        'inference': 18,
        'metric_scale': 1,
        'refinement': 3,
        'point_cloud': 2,
        'total': 25
    }
}
