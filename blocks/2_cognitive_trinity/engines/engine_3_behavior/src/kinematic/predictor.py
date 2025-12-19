# Engine 3: Kinematic Trajectory Predictor
# Constant acceleration model for trajectory forecasting

from typing import List, Dict, Tuple
import numpy as np


def predict_kinematic_v2(
    track,
    horizons: List[float] = [1.0, 2.0, 3.0, 4.0, 5.0]
) -> Dict[str, List]:
    """
    Constant ACCELERATION trajectory prediction.
    
    x(t) = x₀ + v₀×t + 0.5×a×t²
    
    Args:
        track: Track object with bbox_3d, velocity, acceleration
        horizons: Time points to predict (seconds)
        
    Returns:
        Dict with 'optimistic', 'nominal', 'pessimistic' trajectories
    """
    # Extract current state
    if hasattr(track, 'bbox_3d') and track.bbox_3d:
        x, y, z = track.bbox_3d.x, track.bbox_3d.y, track.bbox_3d.z
    else:
        x, y, z = 0.0, 0.0, 10.0  # Default forward position
    
    vx, vy, vz = track.velocity if hasattr(track, 'velocity') else (0, 0, 0)
    
    # Get acceleration if available
    if hasattr(track, 'acceleration'):
        ax, ay, az = track.acceleration
    else:
        ax, ay, az = 0.0, 0.0, 0.0
    
    trajectories = {
        'optimistic': [],
        'nominal': [],
        'pessimistic': []
    }
    
    for t in horizons:
        # Base prediction with constant acceleration
        future_x = x + vx * t + 0.5 * ax * t**2
        future_y = y + vy * t + 0.5 * ay * t**2
        future_z = z + vz * t + 0.5 * az * t**2
        
        # Uncertainty grows with t²
        uncertainty = 0.1 * t**2
        
        # Nominal trajectory
        trajectories['nominal'].append({
            'position': (future_x, future_y, future_z),
            'timestamp': t,
            'uncertainty': uncertainty
        })
        
        # Optimistic: slower approach (object moving away)
        trajectories['optimistic'].append({
            'position': (future_x * 0.9, future_y * 0.9, future_z * 1.1),
            'timestamp': t,
            'uncertainty': uncertainty
        })
        
        # Pessimistic: faster approach (object moving towards)
        trajectories['pessimistic'].append({
            'position': (future_x * 1.1, future_y * 1.1, future_z * 0.9),
            'timestamp': t,
            'uncertainty': uncertainty
        })
    
    return trajectories


def extrapolate_position(
    current_pos: Tuple[float, float, float],
    velocity: Tuple[float, float, float],
    dt: float
) -> Tuple[float, float, float]:
    """
    Simple linear extrapolation.
    
    Args:
        current_pos: Current (x, y, z)
        velocity: Current (vx, vy, vz)
        dt: Time delta
        
    Returns:
        Future (x, y, z)
    """
    return (
        current_pos[0] + velocity[0] * dt,
        current_pos[1] + velocity[1] * dt,
        current_pos[2] + velocity[2] * dt
    )
