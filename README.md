# 🚂 STAC-CAPS

**Sistema de Tracking Avanzado para Colisión y Anti-Colisión en Proximidad de Seguridad**

Sistema de visión por computadora para seguridad ferroviaria con detección de obstáculos, tracking multi-objeto, predicción de comportamiento y decisión de frenado en tiempo real.

---

## 🚀 Inicio Rápido

### Requisitos
- Python 3.10+
- CUDA 11.8+ (RTX 3060 o superior)
- WSL2 (Windows) o Linux

### Instalación

```bash
# Clonar repositorio
git clone https://github.com/hernanbarreto/stac-caps.git
cd stac-caps

# Crear entorno virtual (recomendado)
python -m venv venv
source venv/bin/activate  # Linux/WSL
# o: venv\Scripts\activate  # Windows

# Instalar dependencias
pip install -r requirements.txt
```

### Ejecutar WebApp

```bash
python webapp/run.py
```

Abrir **http://localhost:8000** en el navegador.

---

## 📖 Uso

1. **Subir Video** - Arrastra o selecciona archivo (MP4, AVI, MOV, MKV)
2. **Calibrar Rieles** - Click en 2 puntos por riel + ancho de trocha (default: 1435mm)
3. **Procesar** - El sistema ejecuta el pipeline completo frame a frame
4. **Resultados** - Video anotado + JSON descargables + Vista 3D

---

## 🏗️ Arquitectura

```
STAC-CAPS Pipeline v3.4
═══════════════════════════════════════════════════════════
│ PIPELINED EXECUTION: 50ms throughput @ 20 FPS          │
│ End-to-end latency: ~72ms                               │
═══════════════════════════════════════════════════════════

Frame N:   [CAP]──[═══ 1A+1B ═══]──[FUS]──[E2]──[E3]──[SAF]
Frame N+1:       [CAP]──[═══ 1A+1B ═══]──[FUS]──[E2]──[E3]──[SAF]
                       └── Parallel ──┘
```

| Componente | Tiempo | Descripción |
|------------|--------|-------------|
| Capture + ISP | 5ms | Frame decode + preprocessing |
| Engine 1A | 22ms | DepthAnythingV2 (profundidad) |
| Engine 1B | 25ms | RT-DETR + RTMPose (detección) |
| Fusion 3D | 3ms | Combinar depth + semantic |
| Engine 2 | 5ms | BotSORT + OSNet (tracking) |
| Engine 3 | 5ms | TTC + Risk (comportamiento) |
| Safety | 7ms | Decisión de frenado |

---

## ⚠️ Modos del Sistema (Fail-Safe)

| Modo | Condición | Frenado Automático |
|------|-----------|-------------------|
| **NOMINAL** | Calibración >80% | ✅ Habilitado |
| **DEGRADED** | Calibración 40-80% | ❌ Solo alertas |
| **FAULT** | Error crítico | ❌ Manual only |

En **Modo Degradado**, el sistema reporta:
- `P(alert)` - Probabilidad de alerta correcta
- `P(miss)` - Probabilidad de **NO detectar** obstáculo real
- `degraded_reason` - Causa: TUNNEL, SWITCH, OCCLUSION, etc.

---

## 📊 Decisiones de Seguridad

### Modo NOMINAL

| TTC | Acción | Hardware |
|-----|--------|----------|
| < 1.0s | EMERGENCY_BRAKE | GPIO relay |
| 1.0-2.0s | SERVICE_BRAKE | CAN bus |
| 2.0-3.0s | WARNING | MQTT alert |
| 3.0-5.0s | CAUTION | Log only |
| ≥ 5.0s | CLEAR | Normal |

### Modo DEGRADED

Solo alertas visuales/sonoras, **sin frenado automático**. El operador debe mantener vigilancia.

---

## 🔧 Configuración

| Variable | Default | Descripción |
|----------|---------|-------------|
| `STAC_HOST` | `0.0.0.0` | Host servidor |
| `STAC_PORT` | `8000` | Puerto |
| `STAC_DEBUG` | `true` | Modo debug |

### Modelos (Auto-descarga)

| Modelo | Tamaño | Uso |
|--------|--------|-----|
| DepthAnythingV2 | ~350MB | Profundidad |
| RT-DETR-X | ~280MB | Detección |
| RTMPose-T | ~15MB | Pose |
| OSNet-x0.25 | ~7MB | ReID |

---

## 📁 Estructura

```
stac-caps/
├── spec.md              # Especificación técnica completa
├── requirements.txt     # Dependencias Python
├── webapp/              # Servidor FastAPI + Three.js
└── blocks/              # Módulos del sistema
    ├── 0_sensor_input/
    ├── 1_calibration/
    ├── 2_cognitive_trinity/
    │   └── engines/     # 1A, 1B, 2, 3
    ├── 3_fusion/
    ├── 4_meta_cognition/
    ├── 5_safety_envelope/
    └── 6_output/
```

---

## 📜 Documentación

- **[spec.md](spec.md)** - Especificación técnica completa v3.4
- **[Arquitectura SVG](stac_caps_arquitectura.svg)** - Diagrama de bloques
- **[Flujo SVG](stac_caps_flujo.svg)** - Diagrama de flujo

---

## ⚙️ Hardware Soportado

| Plataforma | Status | FPS |
|------------|--------|-----|
| RTX 3060 | ✅ Dev/Prod | ~20 |
| RTX 3090 | ✅ Tested | ~35 |
| Jetson Orin | 🔲 Roadmap | TBD |

---

## 🐛 Troubleshooting

```bash
# CUDA no disponible
python -c "import torch; print(torch.cuda.is_available())"

# Descargar modelos manualmente
python -c "from webapp.core.model_manager import ModelManager; ModelManager().download_all()"

# Puerto en uso
STAC_PORT=8080 python webapp/run.py
```

---

## 📜 Licencia

STAC-CAPS © 2024 - Sistema de seguridad ferroviaria
