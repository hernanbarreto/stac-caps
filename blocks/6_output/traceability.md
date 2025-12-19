# Block 6: Output Interface - Traceability

## Mapeo Arquitectura → Código
| ID SVG | Componente | Archivo |
|--------|------------|---------|
| comp_can | CAN Bus | can/encoder.py |
| comp_scada | SCADA | scada/opcua.py |
| comp_mqtt | MQTT | mqtt/publisher.py |
| comp_rest | REST | rest/api.py |
| comp_audit | Audit | audit/logger.py |

## Estructura
```
6_output/src/
├── output.py, interfaces.py, config.py
├── can/, scada/, mqtt/, rest/, audit/
```
| Fecha | Cambio |
|-------|--------|
| 2025-12-19 | Creación inicial |
