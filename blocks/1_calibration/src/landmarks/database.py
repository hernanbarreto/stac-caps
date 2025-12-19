# Block 1: Landmark Database
from collections import OrderedDict
from ..interfaces import Landmark

class LandmarkDB:
    """Persistent landmark database for calibration refinement (LRU, max 1000)."""
    def __init__(self, max_size=1000):
        self.landmarks = OrderedDict()
        self.max_size = max_size
    
    def add_landmark(self, keypoint_id, landmark: Landmark):
        if len(self.landmarks) >= self.max_size:
            self.landmarks.popitem(last=False)
        self.landmarks[keypoint_id] = landmark
    
    def match_and_refine(self, current_keypoints, current_descriptors):
        # TODO: Implement PnP solve
        return None, 0
