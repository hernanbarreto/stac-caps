# Block 5: Safety Veto - Entry Point
# Respects SystemMode for fail-safe operation

from typing import Optional
from .interfaces import Action
from .config import SAFETY_PARAMS

# Import SystemMode from calibration block
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
try:
    from blocks._1_calibration.src.degraded_mode import SystemMode, ModeStatus
except ImportError:
    # Fallback definition
    from enum import Enum
    class SystemMode(Enum):
        NOMINAL = "nominal"
        DEGRADED = "degraded"
        FAULT = "fault"
    ModeStatus = None


class SafetyVeto:
    """
    Final decision layer: BRAKE/WARNING/CLEAR.
    
    Respects SystemMode:
    - NOMINAL: Full automatic braking enabled
    - DEGRADED: Visual/audio alerts only, NO automatic braking
    - FAULT: Manual control required
    
    Timing: 7ms
    """
    
    def __init__(self):
        self.params = SAFETY_PARAMS
        self.current_mode = SystemMode.NOMINAL
    
    def set_system_mode(self, mode: SystemMode):
        """Set current system mode (from calibration block)."""
        self.current_mode = mode
    
    def evaluate(
        self,
        ttc_result,
        risk_scores,
        validation_status,
        train_state,
        mode_status: Optional[ModeStatus] = None
    ) -> dict:
        """
        Evaluate safety decision respecting system mode.
        
        Args:
            ttc_result: TTC calculation result
            risk_scores: Risk scores per track
            validation_status: Validation status
            train_state: Current train state
            mode_status: Optional ModeStatus from calibration
            
        Returns:
            dict with action, ttc, risk, and mode info
        """
        from .evaluator.ttc import evaluate_ttc
        from .aggregator.risk import aggregate_risk
        from .decision.engine import decide_action
        
        # Update mode if provided
        if mode_status:
            self.current_mode = mode_status.mode
        
        effective_ttc, conf = evaluate_ttc(ttc_result, validation_status)
        max_risk, critical = aggregate_risk(risk_scores)
        
        # Determine action based on mode
        if self.current_mode == SystemMode.NOMINAL:
            # Full functionality
            action = decide_action(effective_ttc, max_risk, critical, validation_status)
            
            if action == Action.EMERGENCY_BRAKE:
                from .hardware.gpio import execute_hardwire_brake
                execute_hardwire_brake()
                
        elif self.current_mode == SystemMode.DEGRADED:
            # NO automatic braking, only alerts
            action = self._degraded_action(effective_ttc, max_risk)
            
        else:  # FAULT
            # Manual control only
            action = Action.CLEAR  # Let operator decide
        
        result = {
            'action': action,
            'ttc_used': effective_ttc,
            'max_risk': max_risk,
            'system_mode': self.current_mode.value,
            'braking_enabled': self.current_mode == SystemMode.NOMINAL
        }
        
        # Add mode probabilities if in degraded
        if mode_status and self.current_mode == SystemMode.DEGRADED:
            result['P_alert_correct'] = mode_status.p_alert_correct
            result['P_miss'] = mode_status.p_miss
            result['degraded_reason'] = mode_status.degraded_reason.value
            result['recommendation'] = mode_status.recommendation
        
        return result
    
    def _degraded_action(self, ttc: float, risk: float) -> Action:
        """
        Determine action in degraded mode.
        Only visual/audio alerts, NO braking.
        """
        if ttc < 1.0:
            return Action.WARNING  # Urgent alert but NO brake
        elif ttc < 2.0:
            return Action.WARNING
        elif ttc < 3.0:
            return Action.CAUTION
        else:
            return Action.CLEAR
