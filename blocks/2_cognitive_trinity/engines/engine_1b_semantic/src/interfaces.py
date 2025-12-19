"""
Engine 1B: Semantic - Data Interfaces

TRACEABILITY:
  - Architecture: engine_1b_semantic/arquitectura.svg#comp_input, #comp_output
"""

from dataclasses import dataclass, field
from typing import List, Optional
from enum import Enum
import numpy as np


class Category(Enum):
    """Detection category (3-way classification)."""
    PERSONA = 0      # class_id = 0
    CONOCIDO = 1     # class_id 1-50
    DESCONOCIDO = 2  # class_id > 50


@dataclass
class SemanticInput:
    """
    Input data for Engine 1B.
    
    TRACEABILITY: arquitectura.svg#comp_input
    """
    frame: np.ndarray              # [H, W, 3] RGB
    depth_map: np.ndarray          # [H, W] from Engine 1A
    point_cloud: Optional[np.ndarray] = None  # [H, W, 3] optional


@dataclass
class BBox2D:
    """2D bounding box."""
    x: float
    y: float
    width: float
    height: float


@dataclass  
class BBox3D:
    """3D bounding box - ALL categories have this."""
    center: np.ndarray             # [x, y, z]
    dimensions: np.ndarray         # [width, height, depth]
    orientation: float = 0.0       # Yaw angle


@dataclass
class Detection:
    """
    Single unified detection.
    
    TRACEABILITY: flujo.svg UNIFIED DETECTION OUTPUT
    """
    category: Category
    class_id: int
    confidence: float
    bbox2d: BBox2D
    bbox3d: BBox3D                 # Always present for TTC
    track_id: Optional[int] = None
    
    # Category-specific data
    smpl_params: Optional[np.ndarray] = None     # PERSONA: β[10] + θ[72] + t[3]
    ply_ref: Optional[str] = None                 # CONOCIDO: "train_generic.ply"
    # DESCONOCIDO: just bbox3d (no extra data)


@dataclass
class UnknownTrigger:
    """Async trigger for external PLY reconstruction."""
    detection_id: int
    bbox2d: BBox2D
    image_crop: np.ndarray
    timestamp: float


@dataclass
class SemanticOutput:
    """
    Output data from Engine 1B.
    
    TRACEABILITY: arquitectura.svg#comp_output, flujo.svg FINAL OUTPUT
    """
    detections: List[Detection] = field(default_factory=list)
    unknown_triggers: List[UnknownTrigger] = field(default_factory=list)
