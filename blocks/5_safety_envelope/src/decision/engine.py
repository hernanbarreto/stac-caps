# Block 5: Decision Engine
from ..interfaces import Action

def decide_action(effective_ttc, max_risk, critical_count, validation_status):
    """Determine action based on TTC and risk."""
    if effective_ttc < 1.0 or critical_count >= 3:
        return Action.EMERGENCY_BRAKE
    if effective_ttc < 2.0 and max_risk > 0.8:
        return Action.SERVICE_BRAKE
    if effective_ttc < 3.0:
        return Action.WARNING
    if effective_ttc < 5.0 or validation_status == 'UNCERTAIN':
        return Action.CAUTION
    return Action.CLEAR
