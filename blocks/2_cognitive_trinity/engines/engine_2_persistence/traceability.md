# Engine 2: Persistence - Traceability Matrix

Mapeo **1:1** entre documentación (SVGs, spec) y código.

---

## Mapeo Arquitectura → Código

| ID en `arquitectura.svg` | Componente | Archivo en `src/` | Clase/Función |
|--------------------------|------------|-------------------|---------------|
| `comp_input` | INPUT | `interfaces.py` | `TrackingInput` dataclass |
| `comp_botsort` | BotSORT | `tracking/botsort.py` | `BotSORT` class |
| `comp_osnet` | OSNet ReID | `reid/osnet.py` | `OSNetReID` class |
| → EMA Update | - | `reid/ema.py` | `update_embedding()` |
| `comp_kalman` | Kalman Filter | `kalman/filter.py` | `AdaptiveKalman` class |
| `comp_association` | Association | `tracking/association.py` | `associate_detections()` |
| `comp_memory` | Track Memory | `memory/lru_cache.py` | `TrackMemory` class |
| `comp_output` | OUTPUT | `interfaces.py` | `TrackingOutput` dataclass |

---

## Mapeo Flujo → Código

| Step en `flujo.svg` | Descripción | Función | Timing |
|---------------------|-------------|---------|--------|
| 1. RECEIVE DETECTIONS | Input | `Engine2Persistence.process()` | - |
| 2. EXTRACT ReID | Feature extraction | `osnet.extract_batch()` | 2 ms |
| 3. KALMAN PREDICT | Predict positions | `kalman.predict()` | <1 ms |
| 4. ASSOCIATE | Match dets to tracks | `associate_detections()` | <1 ms |
| → Stage 1: IoU | High confidence | `_iou_matching()` | - |
| → Stage 2: ReID | Appearance | `_reid_matching()` | - |
| 5. UPDATE MATCHED | Update tracks | `botsort._update_track()` | <1 ms |
| → EMA embedding | - | `update_embedding()` | - |
| → Quality score | - | `Track.compute_quality_score()` | - |
| 6. CREATE NEW | New tracks | `botsort._create_track()` | - |
| 7. MANAGE TRACKS | Ghost/delete | `botsort._age_track()` | <1 ms |
| → LRU eviction | - | `TrackMemory._evict()` | - |
| 8. OUTPUT | Return results | `return TrackingOutput(...)` | - |

---

## Estructura de Código

```
engine_2_persistence/src/
├── __init__.py
├── engine.py                    # Engine2Persistence (entry point)
├── interfaces.py                # Track, TrackState, TrackingInput/Output
├── config.py                    # PERSISTENCE_PARAMS
│
├── tracking/
│   ├── __init__.py
│   ├── botsort.py               # class BotSORT
│   └── association.py           # associate_detections()
│
├── reid/
│   ├── __init__.py
│   ├── osnet.py                 # class OSNetReID
│   └── ema.py                   # update_embedding()
│
├── kalman/
│   ├── __init__.py
│   └── filter.py                # class AdaptiveKalman
│
└── memory/
    ├── __init__.py
    └── lru_cache.py             # class TrackMemory
```

---

## Reglas de Modificación

| Si cambias... | Actualiza también... |
|---------------|----------------------|
| Nuevo componente de tracking | Agregar caja en SVG + código |
| Cambio de modelo ReID | Actualizar SVG + reid/ |
| Cambio de parámetros Kalman | Actualizar spec.md + config.py |
| Nuevo estado de Track | Actualizar interfaces.py + SVGs |

---

## Historial de Cambios

| Fecha | Cambio | Archivos Afectados |
|-------|--------|-------------------|
| 2025-12-19 | Creación inicial | traceability.md, toda estructura src/ |
