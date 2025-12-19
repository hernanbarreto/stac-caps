# Engine 3: Behavior - Technical Specification

## Overview

Engine 3 implements **behavior prediction** for all tracked objects, combining:
- Trajectory forecasting based on physics/kinematics with acceleration
- Theory of Mind (ToM) intent inference with temporal smoothing
- Risk scoring with confidence intervals
- Cross-validation with optical flow

---

## Key Features

| Feature | Description |
|---------|-------------|
| **Trajectory Forecast** | Predict T+1s to T+5s with acceleration |
| **Theory of Mind** | Bayesian intent + temporal EMA smoothing |
| **Risk Scoring** | Multi-factor with quality weighting |
| **TTC Computation** | Confidence intervals + early exit |
| **Cross-Validation** | Optical flow redundancy check |

---

## Inputs

| Input | Type | Source |
|-------|------|--------|
| `tracks` | List[Track] | Engine 2 |
| `train_state` | TrainState | Vehicle dynamics |
| `danger_zones` | List[Zone] | Layer 1 (calibration) |
| `scene_context` | str | Layer 1 (PLATFORM/CROSSING) |
| `optical_flow` | Tensor[H×W×2] | Pre-process (optional) |

### Track Data Used
```python
# From Engine 2
track = {
    'track_id': int,
    'bbox3D': [x, y, z, w, h, d],
    'velocity': [vx, vy, vz],
    'acceleration': [ax, ay, az],      # NEW: from Kalman
    'category': 'PERSON'|'KNOWN'|'UNKNOWN',
    'quality_score': float,
    'smpl_params': {...},
    'smpl_history': [params × 5],      # NEW: pose history
    'history': [bbox3D × 10 frames],
    'intent_history': [Intent × 5]     # NEW: previous intents
}
```

---

## Outputs

| Output | Type | Description |
|--------|------|-------------|
| `predictions` | List[Prediction] | Future trajectories |
| `risk_scores` | Dict[tid → risk] | Per-track risk |
| `ttc` | TTCResult | Min TTC + confidence |
| `safety_margin` | float | Adjusted margin (m) |
| `validation_status` | str | VALIDATED/UNCERTAIN |

### Prediction Structure
```python
@dataclass
class Prediction:
    track_id: int
    trajectories: List[Trajectory]
    intent: Intent
    collision_prob: float
    ttc: float
    risk_score: float
    validated: bool                    # NEW: cross-validated
    
@dataclass
class Trajectory:
    positions: List[Tuple[3]]          # Optimistic/Nominal/Pessimistic
    timestamps: List[float]
    confidence: float
    acceleration_used: bool            # NEW

@dataclass
class Intent:
    state: str
    distraction_prob: float
    awareness_prob: float
    action_confidence: float
    smoothed: bool                     # NEW: EMA applied

@dataclass
class TTCResult:                       # NEW
    min: float
    mean: float
    max: float
    confidence: float                  # 1.0 = high certainty
```

---

## Components

### 1. Kinematic Trajectory Predictor (IMPROVED)

| Property | Value |
|----------|-------|
| Model | Constant acceleration (IMPROVED) |
| Horizon | 1s, 2s, 3s, 4s, 5s |
| Multi-modal | 3 scenarios: optimistic/nominal/pessimistic |
| Input | bbox3D + velocity + **acceleration** |
| Latency | **1 ms** |

```python
def predict_kinematic_v2(track, horizon=[1, 2, 3, 4, 5]):
    """
    Constant ACCELERATION model (improved).
    x(t) = x₀ + v₀×t + 0.5×a×t²
    """
    x, y, z = track.bbox3D[:3]
    vx, vy, vz = track.velocity
    ax, ay, az = track.acceleration  # NEW
    
    trajectories = {
        'optimistic': [],
        'nominal': [],
        'pessimistic': []
    }
    
    for t in horizon:
        # Base prediction with acceleration
        future_x = x + vx * t + 0.5 * ax * t**2
        future_y = y + vy * t + 0.5 * ay * t**2
        future_z = z + vz * t + 0.5 * az * t**2
        
        # Uncertainty grows with t²
        uncertainty = 0.1 * t**2
        
        trajectories['nominal'].append({
            'position': (future_x, future_y, future_z),
            'timestamp': t
        })
        
        # Optimistic: slower approach
        trajectories['optimistic'].append({
            'position': (future_x * 0.9, future_y * 0.9, future_z),
            'timestamp': t
        })
        
        # Pessimistic: faster approach
        trajectories['pessimistic'].append({
            'position': (future_x * 1.1, future_y * 1.1, future_z),
            'timestamp': t
        })
    
    return trajectories
```

### 2. SMPL Pose Predictor (IMPROVED)

| Property | Value |
|----------|-------|
| Input | SMPL pose + **pose_history** |
| Features | Body orientation + **pose velocity** |
| Purpose | Predict body rotation trend |
| Latency | **<1 ms** |

```python
def predict_from_pose_v2(smpl_params, smpl_history, velocity):
    """
    Use pose history to predict movement intention.
    """
    # Current analysis
    body_facing = smpl_params['body_pose'][:3]
    facing_track = compute_angle_to_track(body_facing)
    
    # NEW: Pose velocity (temporal derivative)
    if len(smpl_history) >= 2:
        pose_delta = smpl_history[-1]['body_pose'][:3] - smpl_history[-2]['body_pose'][:3]
        pose_velocity = pose_delta / DT  # rad/s
        
        # Predict future pose (0.5s ahead)
        predicted_pose = body_facing + pose_velocity * 0.5
        will_face_track = compute_angle_to_track(predicted_pose)
    else:
        pose_velocity = np.zeros(3)
        will_face_track = facing_track
    
    # Rotation towards track is dangerous
    rotating_towards = will_face_track < facing_track
    
    return {
        'facing_track': facing_track,
        'pose_velocity': pose_velocity,
        'rotating_towards': rotating_towards,
        'walk_direction': infer_walk_direction(smpl_params)
    }
```

### 3. Theory of Mind (ToM) (IMPROVED)

| Property | Value |
|----------|-------|
| Method | Bayesian + **temporal EMA** |
| Inputs | Pose, velocity, history, **context** |
| Priors | **Context-adaptive** |
| Latency | **1 ms** |

```python
def get_context_priors(scene_context):
    """
    NEW: Adaptive priors based on scene context.
    """
    CONTEXT_PRIORS = {
        'LEVEL_CROSSING': {
            'STATIC': 0.25,
            'LEAVING': 0.25,
            'APPROACHING': 0.25,
            'CROSSING': 0.25  # Higher chance at crossings
        },
        'PLATFORM': {
            'STATIC': 0.55,
            'LEAVING': 0.25,
            'APPROACHING': 0.15,
            'CROSSING': 0.05  # Lower chance on platforms
        },
        'OPEN_TRACK': {
            'STATIC': 0.40,
            'LEAVING': 0.30,
            'APPROACHING': 0.20,
            'CROSSING': 0.10
        }
    }
    return CONTEXT_PRIORS.get(scene_context, CONTEXT_PRIORS['OPEN_TRACK'])

def smooth_intent(current_intent, intent_history, alpha=0.7):
    """
    NEW: Temporal smoothing to prevent oscillation.
    """
    if not intent_history:
        return current_intent
    
    previous = intent_history[-1]
    
    # Smooth probabilities
    smoothed_probs = {}
    for state in INTENT_STATES:
        current_prob = current_intent.probs.get(state, 0)
        prev_prob = previous.probs.get(state, 0)
        smoothed_probs[state] = alpha * current_prob + (1-alpha) * prev_prob
    
    # Determine smoothed state
    smoothed_state = max(smoothed_probs, key=smoothed_probs.get)
    
    return Intent(
        state=smoothed_state,
        distraction_prob=alpha * current_intent.distraction_prob + 
                        (1-alpha) * previous.distraction_prob,
        awareness_prob=current_intent.awareness_prob,
        action_confidence=smoothed_probs[smoothed_state],
        smoothed=True
    )

def infer_intent_v2(track, smpl_params, context, intent_history):
    """
    Improved ToM with context priors and temporal smoothing.
    """
    # Context-adaptive priors
    priors = get_context_priors(context)
    
    # Observations
    velocity_mag = np.linalg.norm(track.velocity)
    facing_track = is_facing_track(smpl_params)
    moving_towards = is_moving_towards_track(track.velocity)
    
    # Distraction detection (expanded)
    head_down = is_head_down(smpl_params)
    arms_at_ears = has_arms_at_ears(smpl_params)
    irregular_gait = detect_irregular_gait(track.history)  # NEW
    carrying_object = detect_carrying(smpl_params)         # NEW
    
    distraction_prob = (
        0.25 * head_down +
        0.25 * arms_at_ears +
        0.25 * irregular_gait +
        0.25 * carrying_object
    )
    
    # Awareness check (train_direction comes from train_state.heading)
    train_direction = train_state.heading  # from input
    awareness_prob = compute_gaze_awareness(smpl_params, train_direction)
    
    # Update posteriors
    posteriors = update_bayesian(priors, {
        'velocity': velocity_mag,
        'facing': facing_track,
        'moving_towards': moving_towards,
        'distracted': distraction_prob
    })
    
    raw_intent = Intent(
        state=max(posteriors, key=posteriors.get),
        distraction_prob=distraction_prob,
        awareness_prob=awareness_prob,
        action_confidence=posteriors[max(posteriors, key=posteriors.get)],
        probs=posteriors,
        smoothed=False
    )
    
    # Apply temporal smoothing
    return smooth_intent(raw_intent, intent_history, alpha=0.7)
```

### 4. TTC Calculator (IMPROVED)

| Property | Value |
|----------|-------|
| Method | Vector intersection + **confidence intervals** |
| Output | TTCResult (min, mean, max, confidence) |
| Optimization | **Early exit** for emergency |
| Latency | **1 ms** |

```python
def compute_ttc_v2(train_state, predictions, max_tracks=30):
    """
    Improved TTC with confidence intervals and early exit.
    """
    train_pos = np.array(train_state.position)
    train_vel = np.array(train_state.velocity)
    
    # Sort by proximity for early exit
    sorted_preds = sorted(predictions, 
                          key=lambda p: distance_to_train(p.trajectories['nominal'][0]))
    
    ttc_samples = []
    
    for pred in sorted_preds[:max_tracks]:  # Limit for performance
        for scenario in ['optimistic', 'nominal', 'pessimistic']:
            traj = pred.trajectories[scenario]
            
            for point in traj:
                t = point['timestamp']
                obj_pos = np.array(point['position'])
                
                # Train position at time t
                train_future = train_pos + train_vel * t
                
                # Distance at time t
                distance = np.linalg.norm(obj_pos - train_future)
                
                # Check collision
                margin = get_safety_margin(pred.intent)
                if distance < margin:
                    ttc_samples.append(t)
                    
                    # EARLY EXIT for emergency
                    if t < EMERGENCY_THRESHOLD:
                        return TTCResult(
                            min=t,
                            mean=t,
                            max=t,
                            confidence=0.99  # High confidence emergency
                        )
    
    if not ttc_samples:
        return TTCResult(min=float('inf'), mean=float('inf'), 
                         max=float('inf'), confidence=1.0)
    
    # Compute confidence interval
    ttc_min = np.min(ttc_samples)
    ttc_mean = np.mean(ttc_samples)
    ttc_max = np.max(ttc_samples)
    
    # Confidence based on spread
    spread = ttc_max - ttc_min
    confidence = np.clip(1.0 - spread / 10.0, 0.3, 1.0)
    
    return TTCResult(min=ttc_min, mean=ttc_mean, max=ttc_max, confidence=confidence)
```

### 5. Risk Score Calculator (IMPROVED)

| Property | Value |
|----------|-------|
| Factors | TTC, intent, distraction, category, **quality** |
| Weights | 0.35, 0.25, 0.15, 0.10, **0.15** |
| Output | [0.0, 1.0] with **temporal smoothing** |
| Latency | **<1 ms** |

```python
def compute_risk_score_v2(track, intent, ttc_result, prev_risk=None):
    """
    Improved risk scoring with quality and smoothing.
    """
    # TTC factor (use conservative min)
    ttc = ttc_result.min
    ttc_factor = 1.0 - min(ttc / 10.0, 1.0)
    
    # Intent factor
    intent_weights = {
        'STATIC': 0.1,
        'LEAVING': 0.2,
        'APPROACHING': 0.7,
        'CROSSING': 1.0
    }
    intent_factor = intent_weights.get(intent.state, 0.5)
    
    # Distraction factor
    distraction_factor = intent.distraction_prob
    
    # Category factor
    category_weights = {
        'PERSON': 1.0,
        'KNOWN': 0.7,
        'UNKNOWN': 0.3
    }
    category_factor = category_weights.get(track.category, 0.5)
    
    # NEW: Quality factor (low quality = less certain = higher risk)
    quality_factor = 1.0 - track.quality_score
    
    # Weighted combination (adjusted weights)
    raw_risk = (
        0.35 * ttc_factor +
        0.25 * intent_factor +
        0.15 * distraction_factor +
        0.10 * category_factor +
        0.15 * quality_factor
    )
    
    # Modulate by TTC confidence (low confidence = higher risk)
    confidence_adjusted = raw_risk * (2.0 - ttc_result.confidence)
    
    # NEW: Temporal smoothing
    if prev_risk is not None:
        final_risk = 0.7 * confidence_adjusted + 0.3 * prev_risk
    else:
        final_risk = confidence_adjusted
    
    return np.clip(final_risk, 0, 1)
```

### 6. Cross-Validation (NEW)

| Property | Value |
|----------|-------|
| Method | Compare kinematic vs optical flow |
| Threshold | 1.5m divergence |
| Output | VALIDATED / UNCERTAIN |
| Latency | **<1 ms** |

```python
def cross_validate_trajectory(kinematic_pred, optical_flow, roi):
    """
    NEW: Validate trajectory prediction with optical flow.
    """
    if optical_flow is None:
        return 'UNVALIDATED'
    
    # Extract flow at object location
    x, y = roi['center']
    flow_vector = optical_flow[int(y), int(x)]
    
    # Convert to 3D velocity estimate
    flow_velocity = flow_to_velocity(flow_vector, depth=roi['depth'])
    
    # Compare with kinematic prediction
    kinematic_velocity = kinematic_pred[0]['velocity']
    
    divergence = np.linalg.norm(kinematic_velocity - flow_velocity)
    
    if divergence > VALIDATION_THRESHOLD:
        return 'UNCERTAIN'
    
    return 'VALIDATED'
```

---

## Processing Flow

```
1. RECEIVE tracks from Engine 2
           ↓
2. FOR EACH track:
   ├── 2a. PREDICT trajectory (kinematic + acceleration)  [IMPROVED]
   ├── 2b. IF PERSON: Pose velocity prediction            [NEW]
   ├── 2c. IF PERSON: ToM with context priors             [IMPROVED]
   └── 2d. Apply intent temporal smoothing                [NEW]
           ↓
3. CROSS-VALIDATE with optical flow                       [NEW]
           ↓
4. COMPUTE TTC with confidence intervals                  [IMPROVED]
   └── Early exit if < 1.0s                               [NEW]
           ↓
5. CALCULATE risk scores with quality                     [IMPROVED]
           ↓
6. ADJUST safety margins
           ↓
7. OUTPUT → Safety Veto
```

---

## Timing Budget

```
Kinematic Prediction:    1 ms (with acceleration)
SMPL Pose Analysis:     <1 ms (with pose velocity)
ToM Inference:           1 ms (with context + EMA)
Cross-Validation:       <1 ms (optical flow check)
TTC Calculation:        <1 ms (with early exit)
Risk Scoring:           <1 ms

TOTAL:                   3 ms ✅
```

---

## Safety Margin Adjustment

| Intent State | Base | Multiplier | Distracted | Final |
|--------------|------|------------|------------|-------|
| STATIC | 5.0m | ×1.0 | ×1.0 | 5.0m |
| LEAVING | 5.0m | ×0.8 | ×1.0 | 4.0m |
| APPROACHING | 5.0m | ×1.5 | ×1.25 | 9.4m |
| CROSSING | 5.0m | ×2.0 | ×1.25 | 12.5m |

---

## TTC Thresholds

| TTC | Level | Action | Confidence Impact |
|-----|-------|--------|-------------------|
| > 5.0s | GREEN | Normal | Use mean TTC |
| 3.0-5.0s | YELLOW | Caution | Use mean TTC |
| 1.0-3.0s | ORANGE | Warning | Use min TTC |
| < 1.0s | RED | Emergency | Immediate brake |

---

## Integration with Safety Veto

```
Engine 3                    Safety Veto
    │                            │
    │ predictions[] ──────────►  │
    │ risk_scores{} ──────────►  │
    │ ttc_result ─────────────►  │  (min, mean, max, confidence)
    │ safety_margin ──────────►  │
    │ validation_status ──────►  │  [NEW]
    │                            │
    │                   ┌────────┤
    │                   │ IF ttc.min < 1.0s:
    │                   │   → EMERGENCY BRAKE
    │                   │ IF validation == 'UNCERTAIN':
    │                   │   → Use conservative action
    │                   └────────┤
```

---

## Error Handling

| Condition | Action |
|-----------|--------|
| No tracks | Skip prediction, TTC=∞ |
| Missing SMPL | Use kinematic only |
| Missing acceleration | Assume a=0, use velocity |
| Low quality track | Weight in risk + use conservative TTC |
| ToM uncertain | Use conservative margin |
| Validation uncertain | Flag for Safety Veto |
| First frame | No smoothing, kinematic only |
| > 30 tracks | Early exit after top 30 by proximity |

---

## System Limits

```python
ENGINE3_PARAMS = {
    'max_horizon': 5.0,              # seconds
    'intent_ema_alpha': 0.7,         # smoothing factor
    'risk_ema_alpha': 0.7,           # risk smoothing
    'max_tracks_ttc': 30,            # early exit limit
    'validation_threshold': 1.5,     # meters divergence
    'emergency_ttc': 1.0,            # seconds
    'warning_ttc': 3.0,              # seconds
    'base_safety_margin': 5.0        # meters
}
```

---

## Dependencies

- NumPy (vector math)
- SciPy (Bayesian inference)
- SMPL model (pose analysis)
- OpenCV (optical flow processing)

---

## Files

| File | Purpose |
|------|---------|
| [arquitectura.svg](arquitectura.svg) | Component structure |
| [flujo.svg](flujo.svg) | Processing logic |
| `spec.md` | This document |
