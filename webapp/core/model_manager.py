"""
STAC-CAPS Model Manager
Automatic download and verification of required models
"""

import os
from pathlib import Path
from typing import Dict, Optional
import hashlib
from tqdm import tqdm

from .. import config


class ModelManager:
    """
    Manage model downloads and verification.
    
    Features:
    - Automatic download from HuggingFace
    - Progress tracking
    - Checksum verification
    - Lazy loading
    """
    
    def __init__(self, models_dir: Optional[Path] = None):
        self.models_dir = models_dir or config.MODELS_DIR
        self.models_dir.mkdir(parents=True, exist_ok=True)
    
    def get_status(self) -> Dict[str, dict]:
        """Get status of all models."""
        status = {}
        
        for name, info in config.MODEL_URLS.items():
            path = self.models_dir / info["filename"]
            status[name] = {
                "filename": info["filename"],
                "size_mb": info["size_mb"],
                "downloaded": path.exists(),
                "path": str(path) if path.exists() else None
            }
        
        return status
    
    def is_model_available(self, model_name: str) -> bool:
        """Check if model is downloaded."""
        if model_name not in config.MODEL_URLS:
            return False
        
        info = config.MODEL_URLS[model_name]
        path = self.models_dir / info["filename"]
        return path.exists()
    
    def get_model_path(self, model_name: str) -> Optional[Path]:
        """Get path to model file, download if needed."""
        if model_name not in config.MODEL_URLS:
            raise ValueError(f"Unknown model: {model_name}")
        
        info = config.MODEL_URLS[model_name]
        path = self.models_dir / info["filename"]
        
        if not path.exists():
            self.download_model(model_name)
        
        return path
    
    def download_model(self, model_name: str, force: bool = False) -> Path:
        """
        Download a specific model.
        
        Args:
            model_name: Name of model to download
            force: Re-download even if exists
            
        Returns:
            Path to downloaded model
        """
        import requests
        
        if model_name not in config.MODEL_URLS:
            raise ValueError(f"Unknown model: {model_name}")
        
        info = config.MODEL_URLS[model_name]
        url = info["url"]
        filename = info["filename"]
        size_mb = info["size_mb"]
        
        path = self.models_dir / filename
        
        if path.exists() and not force:
            print(f"Model {model_name} already exists at {path}")
            return path
        
        print(f"Downloading {model_name} ({size_mb}MB)...")
        
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            
            with open(path, 'wb') as f:
                with tqdm(total=total_size, unit='B', unit_scale=True, desc=filename) as pbar:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                        pbar.update(len(chunk))
            
            print(f"Downloaded {model_name} to {path}")
            return path
            
        except Exception as e:
            # Clean up partial download
            if path.exists():
                path.unlink()
            raise RuntimeError(f"Failed to download {model_name}: {e}")
    
    def download_all(self, force: bool = False) -> Dict[str, Path]:
        """Download all required models."""
        paths = {}
        
        for model_name in config.MODEL_URLS:
            try:
                paths[model_name] = self.download_model(model_name, force)
            except Exception as e:
                print(f"Error downloading {model_name}: {e}")
                paths[model_name] = None
        
        return paths
    
    def load_onnx_model(self, model_name: str):
        """Load ONNX model for inference."""
        import onnxruntime as ort
        
        path = self.get_model_path(model_name)
        
        # Use GPU if available
        providers = ['CUDAExecutionProvider', 'CPUExecutionProvider']
        
        session = ort.InferenceSession(
            str(path),
            providers=providers
        )
        
        return session
    
    @staticmethod
    def verify_checksum(path: Path, expected_hash: str) -> bool:
        """Verify file checksum."""
        sha256 = hashlib.sha256()
        
        with open(path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                sha256.update(chunk)
        
        return sha256.hexdigest() == expected_hash
