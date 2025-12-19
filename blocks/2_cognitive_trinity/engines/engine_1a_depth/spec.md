# Engine 1A: Depth - Technical Specification

## Overview

Engine 1A implements **monocular depth estimation** using DepthAnything-v2. It converts 2D images to dense 3D point clouds, enabling:
- bbox3D calculation for all detected objects
- TTC (Time-to-Collision) computation
- 3D spatial reasoning without LiDAR/Radar

---

## Key Features

| Feature | Description |
|---------|-------------|
| **Monocular Depth** | Single camera depth estimation |
| **Dense Output** | Depth value per pixel |
| **Metric Scale** | Real-world meters via calibration |
| **Rail-Optimized** | Finetuned on railway domain |
| **Temporal Smoothing** | EMA for noise reduction |
| **Edge Refinement** | Guided filter for precision |

---

## Inputs

| Input | Type | Source |
|-------|------|--------|
| `frame` | Tensor [H×W×3] | Pre-process |
| `intrinsics` | CameraMatrix | Calibration (Layer 1) |
| `scale_factor` | float | Rail calibration result |
| `prev_depth` | Tensor [H×W] | Previous frame (optional) |

---

## Outputs

| Output | Type | Description |
|--------|------|-------------|
| `depth_map` | Tensor [H×W] | Refined metric depth (meters) |
| `point_cloud` | Tensor [H×W×3] | XYZ per pixel |
| `confidence` | Tensor [H×W] | Multi-factor reliability |

### Depth Map
```python
@dataclass
class DepthOutput:
    depth_map: np.ndarray       # [H, W] float32 in meters
    point_cloud: np.ndarray     # [H, W, 3] XYZ coordinates
    confidence: np.ndarray      # [H, W] float32 [0.0-1.0]
    max_range: float            # Maximum reliable range (200m)
    min_range: float            # Minimum reliable range (0.5m)
    smoothed: bool              # Whether temporal smoothing applied
```

---

## Components

### 1. DepthAnything-v2
| Property | Value |
|----------|-------|
| Architecture | ViT-L/14 (Vision Transformer) |
| Input Resolution | 518×518 (internal) |
| Output | Relative depth (normalized) |
| Finetuning | Railway domain (rails, platforms, trains) |
| Optimization | TensorRT FP16 |
| Latency | **18 ms** |

### 2. Metric Scale Calibration
| Property | Value |
|----------|-------|
| Source | Rail Track Geometry (Layer 1) |
| Method | Known track width (1435mm standard gauge) |
| Fallback | SuperPoint landmarks |
| Latency | **<1 ms** |

### 3. Outlier Detection (NEW)
| Property | Value |
|----------|-------|
| Method | Median filter (3×3) |
| Threshold | >20% deviation from median |
| Action | Replace with median value |
| Latency | **<1 ms** |

```python
def detect_and_fix_outliers(depth_map, kernel_size=3, threshold=0.2):
    """Remove depth outliers using median filter."""
    median_depth = median_filter(depth_map, size=kernel_size)
    deviation = np.abs(depth_map - median_depth) / (median_depth + 1e-6)
    
    outliers = deviation > threshold
    depth_clean = depth_map.copy()
    depth_clean[outliers] = median_depth[outliers]
    
    return depth_clean, outliers
```

### 4. Edge-aware Refinement (NEW)
| Property | Value |
|----------|-------|
| Method | Guided Filter |
| Guide Image | RGB frame |
| Radius | 2 pixels |
| Regularization (ε) | 0.01 |
| Latency | **1 ms** |

```python
def guided_filter(guide, depth, radius=2, eps=0.01):
    """
    Edge-aware depth refinement using RGB as guide.
    Preserves edges while smoothing flat regions.
    """
    mean_I = box_filter(guide, radius)
    mean_p = box_filter(depth, radius)
    mean_Ip = box_filter(guide * depth, radius)
    cov_Ip = mean_Ip - mean_I * mean_p
    
    mean_II = box_filter(guide * guide, radius)
    var_I = mean_II - mean_I * mean_I
    
    a = cov_Ip / (var_I + eps)
    b = mean_p - a * mean_I
    
    mean_a = box_filter(a, radius)
    mean_b = box_filter(b, radius)
    
    return mean_a * guide + mean_b
```

### 5. Temporal Smoothing (NEW)
| Property | Value |
|----------|-------|
| Method | Exponential Moving Average |
| Alpha (α) | 0.7 (favor current) |
| Motion Compensation | Yes (optical flow) |
| Latency | **1 ms** |

```python
def temporal_smooth(depth_current, depth_previous, alpha=0.7, flow=None):
    """
    EMA smoothing with optional motion compensation.
    alpha: weight for current frame (0.7 = favor new data)
    """
    if depth_previous is None:
        return depth_current
    
    if flow is not None:
        # Warp previous depth using optical flow
        depth_previous = warp_with_flow(depth_previous, flow)
    
    smoothed = alpha * depth_current + (1 - alpha) * depth_previous
    return smoothed
```

### 6. Enhanced Confidence System (NEW)
| Property | Value |
|----------|-------|
| Factors | Range, Texture, Edges, Temporal |
| Weights | 0.4, 0.2, 0.2, 0.2 |
| Output | [0.0, 1.0] per pixel |
| Latency | **<1 ms** |

```python
def compute_enhanced_confidence(depth_map, rgb, depth_prev=None, max_range=200):
    """
    Multi-factor confidence computation.
    Combines: range, texture richness, edge alignment, temporal consistency.
    """
    H, W = depth_map.shape
    
    # Factor 1: Range-based (40%)
    range_conf = np.clip(1.0 - (depth_map / max_range), 0, 1)
    range_conf = np.where(depth_map < 50, 0.95,
                 np.where(depth_map < 100, 0.80,
                 np.where(depth_map < 200, 0.60, 0.10)))
    
    # Factor 2: Texture richness (20%)
    gray = rgb_to_gray(rgb)
    texture = laplacian_variance(gray)
    texture_conf = np.clip(texture / 100.0, 0, 1)
    
    # Factor 3: Edge alignment (20%)
    rgb_edges = sobel(gray)
    depth_edges = sobel(depth_map)
    edge_conf = 1.0 - np.abs(rgb_edges - depth_edges)
    
    # Factor 4: Temporal consistency (20%)
    if depth_prev is not None:
        temporal_diff = np.abs(depth_map - depth_prev) / (depth_map + 1e-6)
        temporal_conf = np.clip(1.0 - temporal_diff, 0, 1)
    else:
        temporal_conf = np.ones((H, W)) * 0.5
    
    # Weighted combination
    confidence = (0.4 * range_conf + 
                  0.2 * texture_conf + 
                  0.2 * edge_conf + 
                  0.2 * temporal_conf)
    
    return np.clip(confidence, 0, 1)
```

### 7. Point Cloud Generator
| Property | Value |
|----------|-------|
| Input | Refined metric depth + intrinsics |
| Method | Inverse projection |
| Output | XYZ per pixel in camera frame |
| Latency | **3 ms** (GPU accelerated) |

---

## Processing Flow

```
1. RECEIVE frame from Pre-process
           ↓
2. RESIZE to 518×518 (DepthAnything input)
           ↓
3. INFER relative depth (DepthAnything-v2)
           ↓
4. APPLY scale factor (metric calibration)
           ↓
5. DETECT & FIX outliers (median filter) ← NEW
           ↓
6. APPLY edge-aware refinement (guided filter) ← NEW
           ↓
7. APPLY temporal smoothing (EMA) ← NEW
           ↓
8. RESIZE depth back to original resolution
           ↓
9. COMPUTE point cloud (inverse projection)
           ↓
10. GENERATE enhanced confidence map ← IMPROVED
           ↓
11. OUTPUT: depth_map + point_cloud + confidence → Engine 1B
```

---

## Timing Budget

```
Preprocessing:          2 ms (resize to 518×518)
DepthAnything-v2:      18 ms (ViT-L inference)
Metric Scaling:        <1 ms
Outlier Detection:     <1 ms (median filter)
Edge Refinement:        1 ms (guided filter)
Temporal Smoothing:     1 ms (EMA)
Upscale + Point Cloud:  2 ms

TOTAL:                 25 ms ✅
```

---

## Error Precision

| Distance | Expected Error | Confidence |
|----------|----------------|------------|
| < 50m | < 5% | High (>0.8) |
| 50-100m | < 15% | Medium (0.5-0.8) |
| 100-200m | < 30% | Low (<0.5) |
| > 200m | Not reliable | Very Low (<0.1) |

---

## Integration with Engine 1B

```
Engine 1A                    Engine 1B
    │                            │
    │ depth_map (refined) ────►  │
    │ point_cloud ────────────►  │
    │ confidence (enhanced) ──►  │
    │                            │
    │                   ┌────────┤
    │                   │ For each detection:
    │                   │   bbox2D + depth → bbox3D
    │                   │   confidence-weighted
    │                   └────────┤
```

---

## Error Handling

| Condition | Action |
|-----------|--------|
| Calibration unavailable | Use default scale (1.0) |
| Depth out of range | Clamp to [0.5, 200] meters |
| Low confidence region | Mark as unreliable |
| Occlusion artifacts | Outlier detection fixes |
| First frame | Skip temporal smoothing |
| High outlier % (>10%) | Trigger health warning |

---

## System Limits

```python
DEPTH_PARAMS = {
    'max_range': 200.0,            # meters
    'min_range': 0.5,              # meters
    'temporal_alpha': 0.7,         # EMA weight
    'outlier_threshold': 0.2,      # 20% deviation
    'guided_radius': 2,            # pixels
    'guided_eps': 0.01,            # regularization
    'confidence_weights': [0.4, 0.2, 0.2, 0.2]  # range, texture, edge, temporal
}
```

---

## Dependencies

- [DepthAnything-v2](https://github.com/LiheYoung/Depth-Anything-V2) (Apache 2.0)
- PyTorch / TensorRT (inference)
- OpenCV (guided filter, image ops)
- SciPy (median filter)

---

## Files

| File | Purpose |
|------|---------|
| [arquitectura.svg](arquitectura.svg) | Component structure |
| [flujo.svg](flujo.svg) | Processing logic |
| `spec.md` | This document |
