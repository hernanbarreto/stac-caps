# Block 5: Safety Envelope - Traceability

## Mapeo Arquitectura → Código
| ID SVG | Componente | Archivo |
|--------|------------|---------|
| comp_ttc_eval | TTC Evaluator | evaluator/ttc.py |
| comp_risk_agg | Risk Aggregator | aggregator/risk.py |
| comp_decision | Decision Engine | decision/engine.py |
| comp_gpio | Hardwire | hardware/gpio.py |
| comp_audit | Audit | audit/logger.py |

## Estructura
```
5_safety_envelope/src/
├── safety.py, interfaces.py, config.py
├── evaluator/, aggregator/, decision/, hardware/, audit/
```
| Fecha | Cambio |
|-------|--------|
| 2025-12-19 | Creación inicial |
