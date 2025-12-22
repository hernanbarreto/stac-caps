# Tests for Degraded Mode System

import pytest
from blocks._1_calibration.src.degraded_mode import (
    SystemMode,
    DegradedReason,
    ModeStatus,
    DegradedModeDetector
)


class TestSystemMode:
    """Test SystemMode enum."""
    
    def test_modes_exist(self):
        assert SystemMode.NOMINAL.value == "nominal"
        assert SystemMode.DEGRADED.value == "degraded"
        assert SystemMode.FAULT.value == "fault"


class TestModeStatus:
    """Test ModeStatus dataclass."""
    
    def test_nominal_status(self):
        status = ModeStatus(
            mode=SystemMode.NOMINAL,
            confidence_score=0.95
        )
        assert status.p_miss == 0.0
        assert status.p_alert_correct == 1.0
        
    def test_degraded_status(self):
        status = ModeStatus(
            mode=SystemMode.DEGRADED,
            confidence_score=0.55,
            degraded_reason=DegradedReason.TUNNEL_DARK,
            p_alert_correct=0.72,
            p_miss=0.15
        )
        assert status.p_miss == 0.15
        assert status.degraded_reason == DegradedReason.TUNNEL_DARK
        
    def test_to_dict(self):
        status = ModeStatus(
            mode=SystemMode.DEGRADED,
            confidence_score=0.55,
            degraded_reason=DegradedReason.RAIL_SWITCH,
            p_alert_correct=0.70,
            p_miss=0.20
        )
        d = status.to_dict()
        assert d["mode"] == "degraded"
        assert d["P_miss"] == 0.20
        assert d["degraded_reason"] == "rail_switch"


class TestDegradedModeDetector:
    """Test DegradedModeDetector class."""
    
    def test_nominal_mode_high_confidence(self):
        detector = DegradedModeDetector()
        status = detector.update(
            rail_visibility=0.95,
            calibration_confidence=0.90,
            depth_confidence=0.88,
            detection_confidence=0.92
        )
        assert status.mode == SystemMode.NOMINAL
        assert status.p_miss < 0.01
        
    def test_degraded_mode_low_rail_visibility(self):
        detector = DegradedModeDetector()
        # Simulate tunnel entry
        for _ in range(5):
            status = detector.update(
                rail_visibility=0.30,  # Low
                calibration_confidence=0.60,
                depth_confidence=0.70,
                detection_confidence=0.75
            )
        assert status.mode == SystemMode.DEGRADED
        assert status.p_miss > 0.05
        assert status.degraded_reason in [
            DegradedReason.RAIL_OCCLUSION,
            DegradedReason.TUNNEL_DARK
        ]
        
    def test_fault_mode_very_low_confidence(self):
        detector = DegradedModeDetector()
        # Simulate complete failure
        for _ in range(10):
            status = detector.update(
                rail_visibility=0.10,
                calibration_confidence=0.15,
                depth_confidence=0.20,
                detection_confidence=0.25
            )
        assert status.mode == SystemMode.FAULT
        assert status.p_miss > 0.30
        assert status.recommendation == "MANUAL_CONTROL_REQUIRED"
        
    def test_mode_transition_nominal_to_degraded(self):
        detector = DegradedModeDetector()
        
        # Start nominal
        for _ in range(10):
            status = detector.update(0.95, 0.90, 0.88, 0.92)
        assert status.mode == SystemMode.NOMINAL
        
        # Enter tunnel (gradual drop)
        for i in range(15):
            conf = 0.95 - (i * 0.05)
            status = detector.update(conf, conf, conf, conf)
        
        # Should now be degraded
        assert status.mode == SystemMode.DEGRADED
        
    def test_recovery_to_nominal(self):
        detector = DegradedModeDetector()
        
        # Start degraded
        for _ in range(10):
            detector.update(0.50, 0.50, 0.50, 0.50)
        
        # Recovery
        for _ in range(15):
            status = detector.update(0.90, 0.90, 0.90, 0.90)
        
        # Should recover to nominal
        assert status.mode == SystemMode.NOMINAL
        
    def test_reset(self):
        detector = DegradedModeDetector()
        
        # Fill history
        for _ in range(20):
            detector.update(0.50, 0.50, 0.50, 0.50)
        
        assert len(detector.confidence_history) > 0
        
        detector.reset()
        assert len(detector.confidence_history) == 0
