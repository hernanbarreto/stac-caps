# Engine 3: Cross-Validation with Optical Flow
# Validate trajectory prediction with optical flow

from typing import Dict
import numpy as np

VALIDATION_THRESHOLD = 1.5  # meters divergence


def cross_validate_trajectory(
    kinematic_pred: Dict,
    optical_flow: np.ndarray,
    track
) -> str:
    """
    Validate trajectory prediction with optical flow.
    
    Args:
        kinematic_pred: Predicted trajectories (dict)
        optical_flow: Optical flow tensor [H, W, 2]
        track: Track with bbox for ROI extraction
        
    Returns:
        'VALIDATED' | 'UNCERTAIN' | 'UNVALIDATED'
    """
    if optical_flow is None:
        return 'UNVALIDATED'
    
    # Get ROI from track
    if hasattr(track, 'bbox_3d') and track.bbox_3d:
        roi = {
            'center': (track.bbox_3d.x, track.bbox_3d.y),
            'depth': track.bbox_3d.z
        }
    else:
        return 'UNVALIDATED'
    
    # Extract flow at object location
    x, y = int(roi['center'][0]), int(roi['center'][1])
    
    # Bounds check
    h, w = optical_flow.shape[:2]
    if x < 0 or x >= w or y < 0 or y >= h:
        return 'UNVALIDATED'
    
    flow_vector = optical_flow[y, x]
    
    # Convert flow to 3D velocity estimate
    flow_velocity = flow_to_velocity(flow_vector, depth=roi['depth'])
    
    # Get kinematic velocity from first prediction point
    nominal = kinematic_pred.get('nominal', [])
    if not nominal or len(nominal) < 2:
        return 'UNVALIDATED'
    
    # Estimate velocity from first two points
    p0 = np.array(nominal[0].get('position', (0, 0, 0)))
    p1 = np.array(nominal[1].get('position', (0, 0, 0)))
    t0 = nominal[0].get('timestamp', 0)
    t1 = nominal[1].get('timestamp', 1)
    
    dt = t1 - t0 if t1 != t0 else 1.0
    kinematic_velocity = (p1 - p0) / dt
    
    # Compute divergence
    divergence = np.linalg.norm(kinematic_velocity[:2] - flow_velocity[:2])
    
    if divergence > VALIDATION_THRESHOLD:
        return 'UNCERTAIN'
    
    return 'VALIDATED'


def flow_to_velocity(flow_vector: np.ndarray, depth: float) -> np.ndarray:
    """
    Convert optical flow to 3D velocity.
    
    Args:
        flow_vector: [u, v] optical flow
        depth: Depth at flow location
        
    Returns:
        [vx, vy, vz] velocity in 3D
    """
    # Assume focal length ~500 for simplicity
    fx, fy = 500, 500
    
    # Flow to 3D velocity (simplified pinhole model)
    vx = flow_vector[0] * depth / fx
    vy = flow_vector[1] * depth / fy
    vz = 0  # Z velocity from flow requires depth changes
    
    return np.array([vx, vy, vz])
