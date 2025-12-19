# Block 4: Meta-Cognition - Interfaces
from dataclasses import dataclass
from typing import Dict

@dataclass
class TraceEntry:
    timestamp: float
    frame_id: int
    inputs: Dict
    engine_outputs: Dict
    decision: str
    rationale: str
    ttc: float
    risk_score: float
