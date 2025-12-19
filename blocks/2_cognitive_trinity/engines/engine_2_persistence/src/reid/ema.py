# Engine 2: EMA Embedding Update
# Exponential Moving Average for stable appearance model

import numpy as np


def update_embedding(
    current_embedding: np.ndarray,
    new_embedding: np.ndarray,
    alpha: float = 0.7
) -> np.ndarray:
    """
    Update embedding with EMA for temporal stability.
    
    Args:
        current_embedding: Existing embedding [512]
        new_embedding: New observation embedding [512]
        alpha: Weight for current (0.7 = favor history)
        
    Returns:
        Updated embedding [512]
    """
    if current_embedding is None or len(current_embedding) == 0:
        return new_embedding.copy()
    
    # EMA update
    updated = alpha * current_embedding + (1 - alpha) * new_embedding
    
    # Re-normalize
    norm = np.linalg.norm(updated)
    if norm > 0:
        updated = updated / norm
    
    return updated


def compute_embedding_confidence(
    current: np.ndarray,
    new: np.ndarray
) -> float:
    """
    Compute confidence based on embedding stability.
    
    High similarity between old and new = stable = high confidence.
    
    Args:
        current: Current embedding
        new: New embedding
        
    Returns:
        Confidence [0, 1]
    """
    if current is None or new is None:
        return 0.5
    
    # Cosine similarity
    dot = np.dot(current, new)
    norm_c = np.linalg.norm(current)
    norm_n = np.linalg.norm(new)
    
    if norm_c * norm_n == 0:
        return 0.5
    
    similarity = dot / (norm_c * norm_n)
    
    # Map similarity [-1, 1] to confidence [0, 1]
    confidence = (similarity + 1) / 2
    
    return confidence
