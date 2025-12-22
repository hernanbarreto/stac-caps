# Block 1: Calibration - System Mode and Degraded Detection

from enum import Enum
from dataclasses import dataclass
from typing import Optional


class SystemMode(Enum):
    """
    System operating modes for fail-safe design.
    
    NOMINAL: Full functionality, automatic braking enabled
    DEGRADED: Visual alerts only, no automatic braking
    FAULT: Critical error, operator must take manual control
    """
    NOMINAL = "nominal"
    DEGRADED = "degraded"
    FAULT = "fault"


class DegradedReason(Enum):
    """Reasons for entering degraded mode."""
    NONE = "none"
    TUNNEL_DARK = "tunnel_dark"
    RAIL_SWITCH = "rail_switch"
    RAIL_OCCLUSION = "rail_occlusion"
    LOW_CONTRAST = "low_contrast"
    CURVE_SHARP = "curve_sharp"
    WEATHER_SEVERE = "weather_severe"
    CALIBRATION_DRIFT = "calibration_drift"


@dataclass
class ModeStatus:
    """Current system mode status with probabilities."""
    mode: SystemMode
    confidence_score: float  # 0.0 - 1.0
    degraded_reason: DegradedReason = DegradedReason.NONE
    
    # Critical probabilities in DEGRADED mode
    p_alert_correct: float = 1.0  # P(alert is correct)
    p_miss: float = 0.0           # P(missing real obstacle) - CRITICAL
    
    # Recommendation for operator
    recommendation: str = "NORMAL_OPERATION"
    
    def to_dict(self) -> dict:
        return {
            "mode": self.mode.value,
            "confidence_score": self.confidence_score,
            "degraded_reason": self.degraded_reason.value,
            "P_alert_correct": self.p_alert_correct,
            "P_miss": self.p_miss,
            "recommendation": self.recommendation
        }


class DegradedModeDetector:
    """
    Detects when system should enter degraded mode.
    
    Monitors:
    - Rail visibility confidence
    - Calibration drift
    - Environmental conditions
    
    Outputs probabilities of:
    - Correct alerts (false positive rate)
    - Missed obstacles (false negative rate) - CRITICAL
    """
    
    def __init__(self):
        self.confidence_history = []
        self.max_history = 30  # ~1 second at 30 FPS
        
        # Thresholds
        self.nominal_threshold = 0.80
        self.degraded_threshold = 0.40
    
    def update(
        self,
        rail_visibility: float,
        calibration_confidence: float,
        depth_confidence: float,
        detection_confidence: float
    ) -> ModeStatus:
        """
        Update mode based on current confidence scores.
        
        Args:
            rail_visibility: 0-1, how well rails are visible
            calibration_confidence: 0-1, calibration confidence
            depth_confidence: 0-1, depth estimation confidence
            detection_confidence: 0-1, detection confidence
            
        Returns:
            ModeStatus with current mode and probabilities
        """
        # Weighted confidence score
        overall_confidence = (
            rail_visibility * 0.30 +
            calibration_confidence * 0.30 +
            depth_confidence * 0.20 +
            detection_confidence * 0.20
        )
        
        # Track history for smoothing
        self.confidence_history.append(overall_confidence)
        if len(self.confidence_history) > self.max_history:
            self.confidence_history.pop(0)
        
        # Smoothed confidence
        avg_confidence = sum(self.confidence_history) / len(self.confidence_history)
        
        # Determine mode
        if avg_confidence >= self.nominal_threshold:
            mode = SystemMode.NOMINAL
            degraded_reason = DegradedReason.NONE
            p_alert_correct = 0.95
            p_miss = 0.001  # Very low in nominal
            recommendation = "NORMAL_OPERATION"
            
        elif avg_confidence >= self.degraded_threshold:
            mode = SystemMode.DEGRADED
            degraded_reason = self._infer_reason(
                rail_visibility, calibration_confidence, 
                depth_confidence, detection_confidence
            )
            
            # Calculate probabilities based on confidence
            p_alert_correct = 0.50 + (avg_confidence * 0.40)  # 70-90%
            p_miss = 0.05 + (1 - avg_confidence) * 0.20      # 5-25%
            recommendation = "OPERATOR_VIGILANCE_REQUIRED"
            
        else:
            mode = SystemMode.FAULT
            degraded_reason = DegradedReason.CALIBRATION_DRIFT
            p_alert_correct = 0.30
            p_miss = 0.40  # HIGH - critical
            recommendation = "MANUAL_CONTROL_REQUIRED"
        
        return ModeStatus(
            mode=mode,
            confidence_score=avg_confidence,
            degraded_reason=degraded_reason,
            p_alert_correct=p_alert_correct,
            p_miss=p_miss,
            recommendation=recommendation
        )
    
    def _infer_reason(
        self,
        rail_visibility: float,
        calibration_confidence: float,
        depth_confidence: float,
        detection_confidence: float
    ) -> DegradedReason:
        """Infer the most likely reason for degraded mode."""
        
        # Find the lowest confidence factor
        factors = {
            DegradedReason.RAIL_OCCLUSION: rail_visibility,
            DegradedReason.CALIBRATION_DRIFT: calibration_confidence,
            DegradedReason.LOW_CONTRAST: depth_confidence,
            DegradedReason.TUNNEL_DARK: min(rail_visibility, depth_confidence)
        }
        
        return min(factors, key=factors.get)
    
    def reset(self):
        """Reset history (e.g., after operator override)."""
        self.confidence_history.clear()
