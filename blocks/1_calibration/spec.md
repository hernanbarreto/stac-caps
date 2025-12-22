# Block 1: Calibration Specification

**Version:** 1.1  
**Updated:** 2025-12-22

---

## Overview

Adaptive calibration system that computes metric scale from rail geometry and manages system mode transitions for fail-safe operation.

---

## System Modes

| Mode | Condition | Calibration Confidence | Braking |
|------|-----------|------------------------|---------|
| **NOMINAL** | Rails visible, stable geometry | > 80% | ✅ Auto |
| **DEGRADED** | Partial visibility, uncertain | 40-80% | ❌ Alert only |
| **FAULT** | No visibility, error | < 40% | ❌ Manual |

### Mode Transition Triggers

| Trigger | Transition | Time |
|---------|------------|------|
| Rails not visible >2s | NOMINAL → DEGRADED | Automatic |
| Confidence drops <40% | DEGRADED → FAULT | Automatic |
| Calibration recovered >3s | DEGRADED → NOMINAL | Automatic |
| Sensor/model error | Any → FAULT | Immediate |
| Operator override | Any → Any | Manual |

---

## Degraded Mode Output

En modo degradado, el sistema reporta probabilidades críticas:

```json
{
  "mode": "DEGRADED",
  "confidence_score": 0.55,
  "degraded_reason": "TUNNEL_DARK",
  "P_alert_correct": 0.72,
  "P_miss": 0.15,
  "recommendation": "OPERATOR_VIGILANCE_REQUIRED"
}
```

| Indicador | Descripción | Rango |
|-----------|-------------|-------|
| `P_alert_correct` | Probabilidad de alerta correcta | 0.5-0.9 |
| `P_miss` | **Probabilidad de NO detectar obstáculo** | 0.05-0.40 |
| `degraded_reason` | Causa del modo degradado | enum |
| `recommendation` | Acción sugerida para operador | string |

---

## Calibration Methods

### Primary: Rail Geometry
- 2 points per rail + track gauge
- Works for straight and slight curves (<5°)
- Error: ±2% in optimal conditions

### Fallback: SuperPoint Landmarks
- When rails not visible
- Higher error: ±15-25%
- Triggers DEGRADED mode automatically

---

## Operational Limits

| Condition | Behavior | Notes |
|-----------|----------|-------|
| **Rieles rectos** | ✅ NOMINAL | Óptimo |
| **Curvas leves (<5°)** | ✅ NOMINAL | Error ±5% |
| **Curvas medias (5-15°)** | ⚠️ DEGRADED | Calibration drift |
| **Curvas cerradas (>15°)** | ❌ DEGRADED | No confiable |
| **Desvíos/cambios** | ⚠️ DEGRADED | Geometría compleja |
| **Túneles oscuros** | ⚠️ DEGRADED | Rails no visibles |
| **Oclusión >50%** | ⚠️ DEGRADED | Información parcial |
| **Vibración alta** | ✅ NOMINAL | EMA compensa |

---

## Files

| File | Description |
|------|-------------|
| `calibrator.py` | CalibrationManager class |
| `degraded_mode.py` | SystemMode, ModeStatus, DegradedModeDetector |
| `interfaces.py` | CalibrationResult dataclass |
| `config.py` | Thresholds and parameters |
| `initialization/hard_init.py` | Initial calibration |
| `landmarks/database.py` | Landmark DB for fallback |
| `fallback/occlusion.py` | Occlusion handling |

---

## Timing

| Operation | Time |
|-----------|------|
| Initial calibration | 50-100ms |
| Per-frame update | <2ms |
| Mode transition | <10ms |

---

## Traceability

See [traceability.md](traceability.md) for SVG mapping.
