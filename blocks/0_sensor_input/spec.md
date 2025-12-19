# Layer 0: Sensor Input - Technical Specification

## Overview

Layer 0 defines the **hardware sensor interface** for STAC-CAPS. The system operates with monocular RGB cameras only (no LiDAR/Radar), requiring robust image quality management and health monitoring.

---

## Key Features

| Feature | Description |
|---------|-------------|
| **Monocular Only** | Single camera depth inference |
| **HDR Capture** | 120dB dynamic range for tunnels/sun |
| **Dual Feed Option** | Primary + telephoto for long range |
| **Health Monitoring** | Continuous sensor quality checks |
| **ISP Pipeline** | On-chip image preprocessing |

---

## Hardware Components

### 1. Primary Optical Feed

| Property | Value |
|----------|-------|
| Sensor | Sony IMX490 (CMOS) |
| Resolution | 1920×1080 @ 60fps |
| HDR | 120dB dynamic range |
| Interface | GMSL2 / Ethernet |
| Lens | Wide angle (90° FoV) |

```
Specifications:
├── Effective Pixels: 2.95 MP (2880×1860)
├── Output Mode: 1080p60 HDR
├── Sensitivity: 3200 mV/lux·s
├── Operating Temp: -40°C to +85°C
└── Power: 1.5W typical
```

### 2. Secondary Optical Feed (Optional)

| Property | Value |
|----------|-------|
| Purpose | Long-range detection (>200m) |
| Lens | Telephoto (15° FoV) |
| Resolution | 1080p @ 30fps |
| Use Case | Early obstacle detection |

### 3. Hardware Health Monitor

| Property | Value |
|----------|-------|
| Thermal Check | GPU/Camera temp monitoring |
| Voltage Watch | Rail voltage stability |
| FPS Jitter | Frame timing analysis (<5ms) |
| Lens Health | Dirt/fog/blockage detection |

---

## ISP Pipeline

The Image Signal Processor runs on-camera before data reaches the GPU:

```
RAW BAYER
    │
    ▼
┌───────────────────────────┐
│ 1. DEMOSAIC               │ Bayer → RGB
├───────────────────────────┤
│ 2. DENOISE                │ Temporal + Spatial
├───────────────────────────┤
│ 3. HDR TONE MAPPING       │ 120dB → 8-bit output
├───────────────────────────┤
│ 4. WHITE BALANCE          │ Auto AWB
├───────────────────────────┤
│ 5. GAMMA CORRECTION       │ sRGB curve
└───────────────────────────┘
    │
    ▼
RGB FRAME → GPU Memory
```

---

## Outputs

| Output | Type | Destination |
|--------|------|-------------|
| `frame` | Tensor[1080×1920×3] | Pre-process |
| `frame_metadata` | Dict | Timing, exposure, temp |
| `health_status` | Enum | OK / DEGRADED / FAULT |

### Frame Metadata Structure
```python
@dataclass
class FrameMetadata:
    timestamp: float        # Capture time (µs precision)
    frame_id: int           # Sequential counter
    exposure_ms: float      # Current exposure
    gain_db: float          # Current gain
    temperature_c: float    # Sensor temperature
    hdr_enabled: bool       # HDR mode active
```

---

## Health States

| State | Condition | Action |
|-------|-----------|--------|
| **OK** | All parameters normal | Continue |
| **DEGRADED** | Minor issues (fog, temp warning) | Log + Alert |
| **FAULT** | Critical failure (no signal, lens blocked) | Emergency mode |

### Health Check Logic
```python
def check_sensor_health(metadata, prev_frames):
    """Continuous sensor health monitoring."""
    
    issues = []
    
    # Temperature check
    if metadata.temperature_c > 80:
        issues.append('THERMAL_WARNING')
    
    # FPS jitter check
    frame_delta = metadata.timestamp - prev_frames[-1].timestamp
    if abs(frame_delta - EXPECTED_DELTA) > 5.0:  # >5ms jitter
        issues.append('FPS_JITTER')
    
    # Lens blockage check (based on image statistics)
    if is_uniformly_dark(current_frame):
        issues.append('LENS_BLOCKED')
    
    if 'LENS_BLOCKED' in issues or 'NO_SIGNAL' in issues:
        return HealthState.FAULT
    elif issues:
        return HealthState.DEGRADED
    return HealthState.OK
```

---

## Timing Budget

```
Camera Capture:       16.67 ms (60 fps)
ISP Processing:       ~0 ms (on-chip, parallel)
DMA Transfer:         ~2 ms (to GPU memory)
Health Check:         <1 ms

EFFECTIVE LATENCY:    16 ms per frame
```

---

## Failure Modes

| Failure | Detection | Response |
|---------|-----------|----------|
| Camera disconnect | No signal | FAULT → Emergency stop |
| Lens obstruction | Uniform dark | FAULT → Alert operator |
| Thermal shutdown | Temp > 85°C | DEGRADED → Reduce FPS |
| GMSL2 link error | CRC failures | Retry → FAULT if persistent |

---

## Configuration

```python
SENSOR_PARAMS = {
    'primary_camera': {
        'resolution': (1920, 1080),
        'fps': 60,
        'hdr_enabled': True,
        'interface': 'GMSL2'
    },
    'secondary_camera': {
        'enabled': False,  # Optional
        'resolution': (1920, 1080),
        'fps': 30
    },
    'health': {
        'thermal_warning_c': 80,
        'thermal_critical_c': 85,
        'fps_jitter_tolerance_ms': 5,
        'min_brightness_threshold': 10
    }
}
```

---

## Integration

```
Layer 0 (Sensor) ──────► Pre-process ──────► Engine 1A/1B
      │
      └──► Health Status ──► System Health Manager
```

---

## Files

| File | Purpose |
|------|---------|
| [arquitectura.svg](arquitectura.svg) | Component structure |
| [flujo.svg](flujo.svg) | Capture flow |
| `spec.md` | This document |
