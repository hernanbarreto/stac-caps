# 3D Fusion - Technical Specification

## Overview

3D Fusion combines outputs from the Cognitive Trinity engines to create a unified **3D scene representation**. It fuses depth data, semantic bounding boxes, and SMPL avatars into a coherent spatial model for behavior prediction and collision detection.

---

## Key Features

| Feature | Description |
|---------|-------------|
| **Depth-BBox Fusion** | Project 2D bboxes into 3D using depth |
| **SMPL Integration** | Place avatar meshes in 3D space |
| **Point Cloud Filtering** | Keep only relevant object points |
| **Coordinate Unification** | All objects in train-centric coords |
| **Temporal Consistency** | Smooth positions across frames |

---

## Inputs

| Input | Type | Source |
|-------|------|--------|
| `depth_map` | Tensor[H×W] | Engine 1A (current frame) |
| `point_cloud` | Tensor[N×3] | Engine 1A (current frame) |
| `confidence_map` | Tensor[H×W] | Engine 1A (current frame) |
| `detections` | List[Detection] | Engine 1B (current frame) |
| `prev_tracks` | List[Track] | Engine 2 **(previous frame t-1)** |
| `calibration` | CameraIntrinsics | Layer 1 |

> **Nota:** 3D Fusion usa `prev_tracks` del frame anterior porque Engine 2 corre después de 3D Fusion en el pipeline. Esto permite usar información de velocidad e historial para mejorar la estimación 3D.

### Detection Structure (from Engine 1B)
```python
@dataclass
class Detection:
    bbox2D: Tuple[x1, y1, x2, y2]
    class_id: int
    category: str  # PERSON, KNOWN, UNKNOWN
    confidence: float
    smpl_params: Optional[Dict]  # For PERSON
    ply_wireframe: Optional[str]  # For KNOWN
```

---

## Outputs

| Output | Type | Description |
|--------|------|-------------|
| `scene_3d` | Scene3D | Unified 3D scene |
| `objects_3d` | List[Object3D] | 3D objects with positions |
| `fused_tracks` | List[FusedTrack] | Tracks with 3D data |

### Object3D Structure
```python
@dataclass
class Object3D:
    track_id: int
    position: Tuple[x, y, z]          # Center in world coords
    bbox3D: Tuple[x, y, z, w, h, d]   # 3D bounding box
    velocity: Tuple[vx, vy, vz]       # From tracking
    category: str
    representation: str               # 'SMPL' | 'PLY' | 'BBOX'
    mesh_data: Optional[Mesh]         # For rendering
    confidence: float
```

---

## Components

### 1. Depth-to-3D Projector
| Property | Value |
|----------|-------|
| Input | bbox2D + depth_map + calibration |
| Output | bbox3D (center + dimensions) |
| Method | Camera projection with focal length |
| Latency | **<1 ms** |

```python
def project_bbox_to_3d(bbox2D, depth_map, intrinsics):
    """Project 2D bbox to 3D using depth."""
    x1, y1, x2, y2 = bbox2D
    cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
    
    # Sample depth at center
    depth = depth_map[int(cy), int(cx)]
    
    # Project to 3D
    fx, fy = intrinsics.focal_length
    px, py = intrinsics.principal_point
    
    X = (cx - px) * depth / fx
    Y = (cy - py) * depth / fy
    Z = depth
    
    # Estimate dimensions from 2D + depth
    width_3d = (x2 - x1) * depth / fx
    height_3d = (y2 - y1) * depth / fy
    depth_3d = estimate_object_depth(category)
    
    return BBox3D(X, Y, Z, width_3d, height_3d, depth_3d)
```

### 2. SMPL Placer
| Property | Value |
|----------|-------|
| Input | smpl_params + position_3d |
| Output | Placed avatar mesh |
| Purpose | Position SMPL avatar in 3D space |
| Latency | **<1 ms** |

```python
def place_smpl_avatar(smpl_params, position_3d):
    """Place SMPL avatar at 3D position."""
    
    # Get avatar mesh from params
    vertices = smpl_model.forward(
        betas=smpl_params['betas'],
        body_pose=smpl_params['body_pose'],
        global_orient=smpl_params['global_orient']
    )
    
    # Translate to world position
    vertices_world = vertices + position_3d
    
    return Mesh(vertices=vertices_world, faces=smpl_faces)
```

### 3. PLY Aligner
| Property | Value |
|----------|-------|
| Input | ply_wireframe + bbox3D |
| Output | Aligned wireframe mesh |
| Purpose | Scale and position known object wireframes |
| Latency | **<1 ms** |

```python
def align_ply_wireframe(ply_template, bbox3D):
    """Align PLY wireframe to 3D bbox."""
    
    # Load template
    vertices = load_ply(ply_template)
    
    # Scale to match bbox dimensions
    scale = bbox3D.dimensions / vertices.bbox.dimensions
    vertices_scaled = vertices * scale
    
    # Translate to bbox center
    vertices_placed = vertices_scaled + bbox3D.center
    
    return Wireframe(vertices=vertices_placed)
```

### 4. Point Cloud Segmenter
| Property | Value |
|----------|-------|
| Input | point_cloud + bbox3D masks |
| Output | Per-object point clouds |
| Purpose | Extract points belonging to each object |
| Latency | **<1 ms** |

```python
def segment_points_by_object(point_cloud, objects_3d):
    """Segment point cloud by 3D bboxes."""
    
    segmented = {}
    
    for obj in objects_3d:
        # Check which points fall inside bbox
        mask = points_in_bbox(point_cloud, obj.bbox3D)
        segmented[obj.track_id] = point_cloud[mask]
    
    # Remaining points are background
    segmented['background'] = point_cloud[~any_object_mask]
    
    return segmented
```

### 5. Temporal Smoother
| Property | Value |
|----------|-------|
| Input | current_positions + previous_positions |
| Output | Smoothed positions |
| Method | EMA with α=0.7 |
| Latency | **<1 ms** |

```python
def smooth_positions(current_objects, previous_objects, alpha=0.7):
    """Smooth 3D positions temporally."""
    
    smoothed = []
    
    for obj in current_objects:
        prev = find_by_track_id(previous_objects, obj.track_id)
        
        if prev:
            # EMA smoothing
            smoothed_pos = alpha * obj.position + (1-alpha) * prev.position
            obj.position = smoothed_pos
        
        smoothed.append(obj)
    
    return smoothed
```

---

## Processing Flow

```
1. RECEIVE inputs from Engine 1A, 1B, 2
           ↓
2. FOR EACH detection:
   ├── PROJECT bbox2D → bbox3D (using depth)
   ├── IF PERSON: PLACE SMPL avatar
   └── IF KNOWN: ALIGN PLY wireframe
           ↓
3. SEGMENT point cloud by objects
           ↓
4. MERGE with tracking data (velocity, history)
           ↓
5. SMOOTH positions temporally (EMA)
           ↓
6. OUTPUT unified Scene3D → Engine 2, Engine 3
```

---

## Timing Budget

```
Depth-to-3D Projection:  <1 ms (per object)
SMPL Placement:          <1 ms (persons only)
PLY Alignment:           <1 ms (known objects)
Point Cloud Segmentation:<1 ms
Temporal Smoothing:      <1 ms

TOTAL:                    3 ms (all objects)
```

---

## Coordinate System

```
      +Y (up)
       │
       │
       │
       └───────── +X (right)
      /
     /
    +Z (forward, direction of travel)
    
Origin: Camera center (train front)
Units: Meters
```

### Camera → Rail Frame Transformation

The transformation from camera coordinates to rail-centric world coordinates is applied in the **3D Projection** step (after 3D Fusion):

```python
def camera_to_rail(point_camera, extrinsics):
    """
    Transform from camera frame to rail frame.
    
    Args:
        point_camera: [x, y, z] in camera coordinates
        extrinsics: (R, t) from Layer 1 calibration
    
    Returns:
        point_rail: [x, y, z] in rail-centric world coordinates
    """
    R, t = extrinsics  # From Layer 1 calibration
    point_rail = R @ point_camera + t
    return point_rail
```

| Frame | Origin | Use |
|-------|--------|-----|
| **Camera** | Camera optical center | Engine 1A/1B output |
| **Rail** | Center of track at train position | Engine 3 TTC calculations |

---

## Object Representation by Category

| Category | Representation | Data |
|----------|----------------|------|
| **PERSON** | SMPL Avatar | 6890 vertices mesh |
| **KNOWN** | PLY Wireframe | Scaled template |
| **UNKNOWN** | BBox3D only | 8-vertex cuboid |

---

## Integration Points

```
Engine 1A (Depth) ──────┐
                        │
Engine 1B (Semantic) ───┼──► 3D FUSION ──► Engine 2 (Track update)
                        │         │
Layer 1 (Calibration) ──┘         └──────► Engine 3 (Prediction)
```

---

## Error Handling

| Condition | Action |
|-----------|--------|
| No depth at bbox | Use median depth of bbox region |
| Invalid bbox | Skip object, log warning |
| SMPL params missing | Use default T-pose |
| PLY template missing | Fall back to bbox only |
| Depth out of range | Clamp to max_depth (100m) |
| Too many objects | Limit to 50 closest |

---

## System Limits

```python
FUSION_PARAMS = {
    'max_objects': 50,
    'max_depth': 100.0,       # meters
    'min_depth': 0.5,         # meters
    'ema_alpha': 0.7,
    'bbox_expansion': 1.1,    # 10% margin
    'depth_samples': 5,       # points per bbox center
}
```

---

## Dependencies

- NumPy (array operations)
- SMPL model (avatar generation)
- PLY library (wireframe templates)
- Camera calibration (intrinsics)

---

## Files

| File | Purpose |
|------|---------|
| [arquitectura.svg](arquitectura.svg) | Component structure |
| [flujo.svg](flujo.svg) | Processing flow |
| `spec.md` | This document |
