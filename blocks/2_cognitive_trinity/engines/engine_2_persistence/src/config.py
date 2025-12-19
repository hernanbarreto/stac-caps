# Engine 2: Persistence - Configuration
# System parameters and thresholds

PERSISTENCE_PARAMS = {
    # Track limits
    'max_tracks': 50,               # LRU cache size
    'max_detections_per_frame': 30,
    'history_length': 10,           # Frames of history
    
    # Track lifecycle
    'ghost_max_age': 30,            # Frames as ghost before deletion
    'tentative_threshold': 3,       # Frames to confirm track
    
    # ReID
    'reid_model': 'OSNet-x0.25',
    'embedding_dim': 512,
    'match_threshold': 0.4,         # Cosine similarity threshold
    'ema_alpha': 0.7,               # Embedding update rate
    
    # Association
    'iou_threshold': 0.3,
    'max_distance': 100.0,          # Max distance for matching (meters)
    
    # Kalman
    'confidence_decay': 0.95,       # Ghost confidence decay per frame
    'process_noise_scale': 1.0,
    
    # Performance
    'batch_size_reid': 16,          # Batch ReID for efficiency
}

# Timing budget (ms)
TIMING = {
    'osnet_reid': 2,
    'kalman_predict': 1,
    'association': 1,
    'update': 1,
    'total': 5
}
