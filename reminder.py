"""Reminder timers and anomaly-to-reminder mapping (M4)."""

import time
from dataclasses import dataclass
from enum import Enum
from typing import Callable, Optional

from config import AppConfig
from metrics import AnomalyTracker, DistanceCategory, FrameMetrics


class ReminderType(Enum):
    """Kinds of reminders emitted by the manager."""

    EYE_CARE_20_20 = "eye_care_20_20"
    SEDENTARY = "sedentary"
    POSTURE_WARNING = "posture_warning"
    DISTANCE_WARNING = "distance_warning"
    BRIGHTNESS_WARNING = "brightness_warning"
    FACE_LOST = "face_lost"


@dataclass
class ReminderEvent:
    """A triggered reminder."""

    reminder_type: ReminderType
    message: str
    timestamp: float


class ReminderManager:
    """Manage 20-20-20 / sedentary timers and consume anomaly tracking."""

    def __init__(
        self, config: AppConfig, clock: Optional[Callable[[], float]] = None
    ) -> None:
        """Initialize the manager.

        Args:
            config: Application configuration.
            clock: Optional injectable clock (defaults to ``time.monotonic``).
        """
        self._clock = clock or time.monotonic
        self._tracker = AnomalyTracker(clock=self._clock)

        self._eye_care_interval = (
            float(config.get("reminder.eye_care_interval_min")) * 60.0
        )
        self._sedentary_interval = (
            float(config.get("reminder.sedentary_interval_min")) * 60.0
        )
        self._posture_threshold = float(
            config.get("reminder.posture_anomaly_threshold_sec")
        )
        self._distance_threshold = float(
            config.get("reminder.distance_anomaly_threshold_sec")
        )
        self._cooldown = float(config.get("reminder.cooldown_sec"))
        self._face_lost_sec = float(config.get("reminder.face_lost_sec"))
        self._posture_score_threshold = float(config.get("posture.anomaly_score"))

        self.reset()

    def reset(self) -> None:
        """Reset all timers and counters. Call at session start."""
        self._last_update: Optional[float] = None
        self._effective_study_time = 0.0
        self._session_elapsed_time = 0.0
        self._eye_care_accum = 0.0
        self._sedentary_accum = 0.0
        self._paused = False
        self._face_lost_since: Optional[float] = None
        self._face_lost_active = False
        self._tracker.reset()

    @property
    def effective_study_time(self) -> float:
        """Total seconds of valid face-present study time."""
        return self._effective_study_time

    @property
    def session_elapsed_time(self) -> float:
        """Total seconds since session start (including face-lost time)."""
        return self._session_elapsed_time

    @property
    def is_paused(self) -> bool:
        """Whether timers are manually paused."""
        return self._paused

    def pause(self) -> None:
        """Pause all timers. Call when user pauses or face is lost."""
        self._paused = True
        self._last_update = self._clock()

    def resume(self) -> None:
        """Resume all timers. Call when user resumes or face is regained."""
        self._paused = False
        self._last_update = self._clock()

    def update(self, metrics: FrameMetrics) -> list[ReminderEvent]:
        """Process new metrics and return reminders triggered by this frame.

        Args:
            metrics: Current frame metrics.

        Returns:
            List of :class:`ReminderEvent` triggered since the last update.
        """
        now = self._clock()
        if self._last_update is None:
            dt = 0.0
        else:
            dt = max(0.0, now - self._last_update)
        self._last_update = now

        events: list[ReminderEvent] = []
        if self._paused:
            return events

        self._session_elapsed_time += dt

        if metrics.face_detected:
            self._face_lost_since = None
            self._face_lost_active = False
            self._effective_study_time += dt
            self._eye_care_accum += dt
            self._sedentary_accum += dt
        else:
            if self._face_lost_since is None:
                self._face_lost_since = now
            if (
                not self._face_lost_active
                and now - self._face_lost_since >= self._face_lost_sec
            ):
                self._face_lost_active = True
                events.append(
                    ReminderEvent(ReminderType.FACE_LOST, "WARNING: face_lost", now)
                )

        if self._eye_care_accum >= self._eye_care_interval:
            self._eye_care_accum -= self._eye_care_interval
            events.append(
                ReminderEvent(
                    ReminderType.EYE_CARE_20_20,
                    "Eye care: look 20 ft away for 20 s",
                    now,
                )
            )

        if self._sedentary_accum >= self._sedentary_interval:
            self._sedentary_accum -= self._sedentary_interval
            events.append(
                ReminderEvent(
                    ReminderType.SEDENTARY, "Stand up and move around", now
                )
            )

        distance_anomaly = metrics.distance_category in (
            DistanceCategory.TOO_CLOSE,
            DistanceCategory.TOO_FAR,
        )
        if self._tracker.update(
            "distance", distance_anomaly, self._distance_threshold, self._cooldown
        ):
            events.append(
                ReminderEvent(
                    ReminderType.DISTANCE_WARNING, "Adjust viewing distance", now
                )
            )

        posture_anomaly = (
            metrics.face_detected
            and metrics.posture_score < self._posture_score_threshold
        )
        if self._tracker.update(
            "posture", posture_anomaly, self._posture_threshold, self._cooldown
        ):
            events.append(
                ReminderEvent(
                    ReminderType.POSTURE_WARNING, "Adjust your posture", now
                )
            )

        return events

    def active_warnings(self) -> list[str]:
        """Labels of warnings currently active (for the HUD banner)."""
        warnings: list[str] = []
        if self._face_lost_active:
            warnings.append("face_lost")
        if self._tracker.is_active("distance"):
            warnings.append("distance")
        if self._tracker.is_active("posture"):
            warnings.append("posture")
        return warnings
