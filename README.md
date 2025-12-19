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
# Clonar/navegar al proyecto
cd IN3

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

### 1. Subir Video
- Arrastra o haz clic para cargar un video (MP4, AVI, MOV, MKV)

### 2. Calibrar Rieles
- Haz clic en **2 puntos del riel izquierdo** (se marcan en rojo)
- Haz clic en **2 puntos del riel derecho** (se marcan en verde)
- Ingresa el **ancho de trocha** en mm (default: 1435mm para trocha estándar)

### 3. Procesar
- Clic en "Iniciar Procesamiento"
- El sistema procesa frame a frame ejecutando:
  - Estimación de profundidad (DepthAnythingV2)
  - Detección de objetos (RT-DETR)
  - Tracking multi-objeto (BotSORT + OSNet)
  - Predicción de comportamiento
  - Cálculo de TTC
  - Decisión de seguridad

### 4. Resultados
- **Video anotado**: Con bboxes, IDs, estado de seguridad
- **JSON**: Detecciones y tracks por frame
- **Vista 3D**: Visualización en tiempo real con Three.js

---

## 🏗️ Arquitectura

```
STAC-CAPS Pipeline (50ms total @ 20 FPS)
├── Block 0: Sensor Input (frame decode)
├── Block 1: Calibración (geometría via trocha)
├── Engine 1A: Depth (22ms) - DepthAnythingV2
├── Engine 1B: Semantic (25ms) - RT-DETR + RTMPose
├── Engine 2: Persistence (5ms) - BotSORT + OSNet ReID
├── Engine 3: Behavior (3ms) - TTC + ToM + Risk
├── Block 3: Fusion 3D (3ms)
└── Block 5: Safety (7ms) - BRAKE/WARNING/CLEAR
```

---

## 📁 Estructura del Proyecto

```
IN3/
├── README.md
├── requirements.txt
│
├── webapp/                    # Servidor web
│   ├── run.py                 # Launcher
│   ├── app.py                 # FastAPI
│   ├── config.py              # Configuración
│   ├── api/                   # REST + WebSocket
│   ├── core/                  # Pipeline + procesamiento
│   └── static/                # Frontend + Three.js
│
└── blocks/                    # Módulos del sistema
    ├── 0_sensor_input/
    ├── 1_calibration/
    ├── 2_cognitive_trinity/
    │   ├── engines/
    │   │   ├── engine_1a_depth/
    │   │   ├── engine_1b_semantic/
    │   │   ├── engine_2_persistence/
    │   │   └── engine_3_behavior/
    │   └── shared/inference/  # PyTorch + TensorRT
    ├── 3_fusion/
    ├── 4_meta_cognition/
    ├── 5_safety_envelope/
    └── 6_output/
```

---

## 🔧 Configuración

### Variables de Entorno

| Variable | Default | Descripción |
|----------|---------|-------------|
| `STAC_HOST` | `0.0.0.0` | Host del servidor |
| `STAC_PORT` | `8000` | Puerto |
| `STAC_DEBUG` | `true` | Modo debug |

### Modelos

Los modelos se descargan automáticamente al primer uso:

| Modelo | Tamaño | Uso |
|--------|--------|-----|
| DepthAnythingV2 | ~350MB | Estimación de profundidad |
| RT-DETR-X | ~280MB | Detección de objetos |
| RTMPose-T | ~15MB | Estimación de pose |
| OSNet-x0.25 | ~7MB | Re-identificación |

Para usar **TensorRT** (3-4x más rápido):
```bash
# Convertir ONNX a TensorRT
trtexec --onnx=model.onnx --saveEngine=model.trt --fp16
```

---

## 📊 API Endpoints

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/models/status` | Estado de modelos |
| POST | `/api/upload` | Subir video |
| GET | `/api/session/{id}/first_frame` | Primer frame para calibrar |
| POST | `/api/session/{id}/calibrate` | Guardar calibración |
| POST | `/api/session/{id}/process` | Iniciar procesamiento |
| GET | `/api/session/{id}/results` | JSON resultados |
| GET | `/api/session/{id}/video` | Video anotado |
| WS | `/ws/session/{id}` | Streaming tiempo real |

---

## ⚠️ Decisiones de Seguridad

| TTC | Riesgo | Acción | Color |
|-----|--------|--------|-------|
| < 1.0s | > 0.8 | EMERGENCY | 🔴 |
| < 2.0s | > 0.7 | SERVICE | 🟠 |
| < 3.0s | - | WARNING | 🟡 |
| < 5.0s | - | CAUTION | 🟢 |
| ≥ 5.0s | < 0.5 | CLEAR | ⚪ |

---

## 📜 Licencia y Autoría

STAC-CAPS © 2024 - Sistema de seguridad ferroviaria basado en visión por computadora.

---

## 🐛 Troubleshooting

### CUDA no disponible
```bash
# Verificar instalación
python -c "import torch; print(torch.cuda.is_available())"
```

### Modelos no descargan
```bash
# Descargar manualmente
python -c "from webapp.core.model_manager import ModelManager; ModelManager().download_all()"
```

### Puerto en uso
```bash
STAC_PORT=8080 python webapp/run.py
```
