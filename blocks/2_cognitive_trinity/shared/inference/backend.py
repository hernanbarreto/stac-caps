# Inference Backend Abstraction
# Unified interface for PyTorch and TensorRT

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, Optional, Tuple
import numpy as np


class BackendType(Enum):
    """Supported inference backends."""
    PYTORCH = 'pytorch'      # Development, debugging
    TENSORRT = 'tensorrt'    # Production, optimized
    ONNX = 'onnx'            # Intermediate, portable


class BaseBackend(ABC):
    """Abstract base class for inference backends."""
    
    @abstractmethod
    def load(self, model_path: str, **kwargs) -> bool:
        """Load model from file."""
        pass
    
    @abstractmethod
    def infer(self, inputs: np.ndarray) -> np.ndarray:
        """Run inference on input."""
        pass
    
    @abstractmethod
    def warmup(self, input_shape: Tuple[int, ...]) -> None:
        """Warmup inference for consistent timing."""
        pass
    
    @abstractmethod
    def get_latency_stats(self) -> Dict[str, float]:
        """Get latency statistics."""
        pass


class InferenceBackend:
    """
    Unified inference backend supporting multiple engines.
    
    Usage:
        # Development
        backend = InferenceBackend('model.pt', backend_type='pytorch')
        
        # Production
        backend = InferenceBackend('model.trt', backend_type='tensorrt')
        
        # Same API
        output = backend.infer(input_tensor)
    
    Features:
        - Automatic backend selection based on file extension
        - Consistent API across backends
        - Latency tracking for timing budget validation
        - FP16 support for TensorRT
    """
    
    def __init__(
        self,
        model_path: str,
        backend_type: str = 'auto',
        device: str = 'cuda:0',
        fp16: bool = True,
        warmup_iterations: int = 10
    ):
        self.model_path = model_path
        self.device = device
        self.fp16 = fp16
        self.warmup_iterations = warmup_iterations
        
        # Auto-detect backend from extension
        if backend_type == 'auto':
            backend_type = self._detect_backend(model_path)
        
        self.backend_type = BackendType(backend_type)
        self._backend: Optional[BaseBackend] = None
        self._latencies = []
        
    def _detect_backend(self, path: str) -> str:
        """Detect backend from file extension."""
        if path.endswith('.pt') or path.endswith('.pth'):
            return 'pytorch'
        elif path.endswith('.trt') or path.endswith('.engine'):
            return 'tensorrt'
        elif path.endswith('.onnx'):
            return 'onnx'
        else:
            return 'pytorch'  # Default
    
    def load(self) -> bool:
        """Load the model with appropriate backend."""
        if self.backend_type == BackendType.PYTORCH:
            from .pytorch_backend import PyTorchBackend
            self._backend = PyTorchBackend(self.device, self.fp16)
        elif self.backend_type == BackendType.TENSORRT:
            from .tensorrt_backend import TensorRTBackend
            self._backend = TensorRTBackend(self.device, self.fp16)
        elif self.backend_type == BackendType.ONNX:
            from .onnx_backend import ONNXBackend
            self._backend = ONNXBackend(self.device, self.fp16)
        else:
            raise ValueError(f"Unknown backend: {self.backend_type}")
        
        return self._backend.load(self.model_path)
    
    def infer(self, inputs: np.ndarray) -> np.ndarray:
        """
        Run inference with timing tracking.
        
        Args:
            inputs: Input tensor as numpy array
            
        Returns:
            Output tensor as numpy array
        """
        import time
        
        if self._backend is None:
            self.load()
        
        start = time.perf_counter()
        output = self._backend.infer(inputs)
        latency = (time.perf_counter() - start) * 1000  # ms
        
        self._latencies.append(latency)
        if len(self._latencies) > 100:
            self._latencies.pop(0)
        
        return output
    
    def warmup(self, input_shape: Tuple[int, ...]) -> None:
        """Warmup model for consistent timing."""
        if self._backend is None:
            self.load()
        
        dummy = np.zeros(input_shape, dtype=np.float32)
        for _ in range(self.warmup_iterations):
            self._backend.infer(dummy)
        
        self._latencies.clear()
    
    def get_latency_stats(self) -> Dict[str, float]:
        """Get latency statistics in milliseconds."""
        if not self._latencies:
            return {'min': 0, 'max': 0, 'mean': 0, 'std': 0}
        
        arr = np.array(self._latencies)
        return {
            'min': float(np.min(arr)),
            'max': float(np.max(arr)),
            'mean': float(np.mean(arr)),
            'std': float(np.std(arr))
        }
    
    def __call__(self, inputs: np.ndarray) -> np.ndarray:
        """Allow calling backend directly."""
        return self.infer(inputs)
