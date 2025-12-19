# Engine 3: Temporal Smoothing for Intent
# EMA smoothing to prevent oscillation

from typing import List
from ..interfaces import Intent

INTENT_STATES = ['STATIC', 'LEAVING', 'APPROACHING', 'CROSSING']


def smooth_intent(
    current_intent: Intent,
    intent_history: List[Intent],
    alpha: float = 0.7
) -> Intent:
    """
    Apply temporal smoothing to prevent intent oscillation.
    
    Args:
        current_intent: Current frame's raw intent
        intent_history: Previous intents (up to 5)
        alpha: Weight for current (0.7 = favor new)
        
    Returns:
        Smoothed Intent
    """
    if not intent_history:
        return Intent(
            state=current_intent.state,
            distraction_prob=current_intent.distraction_prob,
            awareness_prob=current_intent.awareness_prob,
            action_confidence=current_intent.action_confidence,
            probs=current_intent.probs,
            smoothed=True
        )
    
    previous = intent_history[-1]
    
    # Smooth probabilities
    smoothed_probs = {}
    for state in INTENT_STATES:
        current_prob = current_intent.probs.get(state, 0)
        prev_prob = previous.probs.get(state, 0)
        smoothed_probs[state] = alpha * current_prob + (1 - alpha) * prev_prob
    
    # Determine smoothed state
    smoothed_state = max(smoothed_probs, key=smoothed_probs.get)
    
    # Smooth distraction
    smoothed_distraction = (
        alpha * current_intent.distraction_prob +
        (1 - alpha) * previous.distraction_prob
    )
    
    return Intent(
        state=smoothed_state,
        distraction_prob=smoothed_distraction,
        awareness_prob=current_intent.awareness_prob,
        action_confidence=smoothed_probs[smoothed_state],
        probs=smoothed_probs,
        smoothed=True
    )
