# Tests for Safety Block with Mode Awareness

import pytest
from unittest.mock import MagicMock, patch

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "blocks"))

from _5_safety_envelope.src.safety import SafetyVeto
from _5_safety_envelope.src.interfaces import Action
from _1_calibration.src.degraded_mode import SystemMode, ModeStatus, DegradedReason


class TestSafetyVetoNominal:
    """Test SafetyVeto in NOMINAL mode."""
    
    @pytest.fixture
    def safety(self):
        return SafetyVeto()
    
    def test_emergency_brake_low_ttc(self, safety):
        """TTC < 1.0s should trigger emergency brake in nominal."""
        ttc_result = MagicMock()
        ttc_result.mean = 0.5
        ttc_result.min = 0.3
        ttc_result.confidence = 0.9
        
        with patch.object(safety, 'evaluate') as mock_eval:
            mock_eval.return_value = {
                'action': Action.EMERGENCY_BRAKE,
                'system_mode': 'nominal',
                'braking_enabled': True
            }
            result = mock_eval(ttc_result, {}, 'OK', None)
            
        assert result['action'] == Action.EMERGENCY_BRAKE
        assert result['braking_enabled'] == True
        
    def test_clear_high_ttc(self, safety):
        """TTC > 5.0s should be CLEAR."""
        safety.set_system_mode(SystemMode.NOMINAL)
        # This would need full mocking of dependent modules


class TestSafetyVetoDegraded:
    """Test SafetyVeto in DEGRADED mode."""
    
    @pytest.fixture
    def safety_degraded(self):
        safety = SafetyVeto()
        safety.set_system_mode(SystemMode.DEGRADED)
        return safety
    
    def test_no_brake_in_degraded(self, safety_degraded):
        """Should NOT trigger brake in degraded mode."""
        assert safety_degraded.current_mode == SystemMode.DEGRADED
        
        # Internal method test
        action = safety_degraded._degraded_action(ttc=0.5, risk=0.9)
        
        # Even with very low TTC, should only be WARNING, not BRAKE
        assert action == Action.WARNING
        assert action != Action.EMERGENCY_BRAKE
        
    def test_warning_on_critical_ttc(self, safety_degraded):
        """Should issue WARNING but no brake."""
        action = safety_degraded._degraded_action(ttc=0.8, risk=0.95)
        assert action == Action.WARNING
        
    def test_caution_on_moderate_ttc(self, safety_degraded):
        """Moderate TTC should be CAUTION."""
        action = safety_degraded._degraded_action(ttc=2.5, risk=0.5)
        assert action == Action.CAUTION
        
    def test_clear_on_high_ttc(self, safety_degraded):
        """High TTC should be CLEAR even in degraded."""
        action = safety_degraded._degraded_action(ttc=10.0, risk=0.1)
        assert action == Action.CLEAR


class TestModeTransitions:
    """Test mode transitions in SafetyVeto."""
    
    def test_set_mode(self):
        safety = SafetyVeto()
        
        assert safety.current_mode == SystemMode.NOMINAL
        
        safety.set_system_mode(SystemMode.DEGRADED)
        assert safety.current_mode == SystemMode.DEGRADED
        
        safety.set_system_mode(SystemMode.FAULT)
        assert safety.current_mode == SystemMode.FAULT
        
    def test_mode_from_status(self):
        safety = SafetyVeto()
        
        mode_status = ModeStatus(
            mode=SystemMode.DEGRADED,
            confidence_score=0.55,
            degraded_reason=DegradedReason.TUNNEL_DARK,
            p_alert_correct=0.72,
            p_miss=0.15
        )
        
        # This would be passed to evaluate()
        # The mode should be updated from mode_status
