# Engine 1A: Depth - Traceability Matrix

Este documento establece el mapeo **1:1** entre la documentación (SVGs, spec) y el código.

---

## Nomenclatura de IDs

Los IDs en los SVGs usan el formato:
- Arquitectura: `comp_<nombre>` o `id="<nombre>"`
- Flujo: Steps numerados 1-N

---

## Mapeo Arquitectura → Código

| ID en `arquitectura.svg` | Componente | Archivo en `src/` | Clase/Función |
|--------------------------|------------|-------------------|---------------|
| `comp_input` | FROM PRE-PROCESS | `interfaces.py` | `DepthInput` dataclass |
| `comp_resize` | RESIZE | `preprocessing/resize.py` | `resize_for_depth()` |
| `comp_depth_model` | DepthAnything-v2 | `inference/depth_model.py` | `DepthAnythingV2` class |
| `comp_calib_input` | LAYER 1 (scale) | `interfaces.py` | `CalibrationInput` dataclass |
| (box) METRIC SCALE | Metric Scale | `calibration/metric_scale.py` | `apply_metric_scale()` |
| `comp_refinement` | REFINEMENT PIPELINE | `refinement/` | (submodule) |
| → Outlier Detect | - | `refinement/outlier.py` | `detect_outliers()` |
| → Guided Filter | - | `refinement/guided_filter.py` | `guided_filter()` |
| → Temporal EMA | - | `refinement/temporal_ema.py` | `temporal_smooth()` |
| (box) POINT CLOUD | Point Cloud + Confidence | `output/point_cloud.py` | `generate_point_cloud()` |
| (box) Enhanced Confidence | - | `confidence/enhanced.py` | `compute_confidence()` |
| `comp_output` | TO ENGINE 1B | `interfaces.py` | `DepthOutput` dataclass |

---

## Mapeo Flujo → Código

| Step en `flujo.svg` | Descripción | Función en Código | Timing |
|---------------------|-------------|-------------------|--------|
| 1. RECEIVE FRAME | Input | `Engine1ADepth.process()` entry | - |
| 2. RESIZE INPUT | Resize 518×518 | `resize_for_depth(frame)` | 2 ms |
| 3. INFERENCE | DepthAnything-v2 | `depth_model.infer(resized)` | 18 ms |
| 4. METRIC SCALE | Apply calibration | `apply_metric_scale(rel, scale)` | <1 ms |
| 5. OUTLIER DETECT | Median filter | `detect_outliers(depth)` | <1 ms |
| 6. GUIDED FILTER | Edge-aware | `guided_filter(rgb, depth)` | 1 ms |
| 7. TEMPORAL EMA | Smoothing | `temporal_smooth(cur, prev, α)` | 1 ms |
| 8. UPSCALE | Resize to original | `resize_to_original(refined)` | - |
| 9. POINT CLOUD | Inverse projection | `generate_point_cloud(depth, K)` | 2 ms |
| 10. CONFIDENCE | Multi-factor | `compute_confidence(...)` | <1 ms |
| 11. OUTPUT | Return results | `return DepthOutput(...)` | - |

---

## Estructura de Código Propuesta

```
engine_1a_depth/src/
├── __init__.py
├── engine.py                    # Clase principal: Engine1ADepth (entry point)
├── interfaces.py                # DepthInput, DepthOutput, CalibrationInput
│
├── preprocessing/
│   ├── __init__.py
│   └── resize.py                # resize_for_depth(), resize_to_original()
│
├── inference/
│   ├── __init__.py
│   └── depth_model.py           # class DepthAnythingV2
│
├── calibration/
│   ├── __init__.py
│   └── metric_scale.py          # apply_metric_scale()
│
├── refinement/
│   ├── __init__.py
│   ├── outlier.py               # detect_outliers()
│   ├── guided_filter.py         # guided_filter()
│   └── temporal_ema.py          # temporal_smooth()
│
├── output/
│   ├── __init__.py
│   └── point_cloud.py           # generate_point_cloud()
│
├── confidence/
│   ├── __init__.py
│   └── enhanced.py              # compute_confidence()
│
└── config.py                    # DEPTH_PARAMS (thresholds, weights, etc.)
```

---

## Referencia Cruzada: spec.md

| Sección en spec.md | Archivo de Código |
|--------------------|-------------------|
| Components → DepthAnything-v2 | `inference/depth_model.py` |
| Components → Outlier Detection | `refinement/outlier.py` |
| Components → Edge-aware Refinement | `refinement/guided_filter.py` |
| Components → Temporal Smoothing | `refinement/temporal_ema.py` |
| Components → Enhanced Confidence | `confidence/enhanced.py` |
| Components → Point Cloud Generator | `output/point_cloud.py` |
| System Limits → DEPTH_PARAMS | `config.py` |

---

## Reglas de Modificación

> ⚠️ **IMPORTANTE**: Cualquier cambio en el código debe reflejarse en la documentación y viceversa.

| Si cambias... | Actualiza también... |
|---------------|----------------------|
| Nuevo componente en código | Agregar caja en `arquitectura.svg` |
| Nueva función en pipeline | Agregar step en `flujo.svg` |
| Cambio de parámetros | Actualizar `spec.md` → System Limits |
| Cambio de timing | Actualizar badges en SVGs + spec.md |
| Nuevo input/output | Actualizar `interfaces.py` + SVGs |

---

## Validación de Trazabilidad

Para verificar que todo esté alineado:

```bash
# Futuro script de validación
python -m engine_1a_depth.validate_traceability
```

Checks:
- [ ] Cada `comp_*` en SVG tiene archivo correspondiente
- [ ] Cada step en flujo tiene función correspondiente
- [ ] Timings en SVG = Timings en spec.md
- [ ] DEPTH_PARAMS en config.py = spec.md

---

## Historial de Cambios

| Fecha | Cambio | Archivos Afectados |
|-------|--------|-------------------|
| 2025-12-19 | Creación inicial | traceability.md |

