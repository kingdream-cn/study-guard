"""Tests for frame metrics and anomaly tracking (metrics.py)."""

import numpy as np
import pytest

from calibrator import DistanceCalibrator
from detector import FaceBox
from metrics import (
    AnomalyTracker,
    DistanceCategory,
    FrameMetrics,
    MetricsCalculator,
)


def _calculator() -> MetricsCalculator:
    return MetricsCalculator(DistanceCalibrator())


def _frame(brightness: int = 0, height: int = 480, width: int = 640) -> np.ndarray:
    return np.full((height, width, 3), brightness, dtype=np.uint8)


# --- distance category ---


def test_distance_category_too_close():
    assert _calculator().classify_distance(20.0) is DistanceCategory.TOO_CLOSE


def test_distance_category_normal():
    assert _calculator().classify_distance(50.0) is DistanceCategory.NORMAL


def test_distance_category_too_far():
    assert _calculator().classify_distance(90.0) is DistanceCategory.TOO_FAR


def test_distance_category_no_face():
    assert _calculator().classify_distance(None) is DistanceCategory.UNKNOWN


# --- posture score ---


def test_posture_score_ideal():
    calculator = _calculator()
    # center y = 142 + 100/2 = 192 (= 0.4 * 480); width 160 (= 0.25 * 640)
    face = FaceBox(100, 142, 160, 100)
    metrics = calculator.compute(_frame(), [face])
    assert metrics.posture_score == pytest.approx(1.0, abs=0.01)


def test_posture_score_bad_position():
    calculator = _calculator()
    face = FaceBox(0, 0, 20, 20)  # tiny face at top-left corner
    metrics = calculator.compute(_frame(), [face])
    assert metrics.posture_score == pytest.approx(0.0, abs=0.05)


def test_posture_score_no_face():
    metrics = _calculator().compute(_frame(), [])
    assert metrics.posture_score == 0.0
    assert metrics.face_detected is False


# --- brightness level ---


def test_brightness_level_dark():
    metrics = _calculator().compute(_frame(brightness=0), [])
    assert metrics.brightness_level in (1, 2)


def test_brightness_level_bright():
    metrics = _calculator().compute(_frame(brightness=255), [])
    assert metrics.brightness_level in (4, 5)


# --- frame metrics dataclass ---


def test_frame_metrics_fields():
    face = FaceBox(10, 20, 100, 80)
    metrics = _calculator().compute(_frame(brightness=128), [face])

    assert isinstance(metrics, FrameMetrics)
    assert metrics.face_detected is True
    assert metrics.face_box == face
    assert metrics.distance_cm is None  # calibrator not fitted
    assert metrics.distance_category is DistanceCategory.UNKNOWN
    assert 0.0 <= metrics.posture_score <= 1.0
    assert 1 <= metrics.brightness_level <= 5


# --- anomaly tracker ---


class _FakeClock:
    def __init__(self) -> None:
        self.t = 0.0

    def __call__(self) -> float:
        return self.t

    def advance(self, seconds: float) -> None:
        self.t += seconds


def test_anomaly_duration_tracking():
    clock = _FakeClock()
    tracker = AnomalyTracker(clock=clock)

    assert tracker.update("posture", True, 10.0, 60.0) is False
    clock.advance(9)
    assert tracker.update("posture", True, 10.0, 60.0) is False
    clock.advance(1)
    assert tracker.update("posture", True, 10.0, 60.0) is True


def test_anomaly_cooldown():
    clock = _FakeClock()
    tracker = AnomalyTracker(clock=clock)

    tracker.update("posture", True, 10.0, 60.0)
    clock.advance(10)
    assert tracker.update("posture", True, 10.0, 60.0) is True  # trigger at t=10

    clock.advance(30)  # t=40, still within 60s cooldown
    assert tracker.update("posture", True, 10.0, 60.0) is False

    clock.advance(10)  # t=50
    tracker.update("posture", False, 10.0, 60.0)  # recover
    clock.advance(1)  # t=51, still within cooldown
    assert tracker.update("posture", True, 10.0, 60.0) is False


def test_anomaly_recovery():
    clock = _FakeClock()
    tracker = AnomalyTracker(clock=clock)

    tracker.update("posture", True, 10.0, 60.0)
    clock.advance(10)
    assert tracker.update("posture", True, 10.0, 60.0) is True  # trigger at t=10

    clock.advance(5)  # t=15
    tracker.update("posture", False, 10.0, 60.0)  # recover

    clock.advance(65)  # t=80, after cooldown (trigger at 10 + 60)
    tracker.update("posture", True, 10.0, 60.0)  # start new streak
    clock.advance(10)  # t=90
    assert tracker.update("posture", True, 10.0, 60.0) is True
