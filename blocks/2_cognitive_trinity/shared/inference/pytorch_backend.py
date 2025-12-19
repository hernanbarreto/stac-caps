# PyTorch Backend
# For development and debugging

from typing import Dict, Tuple, Optional
import numpy as np

from .backend import BaseBackend


class PyTorchBackend(BaseBackend):
    """
    PyTorch inference backend.
    
    Best for:
    - Development and debugging
    - Model validation
    - Quick prototyping
    
    Note: Slower than TensorRT, use for development only.
    """
    
    def __init__(self, device: str = 'cuda:0', fp16: bool = False):
        self.device = device
        self.fp16 = fp16
        self.model = None
        self._torch = None
    
    def load(self, model_path: str, model_class=None, **kwargs) -> bool:
        """
        Load PyTorch model.
        
        Args:
            model_path: Path to .pt or .pth file
            model_class: Optional model class for state_dict loading
        """
        try:
            import torch
            self._torch = torch
            
            if model_class is not None:
                # Load from state_dict
                self.model = model_class(**kwargs)
                state_dict = torch.load(model_path, map_location=self.device)
                self.model.load_state_dict(state_dict)
            else:
                # Load full model
                self.model = torch.load(model_path, map_location=self.device)
            
            self.model.to(self.device)
            self.model.eval()
            
            if self.fp16 and 'cuda' in self.device:
                self.model.half()
            
            return True
        except Exception as e:
            print(f"Error loading PyTorch model: {e}")
            return False
    
    def infer(self, inputs: np.ndarray) -> np.ndarray:
        """Run PyTorch inference."""
        if self.model is None:
            raise RuntimeError("Model not loaded")
        
        torch = self._torch
        
        # Convert to tensor
        tensor = torch.from_numpy(inputs).to(self.device)
        if self.fp16:
            tensor = tensor.half()
        
        # Inference
        with torch.no_grad():
            output = self.model(tensor)
        
        # Convert back to numpy
        if isinstance(output, tuple):
            return tuple(o.cpu().numpy() for o in output)
        return output.cpu().numpy()
    
    def warmup(self, input_shape: Tuple[int, ...]) -> None:
        """Warmup PyTorch model."""
        dummy = np.zeros(input_shape, dtype=np.float32)
        for _ in range(5):
            self.infer(dummy)
    
    def get_latency_stats(self) -> Dict[str, float]:
        """PyTorch doesn't track latency internally."""
        return {}
    
    def export_onnx(self, output_path: str, input_shape: Tuple[int, ...]) -> bool:
        """
        Export model to ONNX format.
        
        Args:
            output_path: Path for .onnx file
            input_shape: Example input shape
        """
        try:
            torch = self._torch
            dummy_input = torch.randn(input_shape).to(self.device)
            if self.fp16:
                dummy_input = dummy_input.half()
            
            torch.onnx.export(
                self.model,
                dummy_input,
                output_path,
                opset_version=17,
                input_names=['input'],
                output_names=['output'],
                dynamic_axes={'input': {0: 'batch'}, 'output': {0: 'batch'}}
            )
            return True
        except Exception as e:
            print(f"ONNX export failed: {e}")
            return False
