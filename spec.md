# STAC-CAPS: Spatial-Temporal Awareness & Collision Avoidance Perception System

**Version:** 3.3 (Platform-Ready)  
**Date:** 2025-12-18  
**Domain:** Railway Safety / Autonomous Perception

---

## Overview

STAC-CAPS is a **real-time monocular vision system** for railway collision avoidance. It processes single-camera video to detect, track, and predict the behavior of obstacles in the train's path, enabling timely braking decisions.

### Key Capabilities

| Capability | Description |
|------------|-------------|
| **Monocular 3D** | Depth estimation without LiDAR/Radar |
| **Multi-Object Tracking** | Persistent IDs across frames |
| **Behavior Prediction** | Intent inference (Theory of Mind) |
| **Time-to-Collision** | Real-time TTC with confidence intervals |
| **Privacy by Design** | SMPL avatars, no facial data stored |
| **Federated Learning** | Multi-train fleet coordination |

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        STAC-CAPS v3.3                               │
├─────────────────────────────────────────────────────────────────────┤
│  0. SENSOR INPUT          │ Monocular RGB (IMX490 HDR)              │
│  1. CALIBRATION           │ Rail geometry + Landmarks               │
│  2. COGNITIVE TRINITY     │ Engines 1A/1B/2/3                       │
│  3. 3D FUSION             │ Depth + Semantic → 3D Scene             │
│  4. META-COGNITION        │ Fleet sync, Governance, Privacy         │
│  5. SAFETY VETO           │ TTC-based decision, GPIO brake          │
│  6. OUTPUT                │ CAN/SCADA/MQTT                          │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Timing Budget

| Component | Timing | Mode |
|-----------|--------|------|
| Frame Capture | 16 ms | sync |
| Pre-process | 4 ms | sync |
| Engine 1A: Depth | 25 ms | **parallel** |
| Engine 1B: Semantic | 25 ms | **parallel** |
| Visual Veto | 7 ms | **parallel** |
| 3D Fusion | 3 ms | sync |
| 3D Projection | 2 ms | sync |
| Engine 2: Tracking | 5 ms | sync |
| Federated Micro-sync | 1 ms | sync |
| Engine 3: Behavior | 3 ms | sync |
| Consensus Check | 5 ms | sync |
| TTC + Decision | 2 ms | sync |
| Traceability + Output | 5 ms | sync |
| **TOTAL** | **~78 ms** | **< 100 ms ✅** |

---

## Cognitive Trinity (Engines)

### Engine 1A: Depth
- **Model:** DepthAnything-v2 (ViT-L, TensorRT)
- **Output:** Metric depth map + point cloud + confidence
- **Features:** Refinement pipeline (outlier, guided filter, EMA)
- **Budget:** 25 ms

### Engine 1B: Semantic
- **Model:** RT-DETR-X (transformer detector)
- **Output:** 3-category detections with 3D representation
  - **Personas:** SMPL Avatar (6890 vertices)
  - **Objetos Conocidos:** PLY wireframe from library
  - **Objetos Desconocidos:** bbox3D only
- **Budget:** 25 ms

### Engine 2: Persistence
- **Model:** BotSORT + OSNet (ReID)
- **Output:** Stable track IDs, velocity, quality scores
- **Features:** LRU cache (50 tracks), adaptive Kalman, EMA embeddings
- **Budget:** 5 ms

### Engine 3: Behavior
- **Model:** Kinematic prediction + Theory of Mind (Bayesian)
- **Output:** Trajectories, TTC with confidence intervals, risk scores
- **Features:** Cross-validation with optical flow, early exit
- **Budget:** 3 ms

---

## 3D Fusion

Combines Engine 1A (depth) + Engine 1B (semantic) + Engine 2 (tracks from t-1) into unified 3D scene.

| Component | Function |
|-----------|----------|
| Depth-to-3D Projector | bbox2D → bbox3D using camera intrinsics |
| SMPL Placer | Position avatar mesh in world coords |
| PLY Aligner | Scale and place known object wireframes |
| Temporal Smoother | EMA smoothing across frames |

**Budget:** 3 ms

---

## Safety Veto

Final decision layer based on TTC thresholds:

| TTC | Action | Hardware |
|-----|--------|----------|
| < 1.0s | EMERGENCY_BRAKE | GPIO relay (<0.5ms) |
| 1.0-2.0s | SERVICE_BRAKE | CAN brake command |
| 2.0-3.0s | WARNING | MQTT alert |
| 3.0-5.0s | CAUTION | Log only |
| > 5.0s | CLEAR | Normal operation |

**Budget:** 7 ms  
**Compliance:** ISO 26262 ASIL-D alignment

---

## Meta-Cognition Layer

| Component | Purpose |
|-----------|---------|
| **Federated Orchestration** | Multi-train fleet sync (UDP/MQTT) |
| **Safety Governance** | Audit trails, fail-safe/fail-op logic |
| **Privacy & Security** | GDPR compliance, on-chip anonymization |

All async, **no impact on real-time budget**.

---

## Object Categories

| Category | Representation | Data |
|----------|----------------|------|
| **PERSON** | SMPL Avatar | 72 pose + 10 shape params |
| **KNOWN OBJECT** | PLY Wireframe | Pre-computed from library |
| **UNKNOWN OBJECT** | bbox3D | Async PLY reconstruction |

All categories produce `bbox3D` for unified TTC calculation.

---

## Privacy Guarantees

- ✅ **No facial data stored** (SMPL avatars only)
- ✅ **No identifiable clothing** (geometric representation)
- ✅ **On-chip anonymization** (before any storage/transmission)
- ✅ **GDPR compliant** by design

---

## Dependencies

| Component | Library | License |
|-----------|---------|---------|
| Depth | DepthAnything-v2 | Apache 2.0 |
| Detection | RT-DETR-X | Apache 2.0 |
| Pose | RTMPose | Apache 2.0 |
| Avatar | SMPL | Academic |
| Tracking | BotSORT | MIT |
| ReID | OSNet | MIT |
| Runtime | TensorRT | NVIDIA |

---

## File Structure

```
IN3/
├── spec.md                          # This file
├── stac_caps_arquitectura.svg       # Main architecture diagram
├── stac_caps_flujo.svg              # Main flow diagram
│
└── blocks/
    ├── 2_cognitive_trinity/
    │   └── engines/
    │       ├── engine_1a_depth/     # spec.md, arquitectura.svg, flujo.svg
    │       ├── engine_1b_semantic/  # spec.md, arquitectura.svg, flujo.svg
    │       ├── engine_2_persistence/# spec.md, arquitectura.svg, flujo.svg
    │       └── engine_3_behavior/   # spec.md, arquitectura.svg, flujo.svg
    │
    ├── 3_fusion/                    # spec.md, arquitectura.svg, flujo.svg
    ├── 4_meta_cognition/            # spec.md, arquitectura.svg, flujo.svg
    └── 5_safety_envelope/           # spec.md, arquitectura.svg, flujo.svg
```

---

## Quick Reference

### Diagrams
- [Main Architecture](stac_caps_arquitectura.svg)
- [Main Flow](stac_caps_flujo.svg)

### Engine Details
- [Engine 1A: Depth](blocks/2_cognitive_trinity/engines/engine_1a_depth/spec.md)
- [Engine 1B: Semantic](blocks/2_cognitive_trinity/engines/engine_1b_semantic/spec.md)
- [Engine 2: Persistence](blocks/2_cognitive_trinity/engines/engine_2_persistence/spec.md)
- [Engine 3: Behavior](blocks/2_cognitive_trinity/engines/engine_3_behavior/spec.md)

### Other Blocks
- [3D Fusion](blocks/3_fusion/spec.md)
- [Meta-Cognition](blocks/4_meta_cognition/spec.md)
- [Safety Veto](blocks/5_safety_envelope/spec.md)

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 3.3 | 2025-12-18 | Technical fixes, Service Brake, coordinate docs |
| 3.2 | 2025-12-17 | Engine improvements, 3D Fusion, Layer 4 |
| 3.1 | 2025-12-16 | Object 3D classification |
| 3.0 | 2025-12-15 | Initial platform-ready version |

---

## Contact

Project: STAC-CAPS  
Organization: IN3  
Status: Platform-Ready (v3.3)
