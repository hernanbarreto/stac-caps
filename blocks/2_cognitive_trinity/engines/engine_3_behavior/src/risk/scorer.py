# Engine 3: Risk Score Calculator
# Multi-factor risk scoring with quality and temporal smoothing

from typing import Optional
import numpy as np

from ..interfaces import Intent, TTCResult


def compute_risk_score_v2(
    track,
    intent: Intent,
    ttc_result: TTCResult,
    prev_risk: Optional[float] = None
) -> float:
    """
    Improved risk scoring with quality and smoothing.
    
    Factors:
    - TTC (35%): Lower TTC = higher risk
    - Intent (25%): Crossing/approaching = higher
    - Distraction (15%): Distracted = higher
    - Category (10%): Person > Known > Unknown
    - Quality (15%): Low quality = higher uncertainty = higher
    
    Args:
        track: Track with category, quality_score
        intent: Inferred intent
        ttc_result: TTC with confidence
        prev_risk: Previous frame's risk score
        
    Returns:
        Risk score [0.0, 1.0]
    """
    # TTC factor (use conservative min)
    ttc = ttc_result.min if ttc_result else float('inf')
    if ttc == float('inf'):
        ttc_factor = 0.0
    else:
        ttc_factor = 1.0 - min(ttc / 10.0, 1.0)
    
    # Intent factor
    intent_weights = {
        'STATIC': 0.1,
        'LEAVING': 0.2,
        'APPROACHING': 0.7,
        'CROSSING': 1.0
    }
    intent_state = intent.state if intent else 'STATIC'
    intent_factor = intent_weights.get(intent_state, 0.5)
    
    # Distraction factor
    distraction_factor = intent.distraction_prob if intent else 0.0
    
    # Category factor
    category_weights = {
        'PERSON': 1.0,
        'KNOWN': 0.7,
        'UNKNOWN': 0.3
    }
    category = track.category if hasattr(track, 'category') else 'UNKNOWN'
    if hasattr(category, 'value'):
        category = category.value
    category_factor = category_weights.get(str(category), 0.5)
    
    # Quality factor (low quality = less certain = higher risk)
    quality_score = track.quality_score if hasattr(track, 'quality_score') else 0.5
    quality_factor = 1.0 - quality_score
    
    # Weighted combination
    raw_risk = (
        0.35 * ttc_factor +
        0.25 * intent_factor +
        0.15 * distraction_factor +
        0.10 * category_factor +
        0.15 * quality_factor
    )
    
    # Modulate by TTC confidence (low confidence = higher risk)
    confidence = ttc_result.confidence if ttc_result else 1.0
    confidence_adjusted = raw_risk * (2.0 - confidence)
    
    # Temporal smoothing
    if prev_risk is not None:
        final_risk = 0.7 * confidence_adjusted + 0.3 * prev_risk
    else:
        final_risk = confidence_adjusted
    
    return float(np.clip(final_risk, 0, 1))
