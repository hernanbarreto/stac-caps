# Engine 2: Persistence - Technical Specification

## Overview

Engine 2 implements **temporal persistence** (object permanence) using multi-object tracking. It assigns and maintains stable **Track IDs** across frames, enabling:
- Avatar cache lookup in Engine 1B
- Trajectory prediction in Engine 3
- TTC calculation continuity

---

## Key Features

| Feature | Description |
|---------|-------------|
| **Track ID Assignment** | Unique ID per detected object |
| **Re-identification** | Match same object after occlusion |
| **Ghost State** | Keep track alive when hidden |
| **Kalman Prediction** | Propagate position during occlusion |
| **Quality Metrics** | Track reliability scoring |
| **LRU Eviction** | Memory management for max 50 tracks |

---

## Inputs

| Input | Type | Source |
|-------|------|--------|
| `detections` | List[Detection] | Engine 1B |
| `frame` | Tensor | Pre-process (for ReID) |
| `prev_tracks` | List[Track] | Previous frame |

---

## Outputs

| Output | Type | Description |
|--------|------|-------------|
| `tracks` | List[Track] | Updated tracks with IDs + quality |
| `assignments` | Dict[det_idx, track_id] | Detection → Track mapping |

### Track Structure
```python
@dataclass
class Track:
    # Identity
    track_id: int              # Unique identifier
    state: TrackState          # TENTATIVE | ACTIVE | GHOST | DELETED
    category: Category         # PERSON | KNOWN | UNKNOWN
    
    # Spatial
    bbox_3d: BBox3D            # Last known 3D position
    velocity: Tuple[3]         # (vx, vy, vz) m/s
    
    # Temporal
    age: int                   # Frames since creation
    time_since_update: int     # Frames since last detection
    
    # Appearance (EMA updated)
    features: np.ndarray       # ReID embedding [512]
    
    # Quality Metrics (NEW)
    quality_score: float       # f(confidence, age, match_frequency)
    match_frequency: float     # % frames with successful match
    confidence: float          # Current detection confidence
    
    # Cache References
    smpl_ref: Optional[int]    # Cache key for Engine 1B (PERSON)
    ply_ref: Optional[str]     # PLY template reference (KNOWN)
```

### TrackState
```python
class TrackState(Enum):
    TENTATIVE = 0    # New, unconfirmed (< 3 matches)
    ACTIVE = 1       # Confirmed, visible
    GHOST = 2        # Temporarily lost (occluded)
    DELETED = 3      # Removed from tracking
```

### Quality Score Calculation
```python
def compute_quality_score(track: Track) -> float:
    """
    Quality score: weighted combination of reliability metrics.
    Range: 0.0 (poor) to 1.0 (excellent)
    """
    age_factor = min(track.age / 30, 1.0)           # Mature = better
    match_factor = track.match_frequency            # High match = better
    conf_factor = track.confidence                  # High conf = better
    recency_factor = 1.0 - (track.time_since_update / 30)  # Recent = better
    
    return 0.3 * age_factor + 0.3 * match_factor + 0.2 * conf_factor + 0.2 * recency_factor
```

---

## Components

### 1. BotSORT Core
| Property | Value |
|----------|-------|
| Algorithm | BoT-SORT (Bag of Tricks) |
| Motion Model | Kalman Filter (8-state) |
| IoU Threshold | 0.3 |
| Max Age | 30 frames (ghost lifetime) |
| Confirm Threshold | 3 frames |
| Latency | **3 ms** |

### 2. OSNet ReID (with EMA Update)
| Property | Value |
|----------|-------|
| Architecture | OSNet-x0.25 (Omni-Scale) |
| Output | 512-dim embedding |
| Distance | Cosine similarity |
| Threshold | 0.4 (match) |
| **EMA Update** | α=0.7 (favor history) |
| Latency | **2 ms** (batched) |

```python
# Exponential Moving Average for embedding stability
def update_embedding(track, new_embedding, alpha=0.7):
    """Stable appearance model via EMA."""
    track.features = alpha * track.features + (1 - alpha) * new_embedding
```

### 3. Kalman Filter (Adaptive Noise)
| Property | Value |
|----------|-------|
| State Vector | [x, y, z, vx, vy, vz, w, h] |
| Measurement | [x, y, z, w, h] |
| **Process Noise** | Adaptive (Q × 1/confidence) |
| Purpose | Predict ghost state positions |
| Latency | **<1 ms** |

```python
# Adaptive process noise based on confidence
def update_kalman_noise(kalman, track):
    """Higher noise when confidence is low."""
    kalman.Q = BASE_Q * (1.0 / max(track.confidence, 0.1))
```

### 4. Track Memory (LRU Cache)
| Property | Value |
|----------|-------|
| **Max Size** | 50 tracks |
| **Eviction Policy** | Least Recently Updated |
| Storage | Dict[track_id → Track] |
| Memory per Track | ~100KB (history + embeddings) |

```python
class TrackMemory(LRUCache):
    """LRU cache for track storage with automatic eviction."""
    def __init__(self, max_size=50):
        super().__init__(max_size)
    
    def evict_policy(self):
        # Evict track with lowest quality_score among oldest
        candidates = sorted(self.tracks, key=lambda t: (t.quality_score, -t.time_since_update))
        return candidates[0] if candidates else None
```

---

## Processing Flow

```
1. RECEIVE detections from Engine 1B
           ↓
2. EXTRACT ReID features (crop → OSNet)
           ↓
3. PREDICT existing tracks (Kalman + Adaptive Q)
           ↓
4. ASSOCIATE detections to tracks
   ├── Stage 1: IoU matching (high confidence)
   └── Stage 2: ReID matching (appearance)
           ↓
5. UPDATE matched tracks
   ├── bbox, velocity, features (EMA)
   ├── quality_score, match_frequency
   └── confidence
           ↓
6. CREATE new tracks (unmatched detections)
           ↓
7. MANAGE tracks
   ├── Ghost: age > max_age → DELETE
   ├── LRU: count > 50 → EVICT lowest quality
   └── else → PROPAGATE via Kalman
           ↓
8. OUTPUT: Updated tracks + assignments
```

---

## Timing Budget

```
OSNet ReID:          2 ms (batched + EMA update)
Kalman Predict:     <1 ms (adaptive noise)
Association:        <1 ms (Hungarian)
Update + Quality:   <1 ms
LRU Management:     <1 ms

TOTAL:               5 ms
```

---

## Occlusion Handling

```
Normal State:
   Detection → Match → Update → ACTIVE
   ↳ quality_score increases

Occlusion Start:
   No Detection → No Match → Kalman Predict → GHOST
   ↳ confidence decays: conf *= 0.95
   ↳ quality_score decreases
   
During Occlusion (up to 30 frames):
   Ghost Track → Kalman Propagate → Maintain ID
   ↳ Position estimated from velocity
   ↳ Kalman Q increases (adaptive noise)
   
Re-appearance:
   Detection → ReID Match → Update → ACTIVE
   ↳ Use EMA embedding for stable matching
   ↳ quality_score recovers
```

---

## Error Handling

| Condition | Action |
|-----------|--------|
| No detections | Only update ghosts |
| Track lost > max_age | Delete track |
| ReID ambiguous | Prefer IoU match |
| ID collision | Assign new unique ID |
| **Memory full (>50)** | LRU eviction |
| **Low quality track** | Priority for eviction |

---

## System Limits

```python
MAX_PARAMS = {
    'max_tracks': 50,              # LRU cache size
    'max_detections_per_frame': 30,
    'history_length': 10,          # Frames of history
    'ghost_max_age': 30,           # Frames as ghost
    'tentative_threshold': 3,      # Frames to confirm
    'ema_alpha': 0.7,              # Embedding update rate
    'confidence_decay': 0.95       # Ghost confidence decay
}
```

---

## Dependencies

- [BotSORT](https://github.com/NirAharon/BoT-SORT) (MIT)
- [OSNet](https://github.com/KaiyangZhou/deep-person-reid) (MIT)
- Kalman Filter implementation

---

## Integration with Engine 1B

```
Engine 1B                    Engine 2
    │                            │
    │ detections[] ───────────►  │
    │ (bbox3D, category)         │
    │                            │
    │ ◄─────────── tracks[]      │
    │ (track_id, quality_score)  │
    │                            │
    ├── Avatar Cache lookup ◄────┤
    │   (PERSON: cache[tid])     │
    │                            │
    └── PLY lookup ◄─────────────┤
        (KNOWN: ply_ref)         │
```

---

## Files

| File | Purpose |
|------|---------|
| [arquitectura.svg](arquitectura.svg) | Component structure |
| [flujo.svg](flujo.svg) | Processing logic |
| `spec.md` | This document |
