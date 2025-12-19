#!/usr/bin/env python3
"""
STAC-CAPS WebApp Launcher
Run this to start the server
"""

import sys
import os
from pathlib import Path

# Add project root to path
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from webapp.core.model_manager import ModelManager
from webapp import config


def main():
    print("=" * 60)
    print("  🚂 STAC-CAPS - Sistema de Seguridad Ferroviaria")
    print("=" * 60)
    print()
    
    # Check models
    print("Verificando modelos...")
    manager = ModelManager()
    status = manager.get_status()
    
    for name, info in status.items():
        if info["downloaded"]:
            print(f"  ✓ {name}: disponible")
        else:
            print(f"  ✗ {name}: falta ({info['size_mb']}MB)")
    
    missing = [n for n, i in status.items() if not i["downloaded"]]
    if missing:
        print()
        response = input(f"¿Descargar modelos faltantes ({len(missing)})? [Y/n]: ")
        if response.lower() != 'n':
            manager.download_all()
    
    print()
    print(f"Iniciando servidor en http://{config.HOST}:{config.PORT}")
    print("Presiona Ctrl+C para detener")
    print()
    
    # Start server
    import uvicorn
    uvicorn.run(
        "webapp.app:app",
        host=config.HOST,
        port=config.PORT,
        reload=config.DEBUG,
        log_level="info"
    )


if __name__ == "__main__":
    main()
