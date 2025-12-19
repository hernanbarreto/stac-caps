# Engine 3: Behavior - Traceability Matrix

Mapeo **1:1** entre documentación (SVGs, spec) y código.

---

## Mapeo Arquitectura → Código

| ID en `arquitectura.svg` | Componente | Archivo en `src/` | Clase/Función |
|--------------------------|------------|-------------------|---------------|
| `comp_input` | INPUT | `interfaces.py` | `BehaviorInput` dataclass |
| `comp_kinematic` | Kinematic Predictor | `kinematic/predictor.py` | `predict_kinematic_v2()` |
| `comp_smpl_pred` | SMPL Pose Predictor | `pose/smpl_predictor.py` | `predict_from_pose_v2()` |
| `comp_tom` | Theory of Mind | `tom/intent.py` | `infer_intent_v2()` |
| → Context Priors | - | `tom/priors.py` | `get_context_priors()` |
| → Temporal Smoothing | - | `tom/smoothing.py` | `smooth_intent()` |
| `comp_ttc` | TTC Calculator | `ttc/calculator.py` | `compute_ttc_v2()` |
| `comp_risk` | Risk Scorer | `risk/scorer.py` | `compute_risk_score_v2()` |
| `comp_validation` | Cross-Validation | `validation/optical_flow.py` | `cross_validate_trajectory()` |
| `comp_output` | OUTPUT | `interfaces.py` | `BehaviorOutput` dataclass |

---

## Mapeo Flujo → Código

| Step en `flujo.svg` | Descripción | Función | Timing |
|---------------------|-------------|---------|--------|
| 1. RECEIVE TRACKS | Input | `Engine3Behavior.process()` | - |
| 2. PREDICT TRAJECTORY | Kinematic | `predict_kinematic_v2()` | 1 ms |
| 2b. POSE VELOCITY | For PERSON | `predict_from_pose_v2()` | <1 ms |
| 3. INFER INTENT | ToM | `infer_intent_v2()` | 1 ms |
| 3b. TEMPORAL SMOOTH | - | `smooth_intent()` | - |
| 4. CROSS-VALIDATE | Optical flow | `cross_validate_trajectory()` | <1 ms |
| 5. COMPUTE TTC | Confidence intervals | `compute_ttc_v2()` | <1 ms |
| 5b. EARLY EXIT | If TTC < 1.0s | - | - |
| 6. CALCULATE RISK | Multi-factor | `compute_risk_score_v2()` | <1 ms |
| 7. ADJUST MARGINS | Safety | `_compute_safety_margin()` | - |
| 8. OUTPUT | Return | `return BehaviorOutput(...)` | - |

---

## Estructura de Código

```
engine_3_behavior/src/
├── __init__.py
├── engine.py                    # Engine3Behavior (entry point)
├── interfaces.py                # Prediction, Trajectory, Intent, TTCResult
├── config.py                    # ENGINE3_PARAMS
│
├── kinematic/
│   ├── __init__.py
│   └── predictor.py             # predict_kinematic_v2()
│
├── pose/
│   ├── __init__.py
│   └── smpl_predictor.py        # predict_from_pose_v2()
│
├── tom/
│   ├── __init__.py
│   ├── intent.py                # infer_intent_v2()
│   ├── priors.py                # get_context_priors()
│   └── smoothing.py             # smooth_intent()
│
├── ttc/
│   ├── __init__.py
│   └── calculator.py            # compute_ttc_v2()
│
├── risk/
│   ├── __init__.py
│   └── scorer.py                # compute_risk_score_v2()
│
└── validation/
    ├── __init__.py
    └── optical_flow.py          # cross_validate_trajectory()
```

---

## Reglas de Modificación

| Si cambias... | Actualiza también... |
|---------------|----------------------|
| Nuevo horizonte de predicción | config.py + kinematic/ |
| Nuevo estado de intent | tom/intent.py + priors.py + SVGs |
| Cambio de factores de riesgo | risk/scorer.py + config.py |
| Cambio de umbrales TTC | config.py + ttc/calculator.py |

---

## Historial de Cambios

| Fecha | Cambio | Archivos Afectados |
|-------|--------|-------------------|
| 2025-12-19 | Creación inicial | traceability.md, toda estructura src/ |
