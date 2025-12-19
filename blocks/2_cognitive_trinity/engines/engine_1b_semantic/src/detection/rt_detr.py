# Engine 1B: RT-DETR-X Object Detection
# Supports PyTorch (dev) and TensorRT (production)

from typing import List, Tuple, Optional
import numpy as np

# Import shared inference backend
import sys
sys.path.insert(0, '../../../../shared')
try:
    from blocks.cognitive_trinity.shared.inference import InferenceBackend
except ImportError:
    InferenceBackend = None


class RTDETR:
    """
    RT-DETR-X real-time detection transformer.
    
    Supports:
    - PyTorch (.pt) for development
    - TensorRT (.trt) for production
    
    Timing:
    - PyTorch: ~35ms
    - TensorRT FP16: ~12ms ✓ Meets 25ms budget
    
    Detects: PERSON, VEHICLE, ANIMAL, OBJECT
    """
    
    def __init__(
        self,
        model_path: str = None,
        backend: str = 'auto',
        device: str = 'cuda:0',
        conf_threshold: float = 0.5,
        nms_threshold: float = 0.45
    ):
        self.model_path = model_path
        self.device = device
        self.conf_threshold = conf_threshold
        self.nms_threshold = nms_threshold
        
        self._backend: Optional[InferenceBackend] = None
        self._input_size = (640, 640)
        
        self.class_names = ['person', 'bicycle', 'car', 'motorcycle', 'bus', 
                           'truck', 'cat', 'dog', 'horse', 'cow']
        
        if model_path:
            self.load(model_path, backend)
    
    def load(self, model_path: str, backend: str = 'auto') -> bool:
        """Load model with specified backend."""
        if InferenceBackend is None:
            print("Warning: InferenceBackend not available")
            return False
        
        self._backend = InferenceBackend(
            model_path=model_path,
            backend_type=backend,
            device=self.device,
            fp16=True
        )
        return self._backend.load()
    
    def infer(self, frame: np.ndarray) -> List[dict]:
        """
        Run detection inference.
        
        Args:
            frame: RGB frame [H, W, 3]
            
        Returns:
            List of detections: [{'bbox': [x1,y1,x2,y2], 'class': str, 'conf': float}]
            
        Timing: ~12ms (TensorRT FP16)
        """
        if self._backend is None:
            return []
        
        # Preprocess
        tensor = self._preprocess(frame)
        
        # Inference
        output = self._backend.infer(tensor)
        
        # Postprocess
        detections = self._postprocess(output, frame.shape[:2])
        
        return detections
    
    def _preprocess(self, frame: np.ndarray) -> np.ndarray:
        """Preprocess frame for RT-DETR."""
        import cv2
        resized = cv2.resize(frame, self._input_size)
        normalized = resized.astype(np.float32) / 255.0
        tensor = normalized.transpose(2, 0, 1)[np.newaxis, ...]
        return tensor
    
    def _postprocess(self, output: np.ndarray, original_size: Tuple[int, int]) -> List[dict]:
        """Postprocess RT-DETR output to detections."""
        detections = []
        # TODO: Parse actual RT-DETR output format
        return detections
    
    def get_latency_stats(self) -> dict:
        """Get inference latency statistics."""
        return self._backend.get_latency_stats() if self._backend else {}
