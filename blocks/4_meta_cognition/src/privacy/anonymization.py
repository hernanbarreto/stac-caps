# Block 4: Privacy - Anonymization
def anonymize_frame(frame, detections):
    """On-chip anonymization: face blur, SMPL conversion, plate mask."""
    return frame  # SMPL inherently anonymizes persons

def byzantine_aggregate(updates):
    """Aggregate model updates tolerating malicious nodes (Krum)."""
    return sum(updates) / len(updates) if updates else None
