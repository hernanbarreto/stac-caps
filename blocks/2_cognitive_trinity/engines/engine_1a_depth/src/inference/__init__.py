"""
Inference submodule for Engine 1A

TRACEABILITY:
  - Architecture: engine_1a_depth/arquitectura.svg#comp_depth_model
  - Flow: engine_1a_depth/flujo.svg Step 3
"""
from .depth_model import DepthAnythingV2

__all__ = ['DepthAnythingV2']
