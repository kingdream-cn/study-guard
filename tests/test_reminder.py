"""Tests for reminder timers and anomaly mapping (reminder.py)."""

from pathlib import Path

import pytest

from config import AppConfig
from metrics import DistanceCategory, FrameMetrics
from reminder import ReminderManager, ReminderType

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = PROJECT_ROOT / "configs" / "default.json"


class FakeClock:
    def __init__(self) -> None:
        self.t = 0.0

    def __call__(self) -> float:
        return self.t

    def advance(self, seconds: float) -> None:
        self.t += seconds


def _manager(clock: FakeClock) -> ReminderManager:
    return ReminderManager(AppConfig(CONFIG_PATH), clock=clock)


def _metrics(
    face: bool = True,
    category: DistanceCategory = DistanceCategory.NORMAL,
    posture: float = 0.9,
    distance: float = 50.0,
) -> FrameMetrics:
    return FrameMetrics(
        timestamp=0.0,
        distance_cm=distance if face else None,
        distance_category=category if face else DistanceCategory.UNKNOWN,
        posture_score=posture if face else 0.0,
        brightness_level=3,
        face_detected=face,
        face_box=None,
    )


def test_eye_care_reminder_triggers():
    clock = FakeClock()
    manager = _manager(clock)
    manager.update(_metrics())
    clock.advance(20 * 60)
    events = manager.update(_metrics())
    assert any(e.reminder_type is ReminderType.EYE_CARE_20_20 for e in events)


def test_eye_care_reminder_not_premature():
    clock = FakeClock()
    manager = _manager(clock)
    manager.update(_metrics())
    clock.advance(19 * 60)
    events = manager.update(_metrics())
    assert all(e.reminder_type is not ReminderType.EYE_CARE_20_20 for e in events)


def test_sedentary_reminder_triggers():
    clock = FakeClock()
    manager = _manager(clock)
    manager.update(_metrics())
    clock.advance(45 * 60)
    events = manager.update(_metrics())
    assert any(e.reminder_type is ReminderType.SEDENTARY for e in events)


def test_pause_freezes_timers():
    clock = FakeClock()
    manager = _manager(clock)
    manager.update(_metrics())
    clock.advance(10 * 60)
    manager.update(_metrics())
    assert manager.effective_study_time == pytest.approx(600.0)

    manager.pause()
    clock.advance(30 * 60)
    manager.resume()
    clock.advance(1)
    manager.update(_metrics())
    assert manager.effective_study_time == pytest.approx(601.0)


def test_face_lost_excluded_from_study_time():
    clock = FakeClock()
    manager = _manager(clock)
    manager.update(_metrics())
    clock.advance(100)
    manager.update(_metrics())
    assert manager.effective_study_time == pytest.approx(100.0)

    clock.advance(300)
    manager.update(_metrics(face=False))
    assert manager.effective_study_time == pytest.approx(100.0)
    assert manager.session_elapsed_time == pytest.approx(400.0)


def test_face_lost_warning_and_recovery():
    clock = FakeClock()
    manager = _manager(clock)
    manager.update(_metrics(face=False))
    clock.advance(11)
    events = manager.update(_metrics(face=False))
    assert any(e.reminder_type is ReminderType.FACE_LOST for e in events)
    assert "face_lost" in manager.active_warnings()

    clock.advance(1)
    manager.update(_metrics(face=True))
    assert "face_lost" not in manager.active_warnings()


def test_distance_warning_after_threshold():
    clock = FakeClock()
    manager = _manager(clock)
    manager.update(_metrics(category=DistanceCategory.TOO_CLOSE, distance=20.0))
    clock.advance(3)
    events = manager.update(
        _metrics(category=DistanceCategory.TOO_CLOSE, distance=20.0)
    )
    assert any(e.reminder_type is ReminderType.DISTANCE_WARNING for e in events)


def test_posture_warning_after_threshold():
    clock = FakeClock()
    manager = _manager(clock)
    manager.update(_metrics(posture=0.2))
    clock.advance(8)
    events = manager.update(_metrics(posture=0.2))
    assert any(e.reminder_type is ReminderType.POSTURE_WARNING for e in events)
