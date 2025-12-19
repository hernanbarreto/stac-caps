# Engine 3: Theory of Mind - Intent Inference
# Bayesian intent inference with context and smoothing

from typing import Dict, List, Optional
import numpy as np

from ..interfaces import Intent
from .priors import get_context_priors
from .smoothing import smooth_intent

INTENT_STATES = ['STATIC', 'LEAVING', 'APPROACHING', 'CROSSING']


def infer_intent_v2(
    track,
    smpl_params: Optional[Dict],
    context: str,
    intent_history: List[Intent],
    train_state = None
) -> Intent:
    """
    Improved ToM with context priors and temporal smoothing.
    
    Args:
        track: Track with velocity, category
        smpl_params: Optional SMPL parameters
        context: Scene context (PLATFORM | CROSSING | OPEN_TRACK)
        intent_history: Previous intent inferences
        train_state: Train dynamics for gaze awareness
        
    Returns:
        Smoothed Intent
    """
    # Get context-adaptive priors
    priors = get_context_priors(context)
    
    # Observations
    velocity = track.velocity if hasattr(track, 'velocity') else (0, 0, 0)
    velocity_mag = np.linalg.norm(velocity)
    
    facing_track = is_facing_track(smpl_params) if smpl_params else 0.5
    moving_towards = is_moving_towards_track(velocity)
    
    # Distraction detection
    distraction_prob = compute_distraction(smpl_params, track)
    
    # Awareness check
    awareness_prob = compute_gaze_awareness(smpl_params, train_state)
    
    # Update posteriors with Bayesian inference
    posteriors = update_bayesian(priors, {
        'velocity': velocity_mag,
        'facing': facing_track,
        'moving_towards': moving_towards,
        'distracted': distraction_prob
    })
    
    # Create raw intent
    state = max(posteriors, key=posteriors.get)
    raw_intent = Intent(
        state=state,
        distraction_prob=distraction_prob,
        awareness_prob=awareness_prob,
        action_confidence=posteriors[state],
        probs=posteriors,
        smoothed=False
    )
    
    # Apply temporal smoothing
    return smooth_intent(raw_intent, intent_history, alpha=0.7)


def is_facing_track(smpl_params: Dict) -> float:
    """Check if person is facing towards the track."""
    if smpl_params is None:
        return 0.5
    
    body_pose = smpl_params.get('body_pose', np.zeros(72))
    # Simplified: check Y rotation
    facing_angle = body_pose[1] if len(body_pose) > 1 else 0
    
    # Near 0 or π means facing track
    return 1.0 - abs(facing_angle % np.pi) / np.pi


def is_moving_towards_track(velocity) -> float:
    """Check if velocity points towards track."""
    vx, vy, vz = velocity
    
    # Negative Z = moving towards camera/track
    if vz < -0.1:
        return 1.0
    elif vz > 0.1:
        return 0.0
    return 0.5


def compute_distraction(smpl_params: Optional[Dict], track) -> float:
    """
    Compute distraction probability from pose indicators.
    """
    if smpl_params is None:
        return 0.3  # Default moderate distraction
    
    head_down = is_head_down(smpl_params)
    arms_at_ears = has_arms_at_ears(smpl_params)
    irregular_gait = 0.0  # TODO: from track history
    carrying_object = 0.0  # TODO: from pose
    
    distraction_prob = (
        0.25 * head_down +
        0.25 * arms_at_ears +
        0.25 * irregular_gait +
        0.25 * carrying_object
    )
    
    return distraction_prob


def is_head_down(smpl_params: Dict) -> float:
    """Check if head is tilted down (looking at phone)."""
    body_pose = smpl_params.get('body_pose', np.zeros(72))
    # Head pose is typically indices 15-17 in body_pose
    if len(body_pose) > 15:
        head_tilt = body_pose[15]
        return 1.0 if head_tilt > 0.3 else 0.0
    return 0.0


def has_arms_at_ears(smpl_params: Dict) -> float:
    """Check if arms are raised to ears (phone call)."""
    body_pose = smpl_params.get('body_pose', np.zeros(72))
    # Arm poses are indices 48-53 (left) and 54-59 (right)
    # Simplified check
    return 0.0


def compute_gaze_awareness(smpl_params: Optional[Dict], train_state) -> float:
    """
    Compute probability that person is aware of train.
    """
    if smpl_params is None:
        return 0.5
    
    # Check if head is facing train direction
    facing = is_facing_track(smpl_params)
    head_down = is_head_down(smpl_params)
    
    awareness = facing * (1.0 - head_down)
    return awareness


def update_bayesian(priors: Dict[str, float], observations: Dict) -> Dict[str, float]:
    """
    Update priors with observations using Bayesian inference.
    """
    posteriors = priors.copy()
    
    velocity = observations.get('velocity', 0)
    facing = observations.get('facing', 0.5)
    moving_towards = observations.get('moving_towards', 0.5)
    distracted = observations.get('distracted', 0)
    
    # Static: low velocity
    if velocity < 0.1:
        posteriors['STATIC'] *= 2.0
        posteriors['CROSSING'] *= 0.5
    
    # Approaching: moving towards track
    if moving_towards > 0.7:
        posteriors['APPROACHING'] *= 2.0
        posteriors['LEAVING'] *= 0.3
    
    # Leaving: moving away
    if moving_towards < 0.3:
        posteriors['LEAVING'] *= 2.0
        posteriors['APPROACHING'] *= 0.3
    
    # Crossing: high velocity + facing track
    if velocity > 0.5 and facing > 0.7:
        posteriors['CROSSING'] *= 2.0
    
    # Normalize
    total = sum(posteriors.values())
    return {k: v/total for k, v in posteriors.items()}
