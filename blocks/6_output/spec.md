# Layer 6: Output Interface - Technical Specification

## Overview

Layer 6 is the **output interface layer** that delivers STAC-CAPS decisions to external systems. It handles multiple communication protocols and ensures safety-critical messages are delivered with minimal latency.

---

## Key Features

| Feature | Description |
|---------|-------------|
| **Multi-Protocol** | CAN, SCADA, MQTT, REST |
| **Priority Routing** | Critical messages first |
| **Redundant Channels** | Fallback communication paths |
| **Audit Trail** | All outputs logged |

---

## Output Channels

### 1. CAN Bus (Safety Critical)

| Property | Value |
|----------|-------|
| Purpose | Brake commands to train control |
| Messages | EMERGENCY_BRAKE, SERVICE_BRAKE |
| Latency | <1 ms |
| Interface | CAN 2.0B, 500 kbps |
| Priority | HIGHEST |

```python
@dataclass
class CANBrakeMessage:
    message_id: int = 0x100       # Priority ID
    command: BrakeCommand         # EMERGENCY | SERVICE | RELEASE
    intensity: float              # 0.0-1.0
    ttc_ms: int                   # Time-to-collision
    timestamp: int                # Microseconds
```

### 2. SCADA Integration

| Property | Value |
|----------|-------|
| Purpose | Operations Control Center |
| Protocol | Modbus TCP / OPC-UA |
| Data | System status, alerts, telemetry |
| Latency | <100 ms |

### 3. MQTT Pub/Sub

| Property | Value |
|----------|-------|
| Purpose | Fleet-wide messaging |
| Broker | Local + Cloud |
| Topics | alerts/, telemetry/, commands/ |
| QoS | Level 2 (exactly once) |

```
MQTT Topics:
├── stac/train/{id}/alerts        # Safety alerts
├── stac/train/{id}/telemetry     # Real-time data
├── stac/train/{id}/status        # System health
└── stac/fleet/sync               # Federated updates
```

### 4. REST API

| Property | Value |
|----------|-------|
| Purpose | Configuration, diagnostics |
| Protocol | HTTP/2 + TLS 1.3 |
| Port | 8443 |
| Use Case | Remote config, log retrieval |

---

## Output Messages

### Safety Decision Message

```python
@dataclass
class SafetyDecision:
    timestamp: float              # Time of decision
    action: SafetyAction          # CLEAR | CAUTION | WARNING | SERVICE_BRAKE | EMERGENCY_BRAKE
    ttc_min: float                # Minimum TTC (seconds)
    ttc_confidence: float         # Confidence [0.0, 1.0]
    risk_score: float             # Aggregate risk [0.0, 1.0]
    target_id: Optional[int]      # Track ID of threat
    target_distance: float        # Distance (meters)
    validation_status: str        # OK | PENDING | CONFLICT
```

### Telemetry Packet

```python
@dataclass
class TelemetryPacket:
    timestamp: float
    frame_id: int
    active_tracks: int            # Number of tracked objects
    avg_ttc: float                # Average TTC
    system_fps: float             # Processing rate
    health_status: str            # OK | DEGRADED | FAULT
    gpu_temp: float               # Hardware temp
    latency_ms: float             # Pipeline latency
```

---

## Message Priority

| Priority | Action | Channel | Max Latency |
|----------|--------|---------|-------------|
| **P0** | EMERGENCY_BRAKE | CAN + GPIO | <0.5 ms |
| **P1** | SERVICE_BRAKE | CAN | <1 ms |
| **P2** | WARNING | MQTT + SCADA | <10 ms |
| **P3** | CAUTION | MQTT | <50 ms |
| **P4** | Telemetry | MQTT | <100 ms |
| **P5** | Logs | File + MQTT | Best effort |

---

## Processing Flow

```
┌─────────────────────────────────────────────────────────┐
│                    OUTPUT MANAGER                        │
├─────────────────────────────────────────────────────────┤
│                                                          │
│   Safety Decision ──┬──► CAN Encoder ──► CAN Bus        │
│         │           │                                    │
│         │           ├──► GPIO Controller ──► Relay      │
│         │           │                                    │
│         ▼           └──► SCADA Encoder ──► OPC-UA       │
│   Priority Queue                                         │
│         │                                                │
│         ▼                                                │
│   MQTT Publisher ──────────────────────► Broker         │
│         │                                                │
│         ▼                                                │
│   Audit Logger ────────────────────────► File + Cloud   │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

---

## Redundancy

### Primary/Fallback Channels

| Message Type | Primary | Fallback |
|--------------|---------|----------|
| EMERGENCY_BRAKE | CAN + GPIO | GPIO only |
| SERVICE_BRAKE | CAN | SCADA |
| WARNING | MQTT | SCADA |
| Telemetry | MQTT | Local file |

### Failure Handling

```python
def send_safety_decision(decision, channels):
    """Send with redundancy and fallback."""
    
    # Critical: always use hardwire GPIO for emergency
    if decision.action == 'EMERGENCY_BRAKE':
        gpio_brake_trigger()  # Hardware bypass
    
    # Try primary channel
    for channel in channels.primary:
        try:
            channel.send(decision)
            audit_log(decision, channel, 'SUCCESS')
            return True
        except ChannelError as e:
            audit_log(decision, channel, 'FAILED', e)
    
    # Fallback channels
    for channel in channels.fallback:
        try:
            channel.send(decision)
            audit_log(decision, channel, 'FALLBACK_SUCCESS')
            return True
        except ChannelError as e:
            audit_log(decision, channel, 'FALLBACK_FAILED', e)
    
    # Critical failure
    system_alert('ALL_CHANNELS_FAILED')
    return False
```

---

## Timing Budget

| Operation | Latency |
|-----------|---------|
| Message serialization | <0.5 ms |
| CAN transmission | <1 ms |
| MQTT publish | ~5 ms |
| Audit logging | <1 ms (async) |
| **Total Layer 6** | **~5 ms** |

---

## Configuration

```python
OUTPUT_PARAMS = {
    'can': {
        'interface': 'can0',
        'bitrate': 500000,
        'brake_message_id': 0x100,
        'timeout_ms': 10
    },
    'mqtt': {
        'broker': 'localhost',
        'port': 8883,
        'tls_enabled': True,
        'qos': 2,
        'topics': {
            'alerts': 'stac/train/{train_id}/alerts',
            'telemetry': 'stac/train/{train_id}/telemetry'
        }
    },
    'scada': {
        'protocol': 'opcua',
        'endpoint': 'opc.tcp://localhost:4840',
        'namespace': 'STAC-CAPS'
    },
    'audit': {
        'log_path': '/var/log/stac/audit/',
        'format': 'json',
        'sign_entries': True
    }
}
```

---

## Security

| Aspect | Implementation |
|--------|----------------|
| Authentication | mTLS (mutual TLS) |
| Encryption | TLS 1.3 (MQTT, SCADA) |
| CAN Security | ISO 15765 signed frames |
| Audit Integrity | Cryptographic signatures |
| Access Control | Role-based (RBAC) |

---

## Integration

```
Safety Veto (Layer 5)
        │
        ▼
   Layer 6: Output
        │
        ├──► CAN Bus ──► Train Control Unit
        ├──► GPIO ──► Emergency Relay
        ├──► SCADA ──► Operations Center
        ├──► MQTT ──► Fleet Manager / Cloud
        └──► File ──► Audit Storage
```

---

## Files

| File | Purpose |
|------|---------|
| [arquitectura.svg](arquitectura.svg) | Component structure |
| [flujo.svg](flujo.svg) | Output routing flow |
| `spec.md` | This document |
