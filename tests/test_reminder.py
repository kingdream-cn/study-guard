"""Tests for reminder timers and anomaly mapping (reminder.py)."""

from pathlib import Path

import pytest

from config import AppConfig
from metrics import DistanceCategory, FrameMetrics
from reminder import (
    ReminderEvent,
    ReminderManager,
    ReminderType,
    select_banner,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = PROJECT_ROOT / "configs" / "default.json"


class FakeClock:
    def __init__(self) -> None:
        self.t = 0.0

    def __call__(self) -> float:
        return self.t

    def advance(self, seconds: float) -> None:
        self.t += seconds


def _setup(clock: FakeClock) -> tuple[AppConfig, ReminderManager]:
    config = AppConfig(CONFIG_PATH)
    return config, ReminderManager(config, clock=clock)


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
    config, manager = _setup(clock)
    interval = config.get("reminder.eye_care_interval_min") * 60.0

    manager.update(_metrics())
    clock.advance(interval + 1.0)
    events = manager.update(_metrics())
    assert any(e.reminder_type is ReminderType.EYE_CARE_20_20 for e in events)


def test_eye_care_reminder_not_premature():
    clock = FakeClock()
    config, manager = _setup(clock)
    interval = config.get("reminder.eye_care_interval_min") * 60.0

    manager.update(_metrics())
    clock.advance(interval * 0.9)
    events = manager.update(_metrics())
    assert all(e.reminder_type is not ReminderType.EYE_CARE_20_20 for e in events)


def test_sedentary_reminder_triggers():
    clock = FakeClock()
    config, manager = _setup(clock)
    interval = config.get("reminder.sedentary_interval_min") * 60.0

    manager.update(_metrics())
    clock.advance(interval + 1.0)
    events = manager.update(_metrics())
    assert any(e.reminder_type is ReminderType.SEDENTARY for e in events)


def test_pause_freezes_timers():
    clock = FakeClock()
    manager = _setup(clock)[1]
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
    manager = _setup(clock)[1]
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
    config, manager = _setup(clock)
    face_lost_sec = config.get("reminder.face_lost_sec")

    manager.update(_metrics(face=False))
    clock.advance(face_lost_sec + 1.0)
    events = manager.update(_metrics(face=False))
    assert any(e.reminder_type is ReminderType.FACE_LOST for e in events)
    assert "face_lost" in manager.active_warnings()

    clock.advance(1)
    manager.update(_metrics(face=True))
    assert "face_lost" not in manager.active_warnings()


def test_distance_warning_after_threshold():
    clock = FakeClock()
    config, manager = _setup(clock)
    threshold = config.get("reminder.distance_anomaly_threshold_sec")

    manager.update(_metrics(category=DistanceCategory.TOO_CLOSE, distance=20.0))
    clock.advance(threshold + 0.1)
    events = manager.update(
        _metrics(category=DistanceCategory.TOO_CLOSE, distance=20.0)
    )
    assert any(e.reminder_type is ReminderType.DISTANCE_WARNING for e in events)


def test_posture_warning_after_threshold():
    clock = FakeClock()
    config, manager = _setup(clock)
    threshold = config.get("reminder.posture_anomaly_threshold_sec")

    manager.update(_metrics(posture=0.2))
    clock.advance(threshold + 0.1)
    events = manager.update(_metrics(posture=0.2))
    assert any(e.reminder_type is ReminderType.POSTURE_WARNING for e in events)


def test_distance_warning_cross_direction_not_silenced():
    """D1 regression lock: too_far then too_close must each warn.

    Timeline (injected clock):
      0.00  too_far
      3.10  too_far  -> first DISTANCE_WARNING (too far)
      3.15  normal   -> one recovery frame clears the tracking state
      3.15  too_close starts a fresh duration window
      6.25  too_close -> 3.10 s sustained -> second DISTANCE_WARNING (too close)

    Before the D1 fix both directions shared the single ``"distance"`` tracker
    key and its 60 s cooldown, so the second warning was suppressed (the test
    failed); splitting the key must make this pass.
    """
    clock = FakeClock()
    config, manager = _setup(clock)
    threshold = config.get("reminder.distance_anomaly_threshold_sec")

    manager.update(_metrics(category=DistanceCategory.TOO_FAR, distance=100.0))
    clock.advance(threshold + 0.1)
    events = manager.update(
        _metrics(category=DistanceCategory.TOO_FAR, distance=100.0)
    )
    far_events = [
        e for e in events if e.reminder_type is ReminderType.DISTANCE_WARNING
    ]
    assert len(far_events) == 1

    # One normal frame: the non-anomalous side must reset its tracker state.
    clock.advance(0.05)
    manager.update(_metrics(category=DistanceCategory.NORMAL, distance=50.0))

    manager.update(_metrics(category=DistanceCategory.TOO_CLOSE, distance=20.0))
    clock.advance(threshold + 0.1)
    events = manager.update(
        _metrics(category=DistanceCategory.TOO_CLOSE, distance=20.0)
    )
    close_events = [
        e for e in events if e.reminder_type is ReminderType.DISTANCE_WARNING
    ]
    assert len(close_events) == 1


def test_distance_warning_messages_are_directional():
    """Each direction produces its own whole-sentence message."""
    close_clock = FakeClock()
    config, close_manager = _setup(close_clock)
    threshold = config.get("reminder.distance_anomaly_threshold_sec")

    close_manager.update(
        _metrics(category=DistanceCategory.TOO_CLOSE, distance=20.0)
    )
    close_clock.advance(threshold + 0.1)
    close_events = close_manager.update(
        _metrics(category=DistanceCategory.TOO_CLOSE, distance=20.0)
    )
    assert [e.message for e in close_events] == ["Too close — move back"]

    far_clock = FakeClock()
    config, far_manager = _setup(far_clock)
    far_manager.update(_metrics(category=DistanceCategory.TOO_FAR, distance=100.0))
    far_clock.advance(threshold + 0.1)
    far_events = far_manager.update(
        _metrics(category=DistanceCategory.TOO_FAR, distance=100.0)
    )
    assert [e.message for e in far_events] == ["Too far — move closer"]


def test_distance_warning_same_direction_cooldown_still_holds():
    """D1 fix must not disable the 60 s cooldown for the same direction."""
    clock = FakeClock()
    config, manager = _setup(clock)
    threshold = config.get("reminder.distance_anomaly_threshold_sec")
    cooldown = config.get("reminder.cooldown_sec")

    manager.update(_metrics(category=DistanceCategory.TOO_CLOSE, distance=20.0))
    clock.advance(threshold + 0.1)
    first = manager.update(
        _metrics(category=DistanceCategory.TOO_CLOSE, distance=20.0)
    )
    assert any(e.reminder_type is ReminderType.DISTANCE_WARNING for e in first)

    # Brief recovery clears the "triggered" latch but not the cooldown.
    manager.update(_metrics(category=DistanceCategory.NORMAL, distance=50.0))
    manager.update(_metrics(category=DistanceCategory.TOO_CLOSE, distance=20.0))
    clock.advance(threshold + 0.1)
    suppressed = manager.update(
        _metrics(category=DistanceCategory.TOO_CLOSE, distance=20.0)
    )
    assert all(
        e.reminder_type is not ReminderType.DISTANCE_WARNING for e in suppressed
    )

    # Only after the cooldown expires may the same direction warn again; the
    # duration window then restarts from that frame.
    clock.advance(cooldown)
    manager.update(_metrics(category=DistanceCategory.TOO_CLOSE, distance=20.0))
    clock.advance(threshold + 0.1)
    after_cooldown = manager.update(
        _metrics(category=DistanceCategory.TOO_CLOSE, distance=20.0)
    )
    assert any(
        e.reminder_type is ReminderType.DISTANCE_WARNING for e in after_cooldown
    )


def test_active_warnings_reports_distance_direction():
    clock = FakeClock()
    config, manager = _setup(clock)
    threshold = config.get("reminder.distance_anomaly_threshold_sec")

    manager.update(_metrics(category=DistanceCategory.TOO_CLOSE, distance=20.0))
    clock.advance(threshold + 0.1)
    manager.update(_metrics(category=DistanceCategory.TOO_CLOSE, distance=20.0))
    assert manager.active_warnings() == ["distance_too_close"]

    far_clock = FakeClock()
    config, far_manager = _setup(far_clock)
    far_manager.update(_metrics(category=DistanceCategory.TOO_FAR, distance=100.0))
    far_clock.advance(threshold + 0.1)
    far_manager.update(
        _metrics(category=DistanceCategory.TOO_FAR, distance=100.0)
    )
    assert far_manager.active_warnings() == ["distance_too_far"]


def test_reminder_type_values_unchanged():
    """CSV reminder strings are part of the log contract; lock them verbatim."""
    assert [(member.name, member.value) for member in ReminderType] == [
        ("EYE_CARE_20_20", "eye_care_20_20"),
        ("SEDENTARY", "sedentary"),
        ("POSTURE_WARNING", "posture_warning"),
        ("DISTANCE_WARNING", "distance_warning"),
        ("BRIGHTNESS_WARNING", "brightness_warning"),
        ("FACE_LOST", "face_lost"),
    ]


def test_select_banner_shows_message_within_hold():
    event = ReminderEvent(
        ReminderType.DISTANCE_WARNING, "Too close — move back", 100.0
    )
    for now in (100.0, 101.5, 102.999, 103.0):
        assert (
            select_banner(now, [event], ["distance_too_close"], 3.0)
            == "Too close — move back"
        )


def test_select_banner_falls_back_to_labels_after_hold():
    event = ReminderEvent(
        ReminderType.DISTANCE_WARNING, "Too close — move back", 100.0
    )
    assert (
        select_banner(103.001, [event], ["distance_too_close"], 3.0)
        == "WARNING: distance_too_close"
    )


def test_select_banner_empty_without_events_or_active_labels():
    assert select_banner(0.0, [], [], 3.0) == ""


def test_select_banner_without_events_uses_active_labels():
    assert (
        select_banner(0.0, [], ["face_lost", "posture"], 3.0)
        == "WARNING: face_lost, posture"
    )


def test_select_banner_uses_latest_event_message():
    older = ReminderEvent(ReminderType.SEDENTARY, "Stand up and move around", 10.0)
    newer = ReminderEvent(
        ReminderType.DISTANCE_WARNING, "Too far — move closer", 11.0
    )
    assert (
        select_banner(11.5, [older, newer], ["distance_too_far"], 3.0)
        == "Too far — move closer"
    )
