# Block 3: Fusion - Entry Point
from typing import List, Dict
import numpy as np
from .interfaces import Object3D, Scene3D
from .config import FUSION_PARAMS

class FusionManager:
    """3D scene fusion combining depth, semantic, and tracking data. Timing: 3ms"""
    def __init__(self):
        self.params = FUSION_PARAMS
    
    def fuse(self, depth_output, semantic_output, prev_tracks, calibration) -> Dict:
        objects_3d = []
        for det in semantic_output.get('detections', []):
            bbox3d = self._project_to_3d(det, depth_output, calibration)
            obj = Object3D(track_id=det.get('track_id', 0), position=bbox3d[:3], 
                          bbox3D=bbox3d, category=det.get('category', 'UNKNOWN'))
            objects_3d.append(obj)
        return {'scene_3d': Scene3D(objects=objects_3d), 'objects_3d': objects_3d}
    
    def _project_to_3d(self, det, depth, calib):
        from .projection.depth_to_3d import project_bbox_to_3d
        return project_bbox_to_3d(det.get('bbox2D', (0,0,100,100)), depth, calib)
