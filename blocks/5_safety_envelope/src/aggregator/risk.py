# Block 5: Risk Aggregator
def aggregate_risk(risk_scores):
    """Aggregate risk across all tracks."""
    if not risk_scores:
        return 0.0, 0
    max_risk = max(risk_scores.values())
    critical = sum(1 for r in risk_scores.values() if r > 0.8)
    return max_risk, critical
