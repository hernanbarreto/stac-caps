# STAC-CAPS Test Configuration

import sys
from pathlib import Path

import pytest

# Add project root to path
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "blocks"))


# Fixtures

@pytest.fixture
def sample_frame():
    """Sample frame for testing (720p)."""
    import numpy as np
    return np.zeros((720, 1280, 3), dtype=np.uint8)


@pytest.fixture
def sample_detections():
    """Sample detections for testing."""
    return [
        {"bbox": [100, 200, 200, 400], "category": "PERSON", "confidence": 0.9},
        {"bbox": [500, 300, 600, 500], "category": "KNOWN", "confidence": 0.85},
    ]


@pytest.fixture
def sample_tracks():
    """Sample tracks for testing."""
    return [
        {"track_id": 1, "bbox": [100, 200, 200, 400], "velocity": (0, 0, 5)},
        {"track_id": 2, "bbox": [500, 300, 600, 500], "velocity": (0, 0, 2)},
    ]


@pytest.fixture
def calibration_nominal():
    """Calibration for nominal mode."""
    return {
        "left_rail": [(100, 500), (100, 100)],
        "right_rail": [(200, 500), (200, 100)],
        "track_gauge_mm": 1435
    }


@pytest.fixture
def mock_model_manager(mocker):
    """Mock model manager to avoid downloads in tests."""
    mock = mocker.patch("webapp.core.model_manager.ModelManager")
    mock.return_value.get_status.return_value = {
        "depth_anything_v2": {"downloaded": True},
        "rt_detr": {"downloaded": True},
        "rtmpose": {"downloaded": True},
        "osnet": {"downloaded": True}
    }
    return mock
