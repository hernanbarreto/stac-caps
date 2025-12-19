"""
STAC-CAPS WebApp - FastAPI Application
Video processing server with rail calibration and 3D visualization
"""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path

from .api import routes
from .api import websocket
from . import config


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    
    app = FastAPI(
        title="STAC-CAPS",
        description="Sistema de Tracking Avanzado para Colisión y Anti-Colisión en Proximidad de Seguridad",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc"
    )
    
    # CORS for development
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Mount static files
    static_dir = Path(__file__).parent / "static"
    static_dir.mkdir(exist_ok=True)
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
    
    # Include routers
    app.include_router(routes.router, prefix="/api", tags=["API"])
    app.include_router(websocket.router, prefix="/ws", tags=["WebSocket"])
    
    # Root redirect to UI
    @app.get("/")
    async def root():
        from fastapi.responses import FileResponse
        return FileResponse(static_dir / "index.html")
    
    # Health check
    @app.get("/health")
    async def health():
        return {"status": "ok", "version": "0.1.0"}
    
    return app


# Application instance
app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "webapp.app:app",
        host=config.HOST,
        port=config.PORT,
        reload=config.DEBUG
    )
