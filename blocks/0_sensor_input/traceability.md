# Block 0: Sensor Input - Traceability Matrix

Mapeo **1:1** entre documentación (SVGs, spec) y código.

---

## Mapeo Arquitectura → Código

| ID en `arquitectura.svg` | Componente | Archivo en `src/` | Clase/Función |
|--------------------------|------------|-------------------|---------------|
| `comp_primary` | Primary Camera | `camera/primary.py` | `PrimaryCamera` class |
| `comp_secondary` | Secondary Camera | `camera/secondary.py` | `SecondaryCamera` class |
| `comp_isp` | ISP Pipeline | `isp/pipeline.py` | `ISPPipeline` class |
| → Demosaic | - | `isp/pipeline.py` | `_demosaic()` |
| → Denoise | - | `isp/pipeline.py` | `_denoise()` |
| → HDR Tone Map | - | `isp/pipeline.py` | `_tone_map()` |
| → White Balance | - | `isp/pipeline.py` | `_white_balance()` |
| → Gamma | - | `isp/pipeline.py` | `_gamma_correct()` |
| `comp_health` | Health Monitor | `health/monitor.py` | `check_sensor_health()` |
| `comp_output` | OUTPUT | `interfaces.py` | `SensorInput` dataclass |

---

## Mapeo Flujo → Código

| Step en `flujo.svg` | Descripción | Función | Timing |
|---------------------|-------------|---------|--------|
| 1. CAMERA CAPTURE | HDR capture | `PrimaryCamera.capture()` | 16.67 ms |
| 2. ISP PIPELINE | On-chip processing | `ISPPipeline.process()` | 0 ms (parallel) |
| 3. DMA TRANSFER | To GPU memory | (hardware) | ~2 ms |
| 4. HEALTH CHECK | Status monitor | `check_sensor_health()` | <1 ms |
| 5. OUTPUT | Frame + metadata | `SensorManager.capture()` | - |

---

## Estructura de Código

```
0_sensor_input/src/
├── __init__.py
├── sensor.py                    # SensorManager (entry point)
├── interfaces.py                # FrameMetadata, HealthState
├── config.py                    # SENSOR_PARAMS
│
├── camera/
│   ├── __init__.py
│   ├── primary.py               # class PrimaryCamera
│   └── secondary.py             # class SecondaryCamera
│
├── isp/
│   ├── __init__.py
│   └── pipeline.py              # class ISPPipeline
│
└── health/
    ├── __init__.py
    └── monitor.py               # check_sensor_health()
```

---

## Reglas de Modificación

| Si cambias... | Actualiza también... |
|---------------|----------------------|
| Nuevo sensor | camera/ + config.py + SVGs |
| Nuevo stage ISP | isp/pipeline.py + SVG |
| Nuevo health check | health/monitor.py + spec.md |

---

## Historial de Cambios

| Fecha | Cambio | Archivos Afectados |
|-------|--------|-------------------|
| 2025-12-19 | Creación inicial | traceability.md, toda estructura src/ |
