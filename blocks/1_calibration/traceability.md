# Block 1: Calibration - Traceability Matrix

Mapeo **1:1** entre documentación (SVGs, spec) y código.

---

## Mapeo Arquitectura → Código

| ID en `arquitectura.svg` | Componente | Archivo en `src/` | Clase/Función |
|--------------------------|------------|-------------------|---------------|
| `comp_hard_init` | Hard Initialization | `initialization/hard_init.py` | `hard_initialization()` |
| `comp_landmarks` | Landmark DB | `landmarks/database.py` | `LandmarkDB` class |
| `comp_fallback` | Occlusion Handler | `fallback/occlusion.py` | `handle_occlusion()` |
| `comp_output` | OUTPUT | `interfaces.py` | `CalibrationResult` dataclass |

---

## Estructura de Código

```
1_calibration/src/
├── __init__.py
├── calibrator.py            # CalibrationManager (entry point)
├── interfaces.py            # CalibrationResult, Landmark
├── config.py                # CALIBRATION_PARAMS
├── initialization/
│   ├── __init__.py
│   └── hard_init.py         # hard_initialization()
├── landmarks/
│   ├── __init__.py
│   └── database.py          # class LandmarkDB
└── fallback/
    ├── __init__.py
    └── occlusion.py         # handle_occlusion()
```

---

## Historial de Cambios

| Fecha | Cambio | Archivos Afectados |
|-------|--------|-------------------|
| 2025-12-19 | Creación inicial | traceability.md, toda estructura src/ |
