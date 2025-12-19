# Block 3: Fusion - Interfaces
from dataclasses import dataclass, field
from typing import List, Tuple, Optional

@dataclass
class Object3D:
    track_id: int
    position: Tuple[float, float, float]
    bbox3D: Tuple[float, float, float, float, float, float]  # x,y,z,w,h,d
    velocity: Tuple[float, float, float] = (0, 0, 0)
    category: str = 'UNKNOWN'
    representation: str = 'BBOX'  # SMPL | PLY | BBOX
    confidence: float = 1.0

@dataclass
class Scene3D:
    objects: List[Object3D] = field(default_factory=list)
    timestamp: float = 0.0
