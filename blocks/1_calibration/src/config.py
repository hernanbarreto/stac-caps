# Block 1: Calibration - Configuration
CALIBRATION_PARAMS = {
    'rail': {'gauge_mm': 1435, 'detection_method': 'edge_hough', 'min_rail_length_px': 200},
    'landmarks': {'max_db_size': 1000, 'keypoint_detector': 'SuperPoint', 'match_threshold': 0.7, 'min_matches_for_pnp': 4},
    'fallback': {'occlusion_frames_to_switch': 5, 'low_confidence_threshold': 0.5}
}
