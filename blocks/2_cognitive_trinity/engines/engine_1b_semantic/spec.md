# Engine 1B: Semantic + Object 3D - Technical Specification

## Overview

Engine 1B performs **object detection** with **unified 3D representation** for all detection categories:
- **Personas** → SMPL Avatar (85 floats)
- **Objetos Conocidos** → PLY wireframe from library
- **Objetos Desconocidos** → bbox3D only (+ async PLY reconstruction trigger)

All categories output a common `bbox3D` for TTC calculations.

---

## Detection Categories

| Category | Class IDs | 3D Representation | Source |
|----------|-----------|-------------------|--------|
| **Persona** | 0 | SMPL Avatar + bbox3D | RTMPose → Avatar Cache |
| **Objeto Conocido** | 1-50 | PLY wireframe + bbox3D | PLY Library (lookup) |
| **Objeto Desconocido** | 51+ o sin match | Solo bbox3D | Depth projection |

### Known Object Classes (PLY Library)
| ID | Class | PLY Template |
|----|-------|--------------|
| 1 | train | `train_generic.ply` |
| 2 | car | `car_sedan.ply` |
| 3 | truck | `truck_generic.ply` |
| 4 | motorcycle | `motorcycle.ply` |
| 5 | bicycle | `bicycle.ply` |
| 6 | bus | `bus.ply` |
| 7 | barrier | `barrier_jersey.ply` |
| 8-50 | (reserved) | Custom additions |

---

## Inputs

| Input | Type | Shape | Source |
|-------|------|-------|--------|
| `frame` | Tensor | `[1, 3, 1080, 1920]` | Pre-process |
| `depth_map` | Tensor | `[1, 1, 1080, 1920]` | Engine 1A |
| `track_ids` | List[int] | Variable | Engine 2 (feedback) |
| `ply_library` | Dict[class_id, PLY] | ~50 entries | Static library |

---

## Outputs

| Output | Type | Description |
|--------|------|-------------|
| `detections` | List[Detection] | All detected objects with 3D |
| `unknown_triggers` | List[UnknownTrigger] | Async requests for PLY generation |

### Detection Structure (Unified)
```python
@dataclass
class Detection:
    class_id: int              # COCO/custom class
    category: Category         # PERSON | KNOWN_OBJECT | UNKNOWN_OBJECT
    bbox_2d: Tuple[4]          # (x1, y1, x2, y2)
    bbox_3d: BBox3D            # Always present
    confidence: float          # 0.0 - 1.0
    track_id: Optional[int]    # Assigned by Engine 2
    
    # Category-specific (mutually exclusive)
    smpl: Optional[SMPLParams]      # If PERSON
    ply_ref: Optional[str]          # If KNOWN_OBJECT (path to PLY)
    # If UNKNOWN_OBJECT: only bbox_3d is populated

class Category(Enum):
    PERSON = 0
    KNOWN_OBJECT = 1
    UNKNOWN_OBJECT = 2
```

### BBox3D Structure
```python
@dataclass
class BBox3D:
    center: Tuple[3]    # (x, y, z) in meters, rail frame
    dimensions: Tuple[3] # (width, height, depth)
    orientation: float  # yaw angle (radians)
```

### Async Trigger for Unknown Objects
```python
@dataclass
class UnknownTrigger:
    track_id: int
    class_guess: str           # RT-DETR class name
    bbox_3d: BBox3D
    depth_crop: np.ndarray     # Sparse depth points
    timestamp: float
    # Sent to external PLY reconstruction service
```

---

## Components

### 1. RT-DETR-X (Detection)
| Property | Value |
|----------|-------|
| Architecture | ResNet-50 + HybridEncoder + Transformer |
| Classes | 80 COCO + custom |
| Latency | **17 ms** |

### 2. RTMPose-T (Pose - Only for Persons)
| Property | Value |
|----------|-------|
| Architecture | CSPNeXt-Tiny + SimCC Head |
| Latency | **5 ms** (batched) |

### 3. Avatar Cache (Persons)
| Property | Value |
|----------|-------|
| Structure | Dict[track_id → SMPLAvatar] |
| Latency | **3 ms** |

### 4. PLY Library (Known Objects) - NEW
| Property | Value |
|----------|-------|
| Structure | Dict[class_id → PLY mesh] |
| Entries | ~50 pre-computed wireframes |
| Lookup | **O(1)**, <1 ms |
| Storage | ~10 MB total |

### 5. Unknown Handler - NEW
| Property | Value |
|----------|-------|
| Function | Generate async trigger |
| Output | `UnknownTrigger` message |
| Latency | **<1 ms** (non-blocking) |

---

## Processing Flow

```
RT-DETR-X Detection
        ↓
┌───────────────────────────────────────┐
│          CLASSIFY DETECTION           │
│   ┌─────────┬──────────┬────────────┐ │
│   │ PERSON  │  KNOWN   │  UNKNOWN   │ │
│   │ (id=0)  │ (id 1-50)│  (id>50)   │ │
│   └────┬────┴─────┬────┴──────┬─────┘ │
│        ↓          ↓           ↓       │
│   RTMPose    PLY Lookup   Depth bbox  │
│      ↓          ↓           ↓         │
│   SMPL      PLY ref     Async trigger │
│   Avatar                 (external)   │
└───────────────────────────────────────┘
        ↓
    OUTPUT: Detection[] + UnknownTrigger[]
```

---

## Timing Budget

```
RT-DETR-X Detection:      17 ms
├── Backbone:             10 ms
├── Encoder:               4 ms
└── Decoder:               3 ms

Classification:            0 ms (conditional)

Per-category (parallel branches):
├── Persons: RTMPose + Cache  5 ms
├── Known: PLY Lookup        <1 ms
└── Unknown: Async trigger   <1 ms

TOTAL (worst case):       25 ms
```

---

## External PLY Reconstruction Service

> ⚠️ **NOT part of RT loop** - runs on separate system

| Property | Value |
|----------|-------|
| Trigger | UDP message with `UnknownTrigger` |
| Reconstruction | SAM-3D-OBJECT or similar |
| Output | Sparse PLY (< 1000 vertices) |
| Destination | PLY Library (hot-reload) |
| Expected latency | 5-30 seconds |

---

## Error Handling

| Condition | Action |
|-----------|--------|
| No persons detected | Skip RTMPose |
| Unknown class_id | Classify as UNKNOWN_OBJECT |
| PLY not in library | Fall back to bbox3D only |
| Async service down | Log warning, continue with bbox3D |

---

## Privacy Guarantees

- ✅ **Persons**: SMPL params only (no facial data)
- ✅ **Objects**: PLY wireframes (no texture/color)
- ✅ **GDPR Compliant**: Only geometric data stored

---

## Files

| File | Purpose |
|------|---------|
| [arquitectura.svg](arquitectura.svg) | Component structure |
| [flujo.svg](flujo.svg) | Processing logic |
| `spec.md` | This document |
