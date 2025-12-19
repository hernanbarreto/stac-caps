# Shared Inference Backend
# Abstraction layer for PyTorch (dev) and TensorRT (production)

from .backend import InferenceBackend, BackendType
from .pytorch_backend import PyTorchBackend
from .tensorrt_backend import TensorRTBackend

__all__ = ['InferenceBackend', 'BackendType', 'PyTorchBackend', 'TensorRTBackend']
