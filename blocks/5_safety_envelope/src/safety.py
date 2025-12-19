# Block 5: Safety Veto - Entry Point
from .interfaces import Action
from .config import SAFETY_PARAMS

class SafetyVeto:
    """Final decision layer: BRAKE/WARNING/CLEAR. Timing: 7ms"""
    def __init__(self):
        self.params = SAFETY_PARAMS
    
    def evaluate(self, ttc_result, risk_scores, validation_status, train_state) -> dict:
        from .evaluator.ttc import evaluate_ttc
        from .aggregator.risk import aggregate_risk
        from .decision.engine import decide_action
        
        effective_ttc, conf = evaluate_ttc(ttc_result, validation_status)
        max_risk, critical = aggregate_risk(risk_scores)
        action = decide_action(effective_ttc, max_risk, critical, validation_status)
        
        if action == Action.EMERGENCY_BRAKE:
            from .hardware.gpio import execute_hardwire_brake
            execute_hardwire_brake()
        
        return {'action': action, 'ttc_used': effective_ttc, 'max_risk': max_risk}
