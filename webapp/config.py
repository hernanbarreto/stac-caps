# STAC-CAPS WebApp Configuration

import os
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).parent.parent
WEBAPP_DIR = Path(__file__).parent
BLOCKS_DIR = BASE_DIR / "blocks"
MODELS_DIR = WEBAPP_DIR / "models"
UPLOADS_DIR = WEBAPP_DIR / "uploads"
RESULTS_DIR = WEBAPP_DIR / "results"

# Create directories
MODELS_DIR.mkdir(exist_ok=True)
UPLOADS_DIR.mkdir(exist_ok=True)
RESULTS_DIR.mkdir(exist_ok=True)

# Server
HOST = os.getenv("STAC_HOST", "0.0.0.0")
PORT = int(os.getenv("STAC_PORT", "8000"))
DEBUG = os.getenv("STAC_DEBUG", "true").lower() == "true"

# Video processing
MAX_VIDEO_SIZE_MB = 500
SUPPORTED_FORMATS = [".mp4", ".avi", ".mov", ".mkv", ".webm"]
DEFAULT_TRACK_GAUGE_MM = 1435  # Standard gauge

# Models - HuggingFace URLs
MODEL_URLS = {
    "depth_anything_v2": {
        "url": "https://huggingface.co/depth-anything/Depth-Anything-V2-Base/resolve/main/depth_anything_v2_vitb.onnx",
        "filename": "depth_anything_v2_vitb.onnx",
        "size_mb": 350
    },
    "rt_detr": {
        "url": "https://huggingface.co/jameslahm/yolov10x/resolve/main/yolov10x.onnx",  # Placeholder
        "filename": "rt_detr_x.onnx",
        "size_mb": 280
    },
    "rtmpose": {
        "url": "https://huggingface.co/OpenMMLab/rtmpose-m/resolve/main/rtmpose_m_256x192.onnx",  # Placeholder
        "filename": "rtmpose_t.onnx",
        "size_mb": 15
    },
    "osnet": {
        "url": "https://huggingface.co/spaces/hysts/osnet/resolve/main/osnet_x025.onnx",  # Placeholder
        "filename": "osnet_x025.onnx",
        "size_mb": 7
    }
}

# Pipeline timing budgets (ms)
TIMING_BUDGETS = {
    "depth": 22,
    "semantic": 25,
    "tracking": 5,
    "behavior": 3,
    "fusion": 3,
    "safety": 7,
    "total": 50  # 20 FPS target
}

# GPU
DEVICE = "cuda:0"
FP16 = True
