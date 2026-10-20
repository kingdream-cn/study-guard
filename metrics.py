"""Frame-level metrics computation and anomaly tracking (M4)."""

import statistics
import time
from dataclasses import dataclass
from enum import Enum
from typing import Callable, Optional

import cv2
import numpy as np

from calibrator import DistanceCalibrator
from detector import FaceBox

# Defaults mirror configs/default.json; M4 wires them through AppConfig.
DEFAULT_TOO_CLOSE_CM = 30.0
DEFAULT_TOO_FAR_CM = 80.0
DEFAULT_IDEAL_Y_RATIO = 0.4
DEFAULT_IDEAL_W_RATIO = 0.25
DEFAULT_TOLERANCE = 0.15
DEFAULT_BRIGHTNESS_THRESHOLDS = (51.0, 102.0, 153.0, 204.0)
DEFAULT_AUTO_BASELINE = True
DEFAULT_BASELINE_FRAMES = 30


class DistanceCategory(Enum):
    """Distance category relative to configured thresholds."""

    TOO_CLOSE = "too_close"
    NORMAL = "normal"
    TOO_FAR = "too_far"
    UNKNOWN = "unknown"


@dataclass
class FrameMetrics:
    """Computed metrics for a single frame."""

    timestamp: float           # monotonic time
    distance_cm: Optional[float]
    distance_category: DistanceCategory
    posture_score: float       # 0.0 (worst) to 1.0 (best)
    brightness_level: int      # 1 (darkest) to 5 (brightest)
    face_detected: bool
    face_box: Optional[FaceBox]


class MetricsCalculator:
    """Compute frame-level metrics from detection results.

    Posture scoring can learn a session baseline: when ``auto_baseline`` is
    enabled, the median y/w ratios of the first ``baseline_frames`` face frames
    become the ideal posture. The limitation is that the opening posture is
    taken as correct by definition.
    """

    def __init__(
        self,
        calibrator: DistanceCalibrator,
        too_close_cm: float = DEFAULT_TOO_CLOSE_CM,
        too_far_cm: float = DEFAULT_TOO_FAR_CM,
        ideal_y_ratio: float = DEFAULT_IDEAL_Y_RATIO,
        ideal_w_ratio: float = DEFAULT_IDEAL_W_RATIO,
        tolerance: float = DEFAULT_TOLERANCE,
        brightness_thresholds: tuple[float, ...] = DEFAULT_BRIGHTNESS_THRESHOLDS,
        auto_baseline: bool = DEFAULT_AUTO_BASELINE,
        baseline_frames: int = DEFAULT_BASELINE_FRAMES,
    ) -> None:
        """Initialize the calculator.

        Args:
            calibrator: Fitted distance calibrator.
            too_close_cm: Distance below which the category is TOO_CLOSE.
            too_far_cm: Distance above which the category is TOO_FAR.
            ideal_y_ratio: Fallback ideal face center Y / frame height.
            ideal_w_ratio: Fallback ideal face width / frame width.
            tolerance: Posture score tolerance (fraction).
            brightness_thresholds: Luminance boundaries between levels 1..5.
            auto_baseline: Learn the ideal posture from the session start.
            baseline_frames: Number of face frames used for the baseline.
        """
        self._calibrator = calibrator
        self._too_close_cm = too_close_cm
        self._too_far_cm = too_far_cm
        self._ideal_y_ratio = ideal_y_ratio
        self._ideal_w_ratio = ideal_w_ratio
        self._tolerance = tolerance
        self._brightness_thresholds = tuple(brightness_thresholds)
        self._auto_baseline = auto_baseline
        self._baseline_frames = max(1, int(baseline_frames))
        self._baseline_y: list[float] = []
        self._baseline_w: list[float] = []
        self._baseline_ready = False

    def compute(self, frame: np.ndarray, faces: list[FaceBox]) -> FrameMetrics:
        """Compute all metrics for a single frame.

        The largest detected face is used as the primary subject. If no face is
        detected, distance and posture use fallback values (None / 0.0).

        Args:
            frame: BGR image.
            faces: List of detected face boxes.

        Returns:
            :class:`FrameMetrics` for this frame.
        """
        face = max(faces, key=lambda f: f.area) if faces else None
        frame_h, frame_w = frame.shape[:2]

        y_ratio = 0.0
        w_ratio = 0.0
        if face is not None and frame_h > 0 and frame_w > 0:
            y_ratio = (face.y + face.h / 2.0) / frame_h
            w_ratio = face.w / float(frame_w)
            self._maybe_update_baseline(y_ratio, w_ratio)

        distance_cm: Optional[float] = None
        if face is not None and face.w > 0:
            distance_cm = self._calibrator.estimate_distance(face.w)

        return FrameMetrics(
            timestamp=time.monotonic(),
            distance_cm=distance_cm,
            distance_category=self.classify_distance(distance_cm),
            posture_score=self._posture_score(face, y_ratio, w_ratio),
            brightness_level=self._brightness_level(frame),
            face_detected=face is not None,
            face_box=face,
        )

    def _maybe_update_baseline(self, y_ratio: float, w_ratio: float) -> None:
        if not self._auto_baseline or self._baseline_ready:
            return
        self._baseline_y.append(y_ratio)
        self._baseline_w.append(w_ratio)
        if len(self._baseline_y) >= self._baseline_frames:
            self._ideal_y_ratio = statistics.median(self._baseline_y)
            self._ideal_w_ratio = statistics.median(self._baseline_w)
            self._baseline_ready = True

    def _posture_score(
        self, face: Optional[FaceBox], y_ratio: float, w_ratio: float
    ) -> float:
        if face is None:
            return 0.0
        deviation_y = abs(y_ratio - self._ideal_y_ratio)
        deviation_w = abs(w_ratio - self._ideal_w_ratio)
        if self._tolerance <= 0:
            return 1.0 if deviation_y == 0.0 and deviation_w == 0.0 else 0.0
        score_y = max(0.0, 1.0 - deviation_y / self._tolerance)
        score_w = max(0.0, 1.0 - deviation_w / self._tolerance)
        return max(0.0, min(1.0, (score_y + score_w) / 2.0))

    @property
    def baseline_ready(self) -> bool:
        """Whether the session posture baseline has been established."""
        return self._baseline_ready

    @property
    def baseline_progress(self) -> int:
        """Number of face frames collected for the baseline so far."""
        return len(self._baseline_y)

    @property
    def ideal_y_ratio(self) -> float:
        """Current ideal face center Y / frame height."""
        return self._ideal_y_ratio

    @property
    def ideal_w_ratio(self) -> float:
        """Current ideal face width / frame width."""
        return self._ideal_w_ratio

    def classify_distance(self, distance_cm: Optional[float]) -> DistanceCategory:
        """Classify a distance value into a category.

        Args:
            distance_cm: Estimated distance in cm, or None.

        Returns:
            The corresponding :class:`DistanceCategory`.
        """
        if distance_cm is None:
            return DistanceCategory.UNKNOWN
        if distance_cm < self._too_close_cm:
            return DistanceCategory.TOO_CLOSE
        if distance_cm > self._too_far_cm:
            return DistanceCategory.TOO_FAR
        return DistanceCategory.NORMAL

    def _brightness_level(self, frame: np.ndarray) -> int:
        """Relative brightness grade (1-5) from mean grayscale luminance."""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        luminance = float(np.mean(gray))
        level = 1
        for threshold in self._brightness_thresholds:
            if luminance >= threshold:
                level += 1
        return level


@dataclass
class _AnomalyState:
    """Internal tracking state for one metric."""

    started_at: Optional[float] = None
    last_triggered_at: Optional[float] = None
    triggered: bool = False


class AnomalyTracker:
    """Track sustained anomalies and cooldown per named metric.

    M4's ``reminder.py`` consumes the return value of :meth:`update` to emit
    reminder events.
    """

    def __init__(self, clock: Optional[Callable[[], float]] = None) -> None:
        """Initialize the tracker.

        Args:
            clock: Optional injectable clock (defaults to ``time.monotonic``).
        """
        self._clock = clock or time.monotonic
        self._states: dict[str, _AnomalyState] = {}

    def update(
        self,
        metric: str,
        is_anomalous: bool,
        threshold_sec: float,
        cooldown_sec: float,
    ) -> bool:
        """Advance tracking for one metric.

        Args:
            metric: Metric name (e.g. ``"distance"``, ``"posture"``).
            is_anomalous: Whether the metric is currently out of range.
            threshold_sec: How long the metric must stay anomalous to trigger.
            cooldown_sec: Quiet period after a trigger (no duplicate trigger).

        Returns:
            True exactly once when a sustained anomaly crosses the threshold.
        """
        now = self._clock()
        state = self._states.setdefault(metric, _AnomalyState())

        if not is_anomalous:
            state.started_at = None
            state.triggered = False
            return False

        if state.triggered:
            return False

        if state.last_triggered_at is not None and (
            now - state.last_triggered_at < cooldown_sec
        ):
            return False

        if state.started_at is None:
            state.started_at = now

        if now - state.started_at >= threshold_sec:
            state.triggered = True
            state.last_triggered_at = now
            state.started_at = None
            return True

        return False

    def is_active(self, metric: str) -> bool:
        """Whether the metric is currently in a triggered warning state."""
        state = self._states.get(metric)
        return bool(state and state.triggered)

    def active_metrics(self) -> list[str]:
        """Names of metrics currently in a triggered warning state."""
        return [metric for metric, state in self._states.items() if state.triggered]

    def reset(self) -> None:
        """Reset all tracking state."""
        self._states.clear()
