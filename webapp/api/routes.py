"""
STAC-CAPS API Routes
REST endpoints for video upload, calibration, and processing
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel
from typing import List, Tuple, Optional
import uuid
import shutil
from pathlib import Path

from .. import config
from ..core.model_manager import ModelManager
from ..core.pipeline import Pipeline
from ..core.video_processor import VideoProcessor

router = APIRouter()

# In-memory session storage (use Redis in production)
sessions = {}


# =============================================================================
# MODELS
# =============================================================================

class CalibrationRequest(BaseModel):
    """Rail calibration points."""
    left_rail: List[Tuple[int, int]]   # [(x1,y1), (x2,y2)]
    right_rail: List[Tuple[int, int]]  # [(x1,y1), (x2,y2)]
    track_gauge_mm: float = 1435.0     # Standard gauge


class ProcessingStatus(BaseModel):
    """Processing job status."""
    session_id: str
    status: str  # pending, processing, completed, error
    progress: float  # 0.0 - 1.0
    current_frame: int
    total_frames: int
    fps: float
    message: str


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.get("/models/status")
async def get_models_status():
    """Check which models are available/need download."""
    manager = ModelManager()
    return manager.get_status()


@router.post("/models/download")
async def download_models(background_tasks: BackgroundTasks):
    """Download all required models."""
    manager = ModelManager()
    background_tasks.add_task(manager.download_all)
    return {"message": "Download started", "models": list(config.MODEL_URLS.keys())}


@router.post("/upload")
async def upload_video(file: UploadFile = File(...)):
    """
    Upload video file for processing.
    Returns session_id and first frame for calibration.
    """
    # Validate format
    ext = Path(file.filename).suffix.lower()
    if ext not in config.SUPPORTED_FORMATS:
        raise HTTPException(400, f"Unsupported format: {ext}")
    
    # Create session
    session_id = str(uuid.uuid4())[:8]
    session_dir = config.UPLOADS_DIR / session_id
    session_dir.mkdir(exist_ok=True)
    
    # Save video
    video_path = session_dir / f"input{ext}"
    with open(video_path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    
    # Extract first frame
    processor = VideoProcessor(str(video_path))
    first_frame_path = session_dir / "first_frame.jpg"
    frame_info = processor.extract_first_frame(str(first_frame_path))
    
    # Store session
    sessions[session_id] = {
        "video_path": str(video_path),
        "status": "uploaded",
        "calibration": None,
        "total_frames": frame_info["total_frames"],
        "fps": frame_info["fps"],
        "resolution": frame_info["resolution"]
    }
    
    return {
        "session_id": session_id,
        "first_frame_url": f"/api/session/{session_id}/first_frame",
        "total_frames": frame_info["total_frames"],
        "fps": frame_info["fps"],
        "resolution": frame_info["resolution"]
    }


@router.get("/session/{session_id}/first_frame")
async def get_first_frame(session_id: str):
    """Get first frame image for calibration UI."""
    frame_path = config.UPLOADS_DIR / session_id / "first_frame.jpg"
    if not frame_path.exists():
        raise HTTPException(404, "Frame not found")
    return FileResponse(str(frame_path), media_type="image/jpeg")


@router.post("/session/{session_id}/calibrate")
async def calibrate(session_id: str, calibration: CalibrationRequest):
    """
    Set rail calibration for session.
    """
    if session_id not in sessions:
        raise HTTPException(404, "Session not found")
    
    sessions[session_id]["calibration"] = {
        "left_rail": calibration.left_rail,
        "right_rail": calibration.right_rail,
        "track_gauge_mm": calibration.track_gauge_mm
    }
    sessions[session_id]["status"] = "calibrated"
    
    return {"message": "Calibration saved", "session_id": session_id}


@router.post("/session/{session_id}/process")
async def start_processing(session_id: str, background_tasks: BackgroundTasks):
    """
    Start full pipeline processing.
    Progress available via WebSocket.
    """
    if session_id not in sessions:
        raise HTTPException(404, "Session not found")
    
    session = sessions[session_id]
    
    if session["calibration"] is None:
        raise HTTPException(400, "Calibration required before processing")
    
    # Initialize pipeline
    pipeline = Pipeline(
        calibration=session["calibration"],
        device=config.DEVICE,
        fp16=config.FP16
    )
    
    # Store pipeline reference
    session["pipeline"] = pipeline
    session["status"] = "processing"
    session["progress"] = 0.0
    session["current_frame"] = 0
    
    # Start background processing
    background_tasks.add_task(
        _process_video,
        session_id,
        session["video_path"],
        pipeline
    )
    
    return {
        "message": "Processing started",
        "session_id": session_id,
        "websocket_url": f"/ws/session/{session_id}"
    }


@router.get("/session/{session_id}/status")
async def get_status(session_id: str):
    """Get current processing status."""
    if session_id not in sessions:
        raise HTTPException(404, "Session not found")
    
    session = sessions[session_id]
    return ProcessingStatus(
        session_id=session_id,
        status=session.get("status", "unknown"),
        progress=session.get("progress", 0.0),
        current_frame=session.get("current_frame", 0),
        total_frames=session.get("total_frames", 0),
        fps=session.get("processing_fps", 0.0),
        message=session.get("message", "")
    )


@router.get("/session/{session_id}/results")
async def get_results(session_id: str):
    """Get processing results (JSON detections)."""
    results_path = config.RESULTS_DIR / session_id / "results.json"
    if not results_path.exists():
        raise HTTPException(404, "Results not ready")
    
    return FileResponse(str(results_path), media_type="application/json")


@router.get("/session/{session_id}/video")
async def get_annotated_video(session_id: str):
    """Get annotated output video."""
    video_path = config.RESULTS_DIR / session_id / "output.mp4"
    if not video_path.exists():
        raise HTTPException(404, "Video not ready")
    
    return FileResponse(str(video_path), media_type="video/mp4")


# =============================================================================
# BACKGROUND TASKS
# =============================================================================

async def _process_video(session_id: str, video_path: str, pipeline: Pipeline):
    """Background task: process video frame by frame."""
    import json
    from ..core.video_processor import VideoProcessor
    
    session = sessions[session_id]
    results_dir = config.RESULTS_DIR / session_id
    results_dir.mkdir(exist_ok=True)
    
    processor = VideoProcessor(video_path)
    all_results = []
    
    try:
        output_path = results_dir / "output.mp4"
        
        for frame_idx, frame, annotated in processor.process_with_pipeline(
            pipeline,
            output_path=str(output_path)
        ):
            # Update session status
            session["current_frame"] = frame_idx
            session["progress"] = frame_idx / session["total_frames"]
            
            # Store frame results
            frame_result = pipeline.get_last_result()
            if frame_result:
                all_results.append({
                    "frame": frame_idx,
                    "detections": frame_result.get("detections", []),
                    "tracks": frame_result.get("tracks", []),
                    "ttc": frame_result.get("ttc"),
                    "risk_scores": frame_result.get("risk_scores", {}),
                    "action": frame_result.get("action")
                })
        
        # Save JSON results
        with open(results_dir / "results.json", "w") as f:
            json.dump(all_results, f, indent=2, default=str)
        
        session["status"] = "completed"
        session["progress"] = 1.0
        session["message"] = "Processing complete"
        
    except Exception as e:
        session["status"] = "error"
        session["message"] = str(e)
