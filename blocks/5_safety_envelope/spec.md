# Safety Veto - Technical Specification

## Overview

Safety Veto is the **final decision layer** in STAC-CAPS that determines the appropriate action based on collision risk analysis. It implements a fail-safe architecture with three decision paths: Emergency Brake, Warning, and Clear.

---

## Key Features

| Feature | Description |
|---------|-------------|
| **TTC-based Decision** | Primary decision from Time-To-Collision |
| **Risk Aggregation** | Consider all track risk scores |
| **Validation Check** | Handle UNCERTAIN predictions conservatively |
| **Hardwire Brake** | Direct GPIO relay bypass for emergencies |
| **ISO 26262 Aligned** | ASIL-D hooks for certification |

---

## Inputs

| Input | Type | Source |
|-------|------|--------|
| `ttc_result` | TTCResult | Engine 3 |
| `risk_scores` | Dict[tid → float] | Engine 3 |
| `predictions` | List[Prediction] | Engine 3 |
| `safety_margin` | float | Engine 3 |
| `validation_status` | str | Engine 3 |
| `train_state` | TrainState | Vehicle dynamics |

### TTCResult Structure
```python
@dataclass
class TTCResult:
    min: float          # Conservative (worst case)
    mean: float         # Average case
    max: float          # Optimistic case
    confidence: float   # [0.3, 1.0]
```

---

## Outputs

| Output | Type | Description |
|--------|------|-------------|
| `action` | Action | BRAKE / WARNING / CLEAR |
| `brake_command` | BrakeCmd | Force, type |
| `alert_level` | int | 0-3 severity |
| `audit_log` | AuditEntry | For traceability |

### Action Enum
```python
class Action(Enum):
    EMERGENCY_BRAKE = 'EMERGENCY'    # Direct GPIO
    SERVICE_BRAKE = 'SERVICE'        # Normal brake
    WARNING = 'WARNING'              # Alert only
    CAUTION = 'CAUTION'              # Monitor
    CLEAR = 'CLEAR'                  # Normal operation
```

---

## Decision Logic

### Primary Decision Tree

```
INPUT: ttc_result, risk_scores, validation_status
                    |
         ┌──────────┴──────────┐
         │ validation_status   │
         │ == UNCERTAIN?       │
         └──────────┬──────────┘
                    │
         ┌──────────┴──────────┐
    Yes  │                     │ No
         ▼                     ▼
    Use TTC.min           Use TTC.mean
    (Conservative)         (Nominal)
         │                     │
         └─────────┬───────────┘
                   ▼
         ┌─────────────────────┐
         │  TTC < 1.0s?        │─── Yes ──► EMERGENCY BRAKE
         └─────────┬───────────┘
                   │ No
                   ▼
         ┌─────────────────────┐
         │  TTC < 3.0s?        │─── Yes ──► WARNING + PREPARE
         └─────────┬───────────┘
                   │ No
                   ▼
         ┌─────────────────────┐
         │  TTC < 5.0s?        │─── Yes ──► CAUTION
         └─────────┬───────────┘
                   │ No
                   ▼
                 CLEAR
```

### TTC Thresholds

| TTC | Level | Action | Hardware |
|-----|-------|--------|----------|
| < 1.0s | RED | EMERGENCY_BRAKE | GPIO relay |
| 1.0-2.0s | **DARK ORANGE** | **SERVICE_BRAKE** | **CAN brake cmd** |
| 2.0-3.0s | ORANGE | WARNING | MQTT alert |
| 3.0-5.0s | YELLOW | CAUTION | Log only |
| > 5.0s | GREEN | CLEAR | Normal |

> **Nota:** SERVICE_BRAKE se activa solo si además `max_risk > 0.8`. Ver `decide_action()` para la lógica completa.

---

## Components

### 1. TTC Evaluator
| Property | Value |
|----------|-------|
| Input | TTCResult (min, mean, max, confidence) |
| Strategy | Use min if uncertain, mean otherwise |
| Latency | **<1 ms** |

```python
def evaluate_ttc(ttc_result, validation_status):
    """Select appropriate TTC value based on confidence."""
    
    if validation_status == 'UNCERTAIN':
        # Conservative: use worst case
        effective_ttc = ttc_result.min
        confidence = 0.5  # Reduce confidence
    elif ttc_result.confidence < 0.7:
        # Low confidence: use min
        effective_ttc = ttc_result.min
        confidence = ttc_result.confidence
    else:
        # Normal: use mean
        effective_ttc = ttc_result.mean
        confidence = ttc_result.confidence
    
    return effective_ttc, confidence
```

### 2. Risk Aggregator
| Property | Value |
|----------|-------|
| Input | risk_scores{tid → float} |
| Output | max_risk, critical_count |
| Latency | **<1 ms** |

```python
def aggregate_risk(risk_scores):
    """Aggregate risk across all tracks."""
    
    if not risk_scores:
        return 0.0, 0
    
    max_risk = max(risk_scores.values())
    critical_count = sum(1 for r in risk_scores.values() if r > 0.8)
    
    return max_risk, critical_count
```

### 3. Decision Engine
| Property | Value |
|----------|-------|
| Input | effective_ttc, max_risk, critical_count |
| Output | Action |
| Latency | **<1 ms** |

```python
def decide_action(effective_ttc, max_risk, critical_count, validation_status):
    """Determine action based on inputs."""
    
    # EMERGENCY: TTC < 1.0s or multiple critical
    if effective_ttc < 1.0 or critical_count >= 3:
        return Action.EMERGENCY_BRAKE
    
    # SERVICE BRAKE: TTC < 2.0s with high risk
    if effective_ttc < 2.0 and max_risk > 0.8:
        return Action.SERVICE_BRAKE
    
    # WARNING: TTC < 3.0s
    if effective_ttc < 3.0:
        return Action.WARNING
    
    # CAUTION: TTC < 5.0s or uncertain
    if effective_ttc < 5.0 or validation_status == 'UNCERTAIN':
        return Action.CAUTION
    
    # CLEAR
    return Action.CLEAR
```

### 4. Hardwire Controller
| Property | Value |
|----------|-------|
| Purpose | Direct GPIO for emergency |
| Bypass | Software stack bypass |
| Latency | **<0.5 ms** |

```python
def execute_hardwire_brake():
    """Direct hardware brake via GPIO."""
    
    GPIO.output(BRAKE_RELAY_PIN, GPIO.HIGH)
    
    # Log for audit
    log_emergency_brake(timestamp=time.time())
    
    # Signal to main controller
    send_brake_confirmation()
```

### 5. Audit Logger
| Property | Value |
|----------|-------|
| Purpose | Traceability for ISO 26262 |
| Output | Secure log entry |
| Latency | **async** |

```python
@dataclass
class AuditEntry:
    timestamp: float
    ttc_result: TTCResult
    action: Action
    risk_scores: Dict
    validation_status: str
    decision_rationale: str
    
def log_decision(entry: AuditEntry):
    """Log decision for audit trail."""
    
    # Append to secure log
    audit_log.append(entry)
    
    # If critical, send to external monitor
    if entry.action in [Action.EMERGENCY_BRAKE, Action.SERVICE_BRAKE]:
        send_to_monitoring(entry)
```

---

## Processing Flow

```
1. RECEIVE inputs from Engine 3
           ↓
2. EVALUATE TTC (select min/mean based on confidence)
           ↓
3. AGGREGATE risk scores
           ↓
4. DECIDE action
           ↓
5. IF EMERGENCY:
   └── EXECUTE hardwire brake (GPIO)
           ↓
6. EMIT alert/command
           ↓
7. LOG audit entry (async)
           ↓
8. OUTPUT → SCADA / CAN Bus
```

---

## Timing Budget

```
TTC Evaluation:      <1 ms
Risk Aggregation:    <1 ms
Decision:            <1 ms
Hardwire (if needed): <0.5 ms
Alert Emit:          <1 ms
Audit Log:           async

TOTAL:               7 ms (sync path)
```

---

## Fail-Safe Modes

| Condition | Response |
|-----------|----------|
| Engine 3 timeout | Use last known TTC, conservative |
| TTC = infinity | Assume sensor failure, CAUTION |
| All tracks lost | Check continuity, SERVICE_BRAKE if sudden |
| GPIO failure | Fallback to software brake |
| Validation UNCERTAIN | Use TTC.min (conservative) |

---

## Hardware Interface

```
OUTPUT SIGNALS:
├── GPIO_BRAKE_RELAY   →  Emergency brake
├── CAN_BRAKE_CMD      →  Service brake (0-100%)
├── MQTT_ALERT_FLAG    →  Alert to operator
└── UART_AUDIT_LOG     →  Traceability log
```

---

## Integration with Other Blocks

```
Engine 3 ─────► Safety Veto ─────► SCADA/CAN
                    │
                    ├──► GPIO (Emergency)
                    │
                    └──► Audit Log
```

---

## ISO 26262 Alignment

| Requirement | Implementation |
|-------------|----------------|
| ASIL-D | Hardwire bypass for emergency |
| Fault Tolerance | Dual-path decision |
| Traceability | Complete audit log |
| Response Time | <7ms guaranteed |
| Fail-Safe | Default to brake on failure |

---

## Error Handling

| Condition | Action |
|-----------|--------|
| Missing ttc_result | Emergency stop |
| Empty risk_scores | Use TTC only |
| Invalid validation_status | Assume UNCERTAIN |
| GPIO write failure | Retry + software fallback |
| Audit log full | Rotate, continue operation |

---

## System Limits

```python
SAFETY_PARAMS = {
    'emergency_ttc': 1.0,          # seconds
    'warning_ttc': 3.0,            # seconds
    'caution_ttc': 5.0,            # seconds
    'critical_risk_threshold': 0.8,
    'critical_count_threshold': 3,
    'gpio_timeout_ms': 0.5,
    'max_response_time_ms': 7.0
}
```

---

## Files

| File | Purpose |
|------|---------|
| [arquitectura.svg](arquitectura.svg) | Component structure |
| [flujo.svg](flujo.svg) | Decision flow |
| `spec.md` | This document |
