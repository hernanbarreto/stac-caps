# Layer 1: Calibration & Localization - Technical Specification

## Overview

Layer 1 provides **adaptive calibration** for the monocular vision system. It establishes and maintains the metric scale relationship between 2D images and real-world 3D coordinates using railway-specific geometry.

---

## Key Features

| Feature | Description |
|---------|-------------|
| **Hard Initialization** | Human-assisted rail head selection |
| **Online Learning** | Automatic landmark discovery |
| **Robust Fallback** | Occlusion handling via landmarks |
| **Metric Scale** | Real-world meters from pixels |

---

## Calibration Stages

### Stage 1: Hard Initialization (Human-in-the-Loop)

| Property | Value |
|----------|-------|
| Trigger | System startup or reset |
| Method | Operator selects rail heads |
| Ground Truth | 1435mm (standard gauge) |
| Output | Initial camera-to-world transform |

```python
def hard_initialization(frame, operator_clicks):
    """
    Human-assisted metric scale initialization.
    
    Operator clicks on two visible rail heads.
    Distance between them = 1435mm (standard gauge).
    """
    left_rail, right_rail = operator_clicks
    
    # Pixel distance
    pixel_distance = euclidean_distance(left_rail, right_rail)
    
    # Compute scale factor
    scale_factor = 1.435 / pixel_distance  # meters per pixel
    
    # Compute extrinsics (camera to rail frame)
    extrinsics = estimate_pose_from_rails(left_rail, right_rail, intrinsics)
    
    return CalibrationResult(
        scale_factor=scale_factor,
        extrinsics=extrinsics,
        method='HARD_INIT',
        confidence=0.99
    )
```

---

### Stage 2: Online Learning (Landmarks)

| Property | Value |
|----------|-------|
| Trigger | Continuous during operation |
| Method | SuperPoint keypoint detection |
| Purpose | Refine calibration, handle drift |
| Storage | Landmark database (LRU, max 1000) |

```python
class LandmarkDB:
    """Persistent landmark database for calibration refinement."""
    
    def __init__(self, max_size=1000):
        self.landmarks = LRUCache(max_size)
    
    def add_landmark(self, keypoint, descriptor, world_position):
        """Add a new stable landmark."""
        landmark = Landmark(
            descriptor=descriptor,
            world_pos=world_position,
            first_seen=time.time(),
            observations=1
        )
        self.landmarks[keypoint.id] = landmark
    
    def match_and_refine(self, current_keypoints, current_descriptors):
        """Match current frame to database, refine pose."""
        matches = match_descriptors(current_descriptors, self.get_all_descriptors())
        
        if len(matches) >= 4:
            # PnP solve for pose refinement
            refined_pose = solve_pnp(
                [self.landmarks[m.db_id].world_pos for m in matches],
                [current_keypoints[m.query_id] for m in matches],
                intrinsics
            )
            return refined_pose, len(matches)
        return None, 0
```

---

### Stage 3: Robust Fallback (Occlusion Handler)

| Property | Value |
|----------|-------|
| Trigger | Rails occluded (e.g., by train) |
| Method | Switch to landmark-only calibration |
| Guarantee | Zero drift during occlusion |

```python
def handle_occlusion(frame, rail_visible, landmark_db):
    """
    Fallback calibration when rails are not visible.
    """
    if rail_visible:
        # Normal: use rail geometry
        return calibrate_from_rails(frame)
    else:
        # Fallback: use stored landmarks
        pose, num_matches = landmark_db.match_and_refine(frame)
        
        if num_matches >= 4:
            return CalibrationResult(
                extrinsics=pose,
                method='LANDMARK_FALLBACK',
                confidence=min(num_matches / 10, 0.9)
            )
        else:
            # Critical: not enough landmarks
            return CalibrationResult(
                extrinsics=last_known_pose,
                method='LAST_KNOWN',
                confidence=0.5,
                warning='LOW_CONFIDENCE'
            )
```

---

## Outputs

| Output | Type | Description |
|--------|------|-------------|
| `intrinsics` | CameraMatrix [3×3] | Focal length, principal point |
| `extrinsics` | (R, t) | Rotation + translation |
| `scale_factor` | float | Meters per pixel at reference |
| `landmark_count` | int | Active landmarks |
| `calibration_confidence` | float | [0.0, 1.0] |

### CalibrationResult Structure
```python
@dataclass
class CalibrationResult:
    intrinsics: np.ndarray      # [3, 3] camera matrix K
    extrinsics: Tuple[R, t]     # Rotation, translation
    scale_factor: float         # meters/pixel at rail plane
    method: str                 # HARD_INIT | RAIL_GEOMETRY | LANDMARK
    confidence: float           # [0.0, 1.0]
    landmark_count: int         # Active landmarks in DB
```

---

## Rail Geometry Reference

```
Standard Gauge (UIC/EU/US):
├── Track Width: 1435mm (4 ft 8.5 in)
├── Rail Height: ~172mm (UIC 60)
└── Used for: Metric scale ground truth

Detection Method:
├── Line detection (Hough)
├── Vanishing point estimation
└── Rail head extraction
```

---

## Timing

| Stage | Latency | Frequency |
|-------|---------|-----------|
| Hard Init | ~5 seconds | Once at startup |
| Rail Detection | <5 ms | Every frame |
| Landmark Match | <3 ms | Every frame |
| Fallback Switch | <1 ms | On occlusion |

**Calibration does NOT add to per-frame latency** (runs parallel to Engine 1).

---

## Error Handling

| Condition | Action |
|-----------|--------|
| No rail visible | Switch to landmark fallback |
| < 4 landmarks | Use last known pose, log warning |
| Operator timeout | Use automatic detection |
| Large drift detected | Request re-initialization |
| Camera shake | Increase Kalman noise |

---

## Configuration

```python
CALIBRATION_PARAMS = {
    'rail': {
        'gauge_mm': 1435,
        'detection_method': 'edge_hough',
        'min_rail_length_px': 200
    },
    'landmarks': {
        'max_db_size': 1000,
        'keypoint_detector': 'SuperPoint',
        'match_threshold': 0.7,
        'min_matches_for_pnp': 4
    },
    'fallback': {
        'occlusion_frames_to_switch': 5,
        'low_confidence_threshold': 0.5
    }
}
```

---

## Integration

```
Human Operator (init) ──┐
                        │
Camera Frame ───────────┼──► Layer 1 ──► Calibration Result
                        │       │
Rail Geometry ──────────┘       └──► Engine 1A (scale)
                                     Engine 1B (projection)
                                     3D Fusion (extrinsics)
```

---

## Files

| File | Purpose |
|------|---------|
| [arquitectura.svg](arquitectura.svg) | Component structure |
| [flujo.svg](flujo.svg) | Calibration flow |
| `spec.md` | This document |
