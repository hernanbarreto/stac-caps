# Engine 2: Persistence - Data Interfaces
# Defines Track, TrackState, and related structures

from dataclasses import dataclass, field
from enum import Enum
from typing import Tuple, Optional, List
import numpy as np


class TrackState(Enum):
    """Track lifecycle states."""
    TENTATIVE = 0    # New, unconfirmed (< 3 matches)
    ACTIVE = 1       # Confirmed, visible
    GHOST = 2        # Temporarily lost (occluded)
    DELETED = 3      # Removed from tracking


class Category(Enum):
    """Object category from Engine 1B."""
    PERSON = 'PERSON'
    KNOWN = 'KNOWN'
    UNKNOWN = 'UNKNOWN'


@dataclass
class BBox3D:
    """3D bounding box representation."""
    x: float
    y: float
    z: float
    width: float
    height: float
    depth: float


@dataclass
class Track:
    """
    Complete track representation with all metadata.
    
    Includes identity, spatial, temporal, appearance, and quality metrics.
    """
    # Identity
    track_id: int
    state: TrackState = TrackState.TENTATIVE
    category: Category = Category.UNKNOWN
    
    # Spatial
    bbox_3d: Optional[BBox3D] = None
    velocity: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    
    # Temporal
    age: int = 0
    time_since_update: int = 0
    
    # Appearance (EMA updated)
    features: np.ndarray = field(default_factory=lambda: np.zeros(512))
    
    # Quality Metrics
    quality_score: float = 0.0
    match_frequency: float = 0.0
    confidence: float = 0.0
    
    # Cache References
    smpl_ref: Optional[int] = None      # Cache key for Engine 1B (PERSON)
    ply_ref: Optional[str] = None       # PLY template reference (KNOWN)
    
    # History
    history: List = field(default_factory=list)
    
    def compute_quality_score(self) -> float:
        """
        Compute quality score: weighted combination of reliability metrics.
        Range: 0.0 (poor) to 1.0 (excellent)
        """
        age_factor = min(self.age / 30, 1.0)
        match_factor = self.match_frequency
        conf_factor = self.confidence
        recency_factor = 1.0 - (self.time_since_update / 30)
        
        self.quality_score = (
            0.3 * age_factor +
            0.3 * match_factor +
            0.2 * conf_factor +
            0.2 * max(recency_factor, 0)
        )
        return self.quality_score


@dataclass
class TrackingInput:
    """Input to Engine 2 from Engine 1B."""
    detections: List
    frame: np.ndarray
    timestamp: float


@dataclass
class TrackingOutput:
    """Output from Engine 2."""
    tracks: List[Track]
    assignments: dict  # det_idx -> track_id
