# STAC-CAPS: Spatial-Temporal Awareness & Collision Avoidance Perception System

**Version:** 3.4 (Production-Ready)  
**Date:** 2025-12-22  
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
| **Degraded Mode** | Fail-safe when calibration uncertain |
| **Privacy by Design** | SMPL avatars, no facial data stored |
| **Federated Learning** | Multi-train fleet coordination |

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        STAC-CAPS v3.4                               │
├─────────────────────────────────────────────────────────────────────┤
│  0. SENSOR INPUT          │ Monocular RGB (IMX490 HDR)              │
│  1. CALIBRATION           │ Rail geometry + Landmarks + MODE        │
│  2. COGNITIVE TRINITY     │ Engines 1A/1B/2/3 (PARALLEL)            │
│  3. 3D FUSION             │ Depth + Semantic → 3D Scene             │
│  4. META-COGNITION        │ Fleet sync, Governance, Privacy         │
│  5. SAFETY VETO           │ TTC-based decision, respects MODE       │
│  6. OUTPUT                │ CAN/SCADA/MQTT                          │
└─────────────────────────────────────────────────────────────────────┘
```

---

## ⚠️ Timing Architecture (CRITICAL)

### Latency vs Throughput

> [!IMPORTANT]
> STAC-CAPS uses **pipelined execution**. The system achieves **50ms throughput** (20 FPS) 
> despite **~75ms end-to-end latency** per individual frame.

```
PIPELINING DIAGRAM:

Time (ms):    0    25    50    75   100   125   150
              │     │     │     │     │     │     │
Frame N:      [CAP][===1A+1B===][FUS][E2][E3][SAF]
Frame N+1:          [CAP][===1A+1B===][FUS][E2][E3][SAF]
Frame N+2:                [CAP][===1A+1B===][FUS][E2][E3][SAF]
              │     │     │     │     │     │     │
              ├─────┼─────┼─────┼─────┼─────┼─────┤
              │  Throughput = 50ms per frame = 20 FPS  │
              │    Latency = 75ms first response       │
```

### Timing Budget (Per Frame)

| Stage | Component | Timing | Execution |
|-------|-----------|--------|-----------|
| 1 | Frame Capture + ISP | 5 ms | sync |
| 2 | Engine 1A: Depth | 22 ms | **PARALLEL** ↓ |
| 2 | Engine 1B: Semantic | 25 ms | **PARALLEL** ↑ |
| 3 | 3D Fusion | 3 ms | sync |
| 4 | Engine 2: Tracking | 5 ms | sync |
| 5 | Engine 3: Behavior + TTC | 5 ms | sync |
| 6 | Safety Decision + Output | 7 ms | sync |
| | **End-to-End Latency** | **~72 ms** | |
| | **Throughput (pipelined)** | **50 ms = 20 FPS** | ✅ |

### Latency Guarantees

| Metric | Target | Measurement |
|--------|--------|-------------|
| Throughput | 50ms (20 FPS) | Pipelined |
| End-to-End Latency | <100ms | First response |
| P99 Latency | <120ms | 99th percentile |
| Jitter | <10ms | Frame-to-frame variance |

---

## System Modes (Fail-Safe Design)

> [!CAUTION]
> When calibration confidence is low, the system enters **Degraded Mode** to prevent 
> false measurements. This is a safety feature, not a failure.

### Mode Definitions

| Mode | Condition | Behavior | Automatic Braking |
|------|-----------|----------|-------------------|
| **NOMINAL** | Calibración >80% confianza | Métricas precisas, TTC calculado | ✅ Habilitado |
| **DEGRADED** | Calibración 40-80% | Solo alertas visuales + probabilidades | ❌ Deshabilitado |
| **FAULT** | Calibración <40% o error | Alerta operador, frenado manual | ❌ Manual only |

### Degraded Mode Details

En modo degradado, el sistema reporta:

| Indicador | Descripción |
|-----------|-------------|
| `P(alert)` | Probabilidad de que la alerta sea correcta |
| `P(miss)` | **Probabilidad de NO detectar obstáculo real** (crítico) |
| `confidence_score` | Confianza general del frame |
| `degraded_reason` | Causa: "TUNNEL", "SWITCH", "OCCLUSION", "LOW_CONTRAST" |

```json
{
  "mode": "DEGRADED",
  "degraded_reason": "TUNNEL_DARK",
  "confidence_score": 0.55,
  "P_alert_correct": 0.72,
  "P_miss": 0.15,
  "recommendation": "OPERATOR_VIGILANCE_REQUIRED"
}
```

### Mode Transition Triggers

| Trigger | From → To | Automatic |
|---------|-----------|-----------|
| Rieles no visibles >2s | NOMINAL → DEGRADED | ✅ |
| Calibración recuperada | DEGRADED → NOMINAL | ✅ |
| Error sensor/modelo | Any → FAULT | ✅ |
| Override operador | Any → Any | Manual |

---

## Cognitive Trinity (Engines)

### Engine 1A: Depth
- **Model:** DepthAnything-v2 (ViT-B, TensorRT FP16)
- **Output:** Metric depth map + point cloud + confidence
- **Features:** Refinement pipeline (outlier, guided filter, EMA)
- **Budget:** 22 ms

### Engine 1B: Semantic
- **Model:** RT-DETR-X (transformer detector)
- **Output:** 3-category detections with 3D representation
  - **Personas:** SMPL Avatar (6890 vertices)
  - **Objetos Conocidos:** PLY wireframe from library
  - **Objetos Desconocidos:** bbox3D only
- **Budget:** 25 ms

### Engine 2: Persistence
- **Model:** BotSORT + OSNet-x0.25 (ReID)
- **Output:** Stable track IDs, velocity, quality scores
- **Features:** LRU cache (50 tracks), adaptive Kalman, EMA embeddings
- **Budget:** 5 ms

### Engine 3: Behavior
- **Model:** Kinematic prediction + Theory of Mind (Bayesian)
- **Output:** Trajectories, TTC with confidence intervals, risk scores
- **Features:** Cross-validation with optical flow, early exit
- **Budget:** 5 ms (includes TTC)

---

## Performance Metrics (Targets)

> [!NOTE]
> Métricas target. Validación pendiente con datasets operacionales.

### Per-Engine Metrics

| Engine | Metric | Target | Status |
|--------|--------|--------|--------|
| 1A Depth | AbsRel error | < 0.10 | 🔲 Pendiente |
| 1A Depth | δ₁ accuracy (1.25) | > 0.95 | 🔲 Pendiente |
| 1B Detection | mAP@50 | > 0.85 | 🔲 Pendiente |
| 1B Detection | Recall@10m | > 0.95 | 🔲 Pendiente |
| 2 Tracking | IDF1 | > 0.80 | 🔲 Pendiente |
| 2 Tracking | HOTA | > 0.70 | 🔲 Pendiente |
| 3 TTC | RMSE vs LiDAR | < 0.3s | 🔲 Pendiente |

### Safety Metrics (Critical)

| Metric | Target | Consequence if Failed |
|--------|--------|----------------------|
| **False Negative Rate** | < 0.001 | Colisión no evitada |
| **False Positive Rate** | < 0.01 | Frenado innecesario |
| **Detection Latency** | < 100ms | Respuesta tardía |
| **Mode Transition Time** | < 500ms | Comportamiento incierto |

---

## Operational Limits

> [!WARNING]
> Condiciones donde el sistema puede entrar en modo degradado.

| Condition | Impact | System Response |
|-----------|--------|-----------------|
| **Lluvia ligera** | Contraste reducido | NOMINAL (HDR compensa) |
| **Lluvia fuerte** | Visibilidad <50m | DEGRADED + P(miss) elevado |
| **Nieve leve** | Contraste OK | NOMINAL |
| **Nieve fuerte** | Rieles ocultos | DEGRADED |
| **Niebla densa** | Visibilidad <30m | DEGRADED |
| **Iluminación <50 lux** | HDR compensa | NOMINAL |
| **Oscuridad total** | Sin visión | FAULT |
| **Túnel oscuro** | Sin rieles visibles | DEGRADED (auto) |
| **Cambio de vías/desvío** | Geometría compleja | DEGRADED temporal |
| **Curva cerrada >15°** | Calibración incierta | DEGRADED |
| **Vibración alta** | Blur temporal | NOMINAL (EMA compensa) |
| **Obstrucción cámara** | Sin imagen | FAULT |

---

## Safety Veto (Block 5)

Final decision layer respecting system mode:

### In NOMINAL Mode

| TTC | Risk | Action | Hardware |
|-----|------|--------|----------|
| < 1.0s | Any | EMERGENCY_BRAKE | GPIO relay (<0.5ms) |
| 1.0-2.0s | >0.7 | SERVICE_BRAKE | CAN brake command |
| 2.0-3.0s | Any | WARNING | MQTT alert + audio |
| 3.0-5.0s | Any | CAUTION | Log only |
| > 5.0s | <0.5 | CLEAR | Normal operation |

### In DEGRADED Mode

| Situation | Action | Reason |
|-----------|--------|--------|
| Cualquier detección | VISUAL_ALERT | No confianza para frenar |
| (sin detección) | LOG + P(miss) | Operador debe vigilar |
| TTC < 1.0s estimado | AUDIO_WARNING | Alerta urgente sin frenado |

**Budget:** 7 ms  
**Compliance:** ISO 26262 ASIL-D alignment

---

## Hardware Targets

| Platform | Status | Optimization | FPS |
|----------|--------|--------------|-----|
| RTX 3060 (6GB) | ✅ Desarrollo | PyTorch + ONNX | ~15 |
| RTX 3060 (6GB) | ✅ Producción | TensorRT FP16 | ~22 |
| RTX 3090 (24GB) | ✅ Tested | TensorRT FP16 | ~35 |
| Jetson AGX Orin | 🔲 Roadmap | TensorRT INT8 + DLA | ~18 |
| Hailo-8 | 🔲 Research | Modelos específicos | TBD |

### Optimization Roadmap

- [x] ONNX export para portabilidad
- [x] TensorRT FP16 para RTX
- [ ] INT8 quantization para Edge
- [ ] Multi-stream inference
- [ ] DLA acceleration (Jetson)

---

## Async Operations (Non-Blocking)

> [!IMPORTANT]
> Todas las operaciones async son **fire-and-forget** y NO impactan el timing del frame.

| Operation | Latency | Thread | Blocking |
|-----------|---------|--------|----------|
| Unknown object → PLY server | 5-30s | Background | ❌ No |
| Fleet sync UDP | ~10ms | Background | ❌ No |
| Audit log write | ~5ms | Async queue | ❌ No |
| MQTT publish | ~50ms | Background | ❌ No |

Implementación:
```python
# Fire-and-forget pattern
executor.submit(send_to_ply_server, data)  # Returns immediately
```

---

## Privacy Guarantees

- ✅ **No facial data stored** (SMPL avatars only)
- ✅ **No identifiable clothing** (geometric representation)
- ✅ **On-chip anonymization** (before any storage/transmission)
- ✅ **GDPR compliant** by design

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 3.4 | 2025-12-22 | Pipelining docs, Degraded Mode, Metrics placeholder, Operational limits |
| 3.3 | 2025-12-18 | Technical fixes, Service Brake, coordinate docs |
| 3.2 | 2025-12-17 | Engine improvements, 3D Fusion, Layer 4 |
| 3.1 | 2025-12-16 | Object 3D classification |
| 3.0 | 2025-12-15 | Initial platform-ready version |

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
- [Calibration](blocks/1_calibration/spec.md)
- [3D Fusion](blocks/3_fusion/spec.md)
- [Meta-Cognition](blocks/4_meta_cognition/spec.md)
- [Safety Veto](blocks/5_safety_envelope/spec.md)

---

## Contact

Project: STAC-CAPS  
Organization: IN3  
Status: Production-Ready (v3.4)
