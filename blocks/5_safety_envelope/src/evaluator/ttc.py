# Block 5: TTC Evaluator
def evaluate_ttc(ttc_result, validation_status):
    """Select appropriate TTC value based on confidence."""
    if validation_status == 'UNCERTAIN' or ttc_result.confidence < 0.7:
        return ttc_result.min, 0.5
    return ttc_result.mean, ttc_result.confidence
