# Engine 1B: Semantic - Traceability Matrix

Mapeo **1:1** entre documentación (SVGs, spec) y código.

---

## Mapeo Arquitectura → Código

| ID en `arquitectura.svg` | Componente | Archivo en `src/` | Clase/Función |
|--------------------------|------------|-------------------|---------------|
| `comp_input` | INPUT | `interfaces.py` | `SemanticInput` dataclass |
| `comp_rt_detr_x` | RT-DETR-X | `detection/rt_detr.py` | `RTDetrX` class |
| `comp_classifier` | CLASSIFIER | `classification/classifier.py` | `classify_detection()` |
| `comp_person_branch` | PERSONA | `branches/person/` | (submodule) |
| → RTMPose-T | - | `branches/person/rtmpose.py` | `RTMPoseT` class |
| → Avatar Cache | - | `branches/person/avatar_cache.py` | `AvatarCache` class |
| `comp_known_branch` | CONOCIDO | `branches/known/` | (submodule) |
| → PLY Library | - | `branches/known/ply_library.py` | `PLYLibrary` class |
| → Transform | - | `branches/known/transform.py` | `align_ply()` |
| `comp_unknown_branch` | DESCONOCIDO | `branches/unknown/` | (submodule) |
| → Depth Projection | - | `branches/unknown/depth_projection.py` | `project_to_3d()` |
| → Async Trigger | - | `branches/unknown/async_trigger.py` | `UnknownTrigger` class |
| `comp_output` | UNIFIED OUTPUT | `interfaces.py` | `SemanticOutput` dataclass |
| `comp_external` | EXTERNAL SERVICE | *(external)* | N/A (SAM-3D) |

---

## Mapeo Flujo → Código

| Step en `flujo.svg` | Descripción | Función | Timing |
|---------------------|-------------|---------|--------|
| 1. RECEIVE FRAME + DEPTH | Input | `Engine1BSemantic.process()` | - |
| 2. RT-DETR-X DETECTION | Detection | `rt_detr.infer(frame)` | 17 ms |
| FOR EACH detection[i] | Loop | `for det in detections:` | - |
| → class_id = 0 (PERSONA) | Branch | `_process_person()` | 8 ms |
| → → P1. Get Track ID | Sub-step | `det.track_id` | - |
| → → P2. RTMPose-T | Sub-step | `rtmpose.infer(crop)` | 5 ms |
| → → P3. Apply θ + bbox3D | Sub-step | `avatar.update()` | 3 ms |
| → class_id 1-50 (CONOCIDO) | Branch | `_process_known()` | <1 ms |
| → → K1. PLY Library Lookup | Sub-step | `ply_library.get(class_id)` | <1 ms |
| → → K2. Scale & Orient | Sub-step | `align_ply(depth)` | <1 ms |
| → class_id >50 (UNKNOWN) | Branch | `_process_unknown()` | <1 ms |
| → → U1. Depth Projection | Sub-step | `project_to_3d(bbox2D, depth)` | <1 ms |
| → → U2. Async PLY Trigger | Sub-step | `trigger.send_async()` | non-blocking |
| UNIFIED DETECTION OUTPUT | Merge | `UnifiedDetection` dataclass | - |
| FINAL OUTPUT | Return | `return SemanticOutput(...)` | - |

---

## Estructura de Código

```
engine_1b_semantic/src/
├── __init__.py
├── engine.py                    # Engine1BSemantic (entry point)
├── interfaces.py                # SemanticInput, SemanticOutput, Detection
├── config.py                    # SEMANTIC_PARAMS
│
├── detection/
│   ├── __init__.py
│   └── rt_detr.py               # class RTDetrX
│
├── classification/
│   ├── __init__.py
│   └── classifier.py            # classify_detection()
│
├── branches/
│   ├── __init__.py
│   ├── person/                  # PERSONA branch
│   │   ├── __init__.py
│   │   ├── rtmpose.py           # class RTMPoseT
│   │   └── avatar_cache.py      # class AvatarCache
│   ├── known/                   # CONOCIDO branch
│   │   ├── __init__.py
│   │   ├── ply_library.py       # class PLYLibrary
│   │   └── transform.py         # align_ply()
│   └── unknown/                 # DESCONOCIDO branch
│       ├── __init__.py
│       ├── depth_projection.py  # project_to_3d()
│       └── async_trigger.py     # class UnknownTrigger
│
└── output/
    ├── __init__.py
    └── unified.py               # UnifiedDetection merger
```

---

## Reglas de Modificación

| Si cambias... | Actualiza también... |
|---------------|----------------------|
| Nueva categoría de detección | Agregar branch en SVG + código |
| Nuevo sub-componente en branch | Agregar caja en SVG + archivo |
| Cambio de modelo (RT-DETR → otro) | Actualizar SVG + detection/ |
| Cambio de timing | Actualizar badges SVG + config.py |

---

## Historial de Cambios

| Fecha | Cambio | Archivos Afectados |
|-------|--------|-------------------|
| 2025-12-19 | Creación inicial | traceability.md |
