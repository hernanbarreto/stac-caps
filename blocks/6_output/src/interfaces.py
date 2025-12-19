# Block 6: Output - Interfaces
from dataclasses import dataclass
from typing import Optional

@dataclass
class SafetyDecision:
    timestamp: float
    action: str
    ttc_min: float
    ttc_confidence: float
    risk_score: float
    target_id: Optional[int] = None

@dataclass
class TelemetryPacket:
    timestamp: float
    frame_id: int
    active_tracks: int
    avg_ttc: float
    system_fps: float
    health_status: str
