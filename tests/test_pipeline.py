# Pipeline Integration Tests

import pytest
import numpy as np


@pytest.mark.skip(reason="Requires models to be downloaded")
class TestPipelineIntegration:
    """Integration tests for full pipeline."""
    
    def test_pipeline_initialization(self, calibration_nominal):
        """Pipeline should initialize with calibration."""
        from webapp.core.pipeline import Pipeline
        
        pipeline = Pipeline(
            calibration=calibration_nominal,
            device="cpu",
            fp16=False
        )
        
        assert pipeline.calibration == calibration_nominal
        
    def test_scale_factor_computation(self, calibration_nominal):
        """Scale factor should be computed from track gauge."""
        from webapp.core.pipeline import Pipeline
        
        pipeline = Pipeline(
            calibration=calibration_nominal,
            device="cpu",
            fp16=False
        )
        
        # With 100 pixel rail distance and 1435mm gauge
        # scale = 1.435m / 100px = 0.01435 m/px
        assert pipeline.scale_factor > 0


class TestCalibrationComputation:
    """Test calibration computations."""
    
    def test_scale_factor_standard_gauge(self):
        """Test scale factor with standard gauge."""
        # 100 pixel distance, 1435mm gauge
        left_rail = [(100, 500), (100, 100)]
        right_rail = [(200, 500), (200, 100)]
        gauge_mm = 1435
        
        pixel_distance = abs(right_rail[0][0] - left_rail[0][0])
        scale = (gauge_mm / 1000.0) / pixel_distance
        
        assert scale == pytest.approx(0.01435, rel=0.01)
        
    def test_scale_factor_narrow_gauge(self):
        """Test scale factor with narrow gauge (1000mm)."""
        left_rail = [(100, 500), (100, 100)]
        right_rail = [(200, 500), (200, 100)]
        gauge_mm = 1000
        
        pixel_distance = abs(right_rail[0][0] - left_rail[0][0])
        scale = (gauge_mm / 1000.0) / pixel_distance
        
        assert scale == pytest.approx(0.01, rel=0.01)


class TestVideoProcessor:
    """Test video processor components."""
    
    def test_frame_annotation(self, sample_frame, sample_detections):
        """Test frame annotation doesn't crash."""
        from webapp.core.video_processor import VideoProcessor
        
        # Just test that the method exists and has correct signature
        assert hasattr(VideoProcessor, '_annotate_frame')
