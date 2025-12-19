# Engine 1A: Depth - Source Code

## Overview
Monocular depth estimation using DepthAnything-v2 with refinement pipeline.

## Traceability
See [traceability.md](../traceability.md) for complete mapping to architecture and flow diagrams.

## Structure
```
src/
├── engine.py                    # Main class: Engine1ADepth
├── interfaces.py                # Data types: DepthInput, DepthOutput
├── config.py                    # DEPTH_PARAMS
├── preprocessing/               # Step 2: Resize
├── inference/                   # Step 3: DepthAnything-v2
├── calibration/                 # Step 4: Metric Scale
├── refinement/                  # Steps 5-7: Outlier, Guided, EMA
├── output/                      # Step 9: Point Cloud
└── confidence/                  # Step 10: Enhanced Confidence
```

## Status
🟡 Structure Created - Awaiting Implementation

## Entry Point
```python
from engine_1a_depth.src.engine import Engine1ADepth

engine = Engine1ADepth(config)
result = engine.process(frame, calibration)
```
