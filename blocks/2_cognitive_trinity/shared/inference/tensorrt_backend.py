# TensorRT Backend
# For production deployment with optimized inference

from typing import Dict, Tuple, List, Optional
import numpy as np

from .backend import BaseBackend


class TensorRTBackend(BaseBackend):
    """
    TensorRT inference backend for production.
    
    Best for:
    - Production deployment
    - Real-time inference (STAC-CAPS timing requirements)
    - NVIDIA Jetson / Edge GPU
    
    Features:
    - 3-4x faster than PyTorch
    - Deterministic latency (critical for safety)
    - FP16/INT8 quantization support
    - Memory optimized
    
    Conversion:
        trtexec --onnx=model.onnx --saveEngine=model.trt --fp16
    """
    
    def __init__(self, device: str = 'cuda:0', fp16: bool = True):
        self.device = device
        self.fp16 = fp16
        self.engine = None
        self.context = None
        self.bindings = None
        self.stream = None
        self._trt = None
        self._cuda = None
        
        # Timing stats
        self._latencies: List[float] = []
    
    def load(self, model_path: str, **kwargs) -> bool:
        """
        Load TensorRT engine.
        
        Args:
            model_path: Path to .trt or .engine file
        """
        try:
            import tensorrt as trt
            import pycuda.driver as cuda
            import pycuda.autoinit  # noqa: F401
            
            self._trt = trt
            self._cuda = cuda
            
            # Load engine
            logger = trt.Logger(trt.Logger.WARNING)
            with open(model_path, 'rb') as f:
                engine_data = f.read()
            
            runtime = trt.Runtime(logger)
            self.engine = runtime.deserialize_cuda_engine(engine_data)
            self.context = self.engine.create_execution_context()
            
            # Create CUDA stream
            self.stream = cuda.Stream()
            
            # Allocate buffers
            self._allocate_buffers()
            
            return True
        except ImportError as e:
            print(f"TensorRT not available: {e}")
            print("Falling back to PyTorch or install: pip install tensorrt pycuda")
            return False
        except Exception as e:
            print(f"Error loading TensorRT engine: {e}")
            return False
    
    def _allocate_buffers(self):
        """Allocate GPU memory for input/output bindings."""
        cuda = self._cuda
        
        self.bindings = []
        self.inputs = []
        self.outputs = []
        
        for i in range(self.engine.num_io_tensors):
            name = self.engine.get_tensor_name(i)
            shape = self.engine.get_tensor_shape(name)
            dtype = self.engine.get_tensor_dtype(name)
            
            # Calculate size
            size = abs(int(np.prod(shape)))
            
            # Get numpy dtype
            if dtype == self._trt.DataType.FLOAT:
                np_dtype = np.float32
            elif dtype == self._trt.DataType.HALF:
                np_dtype = np.float16
            elif dtype == self._trt.DataType.INT32:
                np_dtype = np.int32
            else:
                np_dtype = np.float32
            
            # Allocate host and device memory
            host_mem = cuda.pagelocked_empty(size, np_dtype)
            device_mem = cuda.mem_alloc(host_mem.nbytes)
            
            self.bindings.append(int(device_mem))
            
            if self.engine.get_tensor_mode(name) == self._trt.TensorIOMode.INPUT:
                self.inputs.append({'host': host_mem, 'device': device_mem, 'shape': shape})
            else:
                self.outputs.append({'host': host_mem, 'device': device_mem, 'shape': shape})
    
    def infer(self, inputs: np.ndarray) -> np.ndarray:
        """
        Run TensorRT inference.
        
        Args:
            inputs: Input array [B, C, H, W]
            
        Returns:
            Output array
        """
        import time
        cuda = self._cuda
        
        if self.engine is None:
            raise RuntimeError("Engine not loaded")
        
        start = time.perf_counter()
        
        # Copy input to device
        np.copyto(self.inputs[0]['host'], inputs.ravel())
        cuda.memcpy_htod_async(
            self.inputs[0]['device'],
            self.inputs[0]['host'],
            self.stream
        )
        
        # Run inference
        self.context.execute_async_v2(
            bindings=self.bindings,
            stream_handle=self.stream.handle
        )
        
        # Copy output to host
        cuda.memcpy_dtoh_async(
            self.outputs[0]['host'],
            self.outputs[0]['device'],
            self.stream
        )
        
        # Synchronize
        self.stream.synchronize()
        
        # Track latency
        latency = (time.perf_counter() - start) * 1000
        self._latencies.append(latency)
        if len(self._latencies) > 100:
            self._latencies.pop(0)
        
        # Reshape output
        output = self.outputs[0]['host'].reshape(self.outputs[0]['shape'])
        return output.copy()
    
    def warmup(self, input_shape: Tuple[int, ...]) -> None:
        """Warmup TensorRT engine for consistent timing."""
        dummy = np.zeros(input_shape, dtype=np.float32)
        for _ in range(10):
            self.infer(dummy)
        self._latencies.clear()
    
    def get_latency_stats(self) -> Dict[str, float]:
        """Get TensorRT inference latency statistics."""
        if not self._latencies:
            return {'min': 0, 'max': 0, 'mean': 0, 'std': 0}
        
        arr = np.array(self._latencies)
        return {
            'min': float(np.min(arr)),
            'max': float(np.max(arr)),
            'mean': float(np.mean(arr)),
            'std': float(np.std(arr))
        }
    
    def __del__(self):
        """Cleanup GPU resources."""
        if hasattr(self, 'stream') and self.stream:
            del self.stream
        if hasattr(self, 'context') and self.context:
            del self.context
        if hasattr(self, 'engine') and self.engine:
            del self.engine


def build_engine_from_onnx(
    onnx_path: str,
    engine_path: str,
    fp16: bool = True,
    int8: bool = False,
    max_batch_size: int = 1,
    workspace_gb: int = 4
) -> bool:
    """
    Build TensorRT engine from ONNX model.
    
    Args:
        onnx_path: Path to ONNX model
        engine_path: Output path for TensorRT engine
        fp16: Enable FP16 precision
        int8: Enable INT8 quantization (requires calibration)
        max_batch_size: Maximum batch size
        workspace_gb: GPU workspace in GB
    
    Returns:
        True if successful
    
    Alternative CLI:
        trtexec --onnx=model.onnx --saveEngine=model.trt --fp16
    """
    try:
        import tensorrt as trt
        
        logger = trt.Logger(trt.Logger.INFO)
        builder = trt.Builder(logger)
        network = builder.create_network(
            1 << int(trt.NetworkDefinitionCreationFlag.EXPLICIT_BATCH)
        )
        parser = trt.OnnxParser(network, logger)
        
        # Parse ONNX
        with open(onnx_path, 'rb') as f:
            if not parser.parse(f.read()):
                for i in range(parser.num_errors):
                    print(parser.get_error(i))
                return False
        
        # Configure builder
        config = builder.create_builder_config()
        config.set_memory_pool_limit(
            trt.MemoryPoolType.WORKSPACE,
            workspace_gb * (1 << 30)
        )
        
        if fp16:
            config.set_flag(trt.BuilderFlag.FP16)
        if int8:
            config.set_flag(trt.BuilderFlag.INT8)
        
        # Build engine
        engine = builder.build_serialized_network(network, config)
        
        if engine is None:
            print("Failed to build engine")
            return False
        
        # Save engine
        with open(engine_path, 'wb') as f:
            f.write(engine)
        
        print(f"Engine saved to {engine_path}")
        return True
        
    except Exception as e:
        print(f"Engine build failed: {e}")
        return False
