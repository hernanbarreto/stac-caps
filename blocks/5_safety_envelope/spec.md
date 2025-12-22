# Block 5: Safety Envelope Specification

**Version:** 1.1  
**Updated:** 2025-12-22

---

## Overview

Final decision layer that evaluates TTC and risk to determine braking action. **Respects SystemMode** for fail-safe operation.

---

## Mode-Aware Behavior

### NOMINAL Mode
Full automatic braking enabled based on TTC thresholds.

| TTC | Risk | Action | Hardware |
|-----|------|--------|----------|
| < 1.0s | Any | EMERGENCY_BRAKE | GPIO relay (<0.5ms) |
| 1.0-2.0s | >0.7 | SERVICE_BRAKE | CAN brake command |
| 2.0-3.0s | Any | WARNING | MQTT alert + audio |
| 3.0-5.0s | Any | CAUTION | Log only |
| > 5.0s | <0.5 | CLEAR | Normal operation |

### DEGRADED Mode
**NO automatic braking**. Only visual/audio alerts.

| Situation | Action | Reason |
|-----------|--------|--------|
| TTC < 1.0s | WARNING | Urgent alert, NO brake |
| TTC 1.0-3.0s | CAUTION | Visual alert |
| Any detection | LOG | Record with P(miss) |

Output includes:
- `P_alert_correct` - Probability alert is valid
- `P_miss` - **Probability of missing real obstacle**
- `recommendation` - OPERATOR_VIGILANCE_REQUIRED

### FAULT Mode
Manual control only. System logs but takes no action.

---

## Decision Flow

```
Input: TTC, Risk, SystemMode
         │
         ▼
    ┌────────────┐
    │ Check Mode │
    └─────┬──────┘
          │
    ┌─────┴─────┐
    │           │
    ▼           ▼
 NOMINAL    DEGRADED/FAULT
    │           │
    ▼           ▼
 Full        Alert
 Decision    Only
    │           │
    ▼           ▼
 BRAKE?     WARNING
```

---

## Timing Budget

| Component | Time |
|-----------|------|
| TTC evaluation | 1ms |
| Risk aggregation | 1ms |
| Mode check | <0.5ms |
| Decision logic | 2ms |
| GPIO trigger | <0.5ms |
| Output formatting | 2ms |
| **Total** | **7ms** |

---

## Files

| File | Description |
|------|-------------|
| `safety.py` | SafetyVeto class (mode-aware) |
| `interfaces.py` | Action enum |
| `config.py` | Thresholds |
| `evaluator/ttc.py` | TTC evaluation |
| `aggregator/risk.py` | Risk aggregation |
| `decision/engine.py` | Decision logic |
| `hardware/gpio.py` | Brake trigger |
| `audit/logger.py` | Decision logging |

---

## Compliance

- ISO 26262 ASIL-D alignment
- Fail-safe design (DEGRADED mode)
- Auditable decision trail
