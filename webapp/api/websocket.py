"""
STAC-CAPS WebSocket Handler
Real-time streaming of processing progress and results
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, Set
import asyncio
import json

router = APIRouter()

# Active connections per session
connections: Dict[str, Set[WebSocket]] = {}


class ConnectionManager:
    """Manage WebSocket connections."""
    
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
    
    async def connect(self, session_id: str, websocket: WebSocket):
        await websocket.accept()
        if session_id not in self.active_connections:
            self.active_connections[session_id] = set()
        self.active_connections[session_id].add(websocket)
    
    def disconnect(self, session_id: str, websocket: WebSocket):
        if session_id in self.active_connections:
            self.active_connections[session_id].discard(websocket)
            if not self.active_connections[session_id]:
                del self.active_connections[session_id]
    
    async def broadcast(self, session_id: str, message: dict):
        """Send message to all connections for a session."""
        if session_id in self.active_connections:
            dead_connections = set()
            for connection in self.active_connections[session_id]:
                try:
                    await connection.send_json(message)
                except Exception:
                    dead_connections.add(connection)
            
            # Clean up dead connections
            for conn in dead_connections:
                self.disconnect(session_id, conn)


manager = ConnectionManager()


@router.websocket("/session/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """
    WebSocket endpoint for real-time updates.
    
    Messages sent:
    - {"type": "status", "progress": 0.5, "frame": 100, "fps": 20.5}
    - {"type": "detection", "frame": 100, "objects": [...]}
    - {"type": "track", "frame": 100, "tracks": [...]}
    - {"type": "alert", "ttc": 2.5, "action": "WARNING", "risk": 0.7}
    - {"type": "complete", "output_url": "/api/session/xxx/video"}
    - {"type": "error", "message": "..."}
    """
    await manager.connect(session_id, websocket)
    
    try:
        # Import here to avoid circular import
        from .routes import sessions
        
        while True:
            # Check session status and send updates
            if session_id in sessions:
                session = sessions[session_id]
                
                # Send status update
                await websocket.send_json({
                    "type": "status",
                    "status": session.get("status", "unknown"),
                    "progress": session.get("progress", 0),
                    "frame": session.get("current_frame", 0),
                    "total_frames": session.get("total_frames", 0),
                    "fps": session.get("processing_fps", 0)
                })
                
                # Check if completed
                if session.get("status") == "completed":
                    await websocket.send_json({
                        "type": "complete",
                        "output_url": f"/api/session/{session_id}/video",
                        "results_url": f"/api/session/{session_id}/results"
                    })
                    break
                
                # Check if error
                if session.get("status") == "error":
                    await websocket.send_json({
                        "type": "error",
                        "message": session.get("message", "Unknown error")
                    })
                    break
            
            # Wait before next update
            await asyncio.sleep(0.5)
            
            # Also listen for client messages
            try:
                data = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=0.1
                )
                message = json.loads(data)
                
                # Handle client commands
                if message.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})
                
            except asyncio.TimeoutError:
                pass  # No message, continue
            except json.JSONDecodeError:
                pass
                
    except WebSocketDisconnect:
        manager.disconnect(session_id, websocket)
    except Exception as e:
        await websocket.send_json({
            "type": "error",
            "message": str(e)
        })
        manager.disconnect(session_id, websocket)


async def send_frame_update(session_id: str, frame_data: dict):
    """
    Send frame update to all connected clients.
    Called by pipeline during processing.
    """
    await manager.broadcast(session_id, {
        "type": "frame",
        **frame_data
    })


async def send_alert(session_id: str, ttc: float, action: str, risk: float):
    """Send safety alert to clients."""
    await manager.broadcast(session_id, {
        "type": "alert",
        "ttc": ttc,
        "action": action,
        "risk": risk
    })
