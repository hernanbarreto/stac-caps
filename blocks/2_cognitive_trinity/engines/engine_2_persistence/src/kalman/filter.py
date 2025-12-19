# Engine 2: Adaptive Kalman Filter
# Position/velocity prediction with adaptive noise

from typing import Tuple
import numpy as np


class AdaptiveKalman:
    """
    8-state Kalman filter for object tracking.
    
    State: [x, y, z, vx, vy, vz, w, h]
    Measurement: [x, y, z, w, h]
    
    Features:
    - Adaptive process noise based on confidence
    - Handles ghost state prediction
    - Returns uncertainty estimates
    """
    
    def __init__(self):
        # State dimension
        self.dim_x = 8  # [x, y, z, vx, vy, vz, w, h]
        self.dim_z = 5  # [x, y, z, w, h]
        
        # State and covariance
        self.x = np.zeros(self.dim_x)
        self.P = np.eye(self.dim_x) * 10
        
        # State transition matrix
        self.F = np.eye(self.dim_x)
        dt = 1.0 / 60  # 60 fps
        self.F[0, 3] = dt  # x += vx * dt
        self.F[1, 4] = dt  # y += vy * dt
        self.F[2, 5] = dt  # z += vz * dt
        
        # Measurement matrix
        self.H = np.zeros((self.dim_z, self.dim_x))
        self.H[0, 0] = 1  # x
        self.H[1, 1] = 1  # y
        self.H[2, 2] = 1  # z
        self.H[3, 6] = 1  # w
        self.H[4, 7] = 1  # h
        
        # Process noise (base)
        self.Q_base = np.eye(self.dim_x) * 0.01
        self.Q = self.Q_base.copy()
        
        # Measurement noise
        self.R = np.eye(self.dim_z) * 1.0
    
    def initialize(self, measurement: np.ndarray):
        """
        Initialize state from first measurement.
        
        Args:
            measurement: [x, y, z, w, h]
        """
        self.x[0] = measurement[0]  # x
        self.x[1] = measurement[1]  # y
        self.x[2] = measurement[2]  # z
        self.x[6] = measurement[3]  # w
        self.x[7] = measurement[4]  # h
        # velocities start at 0
        self.x[3:6] = 0
    
    def predict(self, confidence: float = 1.0) -> Tuple[np.ndarray, np.ndarray]:
        """
        Predict next state.
        
        Args:
            confidence: Track confidence (lower = more noise)
            
        Returns:
            (predicted_state, uncertainty)
        """
        # Adaptive process noise
        self.Q = self.Q_base * (1.0 / max(confidence, 0.1))
        
        # Predict
        self.x = self.F @ self.x
        self.P = self.F @ self.P @ self.F.T + self.Q
        
        # Return position and uncertainty
        position = self.x[:3]
        uncertainty = np.sqrt(np.diag(self.P)[:3])
        
        return position, uncertainty
    
    def update(self, measurement: np.ndarray) -> np.ndarray:
        """
        Update state with measurement.
        
        Args:
            measurement: [x, y, z, w, h]
            
        Returns:
            Updated state
        """
        # Kalman gain
        S = self.H @ self.P @ self.H.T + self.R
        K = self.P @ self.H.T @ np.linalg.inv(S)
        
        # Update
        y = measurement - self.H @ self.x
        self.x = self.x + K @ y
        self.P = (np.eye(self.dim_x) - K @ self.H) @ self.P
        
        return self.x.copy()
    
    def get_velocity(self) -> np.ndarray:
        """Get current velocity estimate."""
        return self.x[3:6]
    
    def get_position(self) -> np.ndarray:
        """Get current position estimate."""
        return self.x[:3]
    
    def get_acceleration(self) -> np.ndarray:
        """
        Estimate acceleration from velocity changes.
        (Simplified - returns zeros for now)
        """
        # TODO: Implement acceleration estimation
        return np.zeros(3)
