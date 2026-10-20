"""Frame-level metrics computation (M2: distance estimation)."""

from enum import Enum
from typing import Optional

from calibrator import DistanceCalibrator

# Default distance thresholds. These mirror the ``distance`` section of
# ``configs/default.json`` and will be wired to AppConfig in a later milestone.
DEFAULT_TOO_CLOSE_CM = 30.0
DEFAULT_TOO_FAR_CM = 80.0


class DistanceCategory(Enum):
    """Distance category relative to configured thresholds."""

    TOO_CLOSE = "too_close"
    NORMAL = "normal"
    TOO_FAR = "too_far"
    UNKNOWN = "unknown"


class DistanceEstimator:
    """Estimate distance from face width and classify it.

    M2 scope: distance estimation only. Posture and brightness metrics are
    added in M3.
    """

    def __init__(
        self,
        calibrator: DistanceCalibrator,
        too_close_cm: float = DEFAULT_TOO_CLOSE_CM,
        too_far_cm: float = DEFAULT_TOO_FAR_CM,
    ) -> None:
        """Initialize the estimator.

        Args:
            calibrator: Fitted distance calibrator.
            too_close_cm: Distance below which the category is TOO_CLOSE.
            too_far_cm: Distance above which the category is TOO_FAR.
        """
        self._calibrator = calibrator
        self._too_close_cm = too_close_cm
        self._too_far_cm = too_far_cm

    def estimate(
        self, face_width_px: float
    ) -> tuple[Optional[float], DistanceCategory]:
        """Estimate distance and category for a face width.

        Args:
            face_width_px: Face bounding box width in pixels.

        Returns:
            Tuple of ``(distance_cm, category)``. ``distance_cm`` is None when
            the calibrator has not been fitted.

        Raises:
            ValueError: If face_width_px is non-positive.
        """
        distance = self._calibrator.estimate_distance(face_width_px)
        return distance, self.classify(distance)

    def classify(self, distance_cm: Optional[float]) -> DistanceCategory:
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
