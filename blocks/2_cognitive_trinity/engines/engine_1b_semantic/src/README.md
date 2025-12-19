# Engine 1B: Semantic - Source Code

## Overview
Unified object detection and classification with 3-category handling.

## Traceability
See [traceability.md](../traceability.md) for complete mapping.

## Categories
- **PERSONA (class_id=0)**: SMPL Avatar + bbox3D
- **CONOCIDO (class_id 1-50)**: PLY Reference + bbox3D
- **DESCONOCIDO (class_id >50)**: bbox3D only + async trigger

## Structure
```
src/
├── engine.py                # Engine1BSemantic
├── interfaces.py            # I/O types
├── config.py                # Parameters
├── detection/               # RT-DETR-X
├── classification/          # Category router
├── branches/
│   ├── person/              # SMPL pipeline
│   ├── known/               # PLY lookup
│   └── unknown/             # Async PLY trigger
└── output/                  # Unified merger
```

## Status
🟡 Structure Created - Awaiting Implementation

## Timing Budget
- Detection: 17ms
- Person branch: 8ms
- Known branch: <1ms
- Unknown branch: <1ms
- **Total: 25ms**
