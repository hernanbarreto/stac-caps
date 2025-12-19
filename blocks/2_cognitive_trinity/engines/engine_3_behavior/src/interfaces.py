# Engine 3: Behavior - Data Interfaces
# Prediction, Trajectory, Intent, TTCResult structures

from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional


@dataclass
class Trajectory:
    """
    Multi-scenario trajectory prediction.
    """
    positions: List[Tuple[float, float, float]]  # [(x, y, z), ...]
    timestamps: List[float]                       # [1.0, 2.0, 3.0, ...]
    confidence: float = 1.0
    acceleration_used: bool = True


@dataclass  
class Intent:
    """
    Theory of Mind intent inference result.
    """
    state: str                    # STATIC | LEAVING | APPROACHING | CROSSING
    distraction_prob: float       # [0, 1]
    awareness_prob: float         # [0, 1] 
    action_confidence: float      # [0, 1]
    smoothed: bool = False
    probs: Dict[str, float] = field(default_factory=dict)


@dataclass
class TTCResult:
    """
    Time-To-Collision with confidence intervals.
    """
    min: float              # Conservative (worst case)
    mean: float             # Average case
    max: float              # Optimistic case
    confidence: float       # [0.3, 1.0]


@dataclass
class Prediction:
    """
    Complete prediction for a single track.
    """
    track_id: int
    trajectories: Dict[str, List]  # optimistic/nominal/pessimistic
    intent: Intent
    collision_prob: float
    ttc: float
    risk_score: float
    validated: bool = False


@dataclass
class TrainState:
    """
    Current train dynamics.
    """
    position: Tuple[float, float, float]  # (x, y, z)
    velocity: Tuple[float, float, float]  # (vx, vy, vz)
    acceleration: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    heading: float = 0.0                   # Heading angle (radians)
    speed: float = 0.0                     # Scalar speed (m/s)


@dataclass
class BehaviorInput:
    """Input to Engine 3."""
    tracks: List
    train_state: TrainState
    danger_zones: List = field(default_factory=list)
    scene_context: str = 'OPEN_TRACK'
    optical_flow: Optional[object] = None


@dataclass 
class BehaviorOutput:
    """Output from Engine 3."""
    predictions: List[Prediction]
    risk_scores: Dict[int, float]
    ttc: TTCResult
    safety_margin: float
    validation_status: str
