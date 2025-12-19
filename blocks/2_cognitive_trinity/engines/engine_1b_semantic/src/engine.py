"""
Engine 1B: Semantic - Main Engine Class

TRACEABILITY:
  - Architecture: engine_1b_semantic/arquitectura.svg
  - Flow: engine_1b_semantic/flujo.svg
"""

from .interfaces import SemanticInput, SemanticOutput, Detection, Category
from .config import SEMANTIC_PARAMS


class Engine1BSemantic:
    """
    Unified semantic perception with 3-category classification.
    
    Flow:
        1. Receive frame + depth
        2. RT-DETR-X detection
        3. FOR EACH detection:
           - Classify by class_id
           - Route to PERSONA | CONOCIDO | DESCONOCIDO branch
           - Generate bbox3D (all categories)
        4. Return unified detections
    
    Timing Budget: 25ms
    """
    
    def __init__(self, config: dict = None):
        self.config = config or SEMANTIC_PARAMS
        # TODO: Initialize models
        # self.rt_detr = RTDetrX(...)
        # self.rtmpose = RTMPoseT(...)
        # self.avatar_cache = AvatarCache()
        # self.ply_library = PLYLibrary(...)
    
    def process(self, input_data: SemanticInput) -> SemanticOutput:
        """
        Process frame through semantic pipeline.
        
        TRACEABILITY: flujo.svg Steps 1-Final
        """
        # Step 1: Receive
        frame = input_data.frame
        depth = input_data.depth_map
        
        # Step 2: RT-DETR-X Detection (17ms)
        # detections = self.rt_detr.infer(frame)
        
        # Step 3: FOR EACH detection
        results = []
        # for det in detections:
        #     category = self._classify(det.class_id)
        #     
        #     if category == Category.PERSONA:
        #         result = self._process_person(det, frame, depth)
        #     elif category == Category.CONOCIDO:
        #         result = self._process_known(det, depth)
        #     else:  # DESCONOCIDO
        #         result = self._process_unknown(det, depth)
        #     
        #     results.append(result)
        
        # return SemanticOutput(detections=results)
        
        raise NotImplementedError("Engine 1B not yet implemented")
    
    def _classify(self, class_id: int) -> "Category":
        """TRACEABILITY: arquitectura.svg#comp_classifier"""
        pass
    
    def _process_person(self, det, frame, depth):
        """TRACEABILITY: arquitectura.svg#comp_person_branch, flujo.svg P1-P3"""
        pass
    
    def _process_known(self, det, depth):
        """TRACEABILITY: arquitectura.svg#comp_known_branch, flujo.svg K1-K2"""
        pass
    
    def _process_unknown(self, det, depth):
        """TRACEABILITY: arquitectura.svg#comp_unknown_branch, flujo.svg U1-U2"""
        pass
