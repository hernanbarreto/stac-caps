# Engine 1A: Depth Model - DepthAnything-v2
# Supports PyTorch (dev) and TensorRT (production)

from typing import Optional, Tuple
import numpy as np

# Import shared inference backend
import sys
sys.path.insert(0, '../../../shared')
from blocks.cognitive_trinity.shared.inference import InferenceBackend


class DepthAnythingV2:
    """
    DepthAnything-v2 depth estimation model.
    
    Supports:
    - PyTorch (.pt) for development/debugging
    - TensorRT (.trt) for production (3-4x faster)
    
    Timing:
    - PyTorch: ~40-50ms
    - TensorRT FP16: ~15-18ms ✓ Meets 22ms budget
    
    Usage:
        # Development
        model = DepthAnythingV2('model.pt', backend='pytorch')
        
        # Production  
        model = DepthAnythingV2('model.trt', backend='tensorrt')
        
        depth = model.infer(frame)
    """
    
    def __init__(
        self,
        model_path: str = None,
        backend: str = 'auto',
        device: str = 'cuda:0',
        fp16: bool = True
    ):
        self.model_path = model_path
        self.device = device
        self.fp16 = fp16
        
        self._backend: Optional[InferenceBackend] = None
        self._input_size = (518, 518)  # DepthAnything-v2 input size
        
        if model_path:
            self.load(model_path, backend)
    
    def load(self, model_path: str, backend: str = 'auto') -> bool:
        """
        Load model with specified backend.
        
        Args:
            model_path: Path to .pt or .trt file
            backend: 'pytorch', 'tensorrt', or 'auto'
        """
        self._backend = InferenceBackend(
            model_path=model_path,
            backend_type=backend,
            device=self.device,
            fp16=self.fp16
        )
        return self._backend.load()
    
    def preprocess(self, frame: np.ndarray) -> np.ndarray:
        """
        Preprocess frame for inference.
        
        Args:
            frame: RGB frame [H, W, 3] uint8
            
        Returns:
            Preprocessed tensor [1, 3, 518, 518] float32
        """
        import cv2
        
        # Resize to model input size
        resized = cv2.resize(frame, self._input_size)
        
        # Normalize to [0, 1]
        normalized = resized.astype(np.float32) / 255.0
        
        # ImageNet normalization
        mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
        std = np.array([0.229, 0.224, 0.225], dtype=np.float32)
        normalized = (normalized - mean) / std
        
        # HWC -> CHW -> NCHW
        tensor = normalized.transpose(2, 0, 1)[np.newaxis, ...]
        
        return tensor.astype(np.float32)
    
    def postprocess(
        self,
        output: np.ndarray,
        original_size: Tuple[int, int]
    ) -> np.ndarray:
        """
        Postprocess model output.
        
        Args:
            output: Raw model output [1, 1, H, W]
            original_size: (width, height) to resize to
            
        Returns:
            Depth map [H, W] in relative units
        """
        import cv2
        
        # Remove batch and channel dims
        depth = output.squeeze()
        
        # Resize to original
        depth = cv2.resize(depth, original_size)
        
        return depth
    
    def infer(self, frame: np.ndarray) -> np.ndarray:
        """
        Run depth inference.
        
        Args:
            frame: RGB frame [H, W, 3] uint8
            
        Returns:
            Relative depth map [H, W] float32
            
        Timing: ~18ms (TensorRT FP16)
        """
        if self._backend is None:
            raise RuntimeError("Model not loaded. Call load() first.")
        
        original_size = (frame.shape[1], frame.shape[0])
        
        # Preprocess
        tensor = self.preprocess(frame)
        
        # Inference
        output = self._backend.infer(tensor)
        
        # Postprocess
        depth = self.postprocess(output, original_size)
        
        return depth
    
    def get_latency_stats(self) -> dict:
        """Get inference latency statistics in ms."""
        if self._backend:
            return self._backend.get_latency_stats()
        return {}
    
    def warmup(self, frame_shape: Tuple[int, int, int] = (1080, 1920, 3)):
        """Warmup model for consistent timing."""
        dummy = np.zeros(frame_shape, dtype=np.uint8)
        for _ in range(10):
            self.infer(dummy)
