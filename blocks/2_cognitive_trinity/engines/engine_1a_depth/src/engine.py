"""
Engine 1A: Depth - Main Engine Class

TRACEABILITY:
  - Architecture: engine_1a_depth/arquitectura.svg (full diagram)
  - Flow: engine_1a_depth/flujo.svg (steps 1-11)
  - Spec: engine_1a_depth/spec.md
"""

from .interfaces import DepthInput, DepthOutput, CalibrationInput
from .config import DEPTH_PARAMS

# TODO: Import submodules when implemented
# from .preprocessing import resize_for_depth, resize_to_original
# from .inference import DepthAnythingV2
# from .calibration import apply_metric_scale
# from .refinement import detect_outliers, guided_filter, temporal_smooth
# from .output import generate_point_cloud
# from .confidence import compute_confidence


class Engine1ADepth:
    """
    Main engine for monocular depth estimation.
    
    Flow:
        1. Receive frame
        2. Resize to 518x518
        3. DepthAnything-v2 inference
        4. Apply metric scale
        5. Outlier detection
        6. Guided filter
        7. Temporal EMA
        8. Upscale to original
        9. Generate point cloud
        10. Compute confidence
        11. Return output
    
    Timing Budget: 25ms
    """
    
    def __init__(self, config: dict = None):
        """Initialize engine with configuration."""
        self.config = config or DEPTH_PARAMS
        self.prev_depth = None
        
        # TODO: Initialize model
        # self.depth_model = DepthAnythingV2(...)
    
    def process(self, input_data: DepthInput, calibration: CalibrationInput) -> DepthOutput:
        """
        Process a single frame through the depth pipeline.
        
        TRACEABILITY: flujo.svg Steps 1-11
        
        Args:
            input_data: Frame and optional previous depth
            calibration: Scale factor from Layer 1
            
        Returns:
            DepthOutput with depth_map, point_cloud, confidence
        """
        # Step 1: Receive frame
        frame = input_data.frame
        prev_depth = input_data.prev_depth or self.prev_depth
        
        # Step 2: Resize (2ms)
        # resized = resize_for_depth(frame)
        
        # Step 3: Inference (18ms)
        # relative_depth = self.depth_model.infer(resized)
        
        # Step 4: Metric scale (<1ms)
        # depth_m = apply_metric_scale(relative_depth, calibration.scale_factor)
        
        # Step 5: Outlier detection (<1ms)
        # depth_clean = detect_outliers(depth_m)
        
        # Step 6: Guided filter (1ms)
        # depth_guided = guided_filter(frame, depth_clean)
        
        # Step 7: Temporal EMA (1ms)
        # depth_smooth = temporal_smooth(depth_guided, prev_depth, self.config['temporal_alpha'])
        
        # Step 8: Upscale
        # depth_full = resize_to_original(depth_smooth, frame.shape[:2])
        
        # Step 9: Point cloud (2ms)
        # point_cloud = generate_point_cloud(depth_full, calibration.intrinsics)
        
        # Step 10: Confidence (<1ms)
        # confidence = compute_confidence(depth_full, frame, prev_depth)
        
        # Update state
        # self.prev_depth = depth_full
        
        # Step 11: Output
        # return DepthOutput(
        #     depth_map=depth_full,
        #     point_cloud=point_cloud,
        #     confidence=confidence
        # )
        
        raise NotImplementedError("Engine 1A not yet implemented")
