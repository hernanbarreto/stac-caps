# Engine 3: Context-Adaptive Priors
# Scene context affects intent priors

from typing import Dict


CONTEXT_PRIORS = {
    'LEVEL_CROSSING': {
        'STATIC': 0.25,
        'LEAVING': 0.25,
        'APPROACHING': 0.25,
        'CROSSING': 0.25  # Higher chance at crossings
    },
    'PLATFORM': {
        'STATIC': 0.55,
        'LEAVING': 0.25,
        'APPROACHING': 0.15,
        'CROSSING': 0.05  # Lower chance on platforms
    },
    'OPEN_TRACK': {
        'STATIC': 0.40,
        'LEAVING': 0.30,
        'APPROACHING': 0.20,
        'CROSSING': 0.10
    },
    'CROSSING': {  # Alias for level crossing
        'STATIC': 0.25,
        'LEAVING': 0.25,
        'APPROACHING': 0.25,
        'CROSSING': 0.25
    }
}


def get_context_priors(scene_context: str) -> Dict[str, float]:
    """
    Get adaptive priors based on scene context.
    
    Args:
        scene_context: LEVEL_CROSSING | PLATFORM | OPEN_TRACK
        
    Returns:
        Prior probabilities for each intent state
    """
    return CONTEXT_PRIORS.get(scene_context, CONTEXT_PRIORS['OPEN_TRACK'])
