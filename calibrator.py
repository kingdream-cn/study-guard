"""Three-point distance calibration using face box width."""

import json
from pathlib import Path
from typing import Optional


class CalibrationError(Exception):
    """Raised when calibration data is invalid or insufficient."""


class DistanceCalibrator:
    """Three-point distance calibration using face box width.

    Model: ``d = k / w`` where ``d`` is distance in cm and ``w`` is face box
    width in pixels. The parameter ``k`` is fitted by least squares:

        k = sum(d_i / w_i) / sum(1 / w_i^2)
    """

    def __init__(self) -> None:
        """Initialize with no calibration data."""
        self._samples: list[tuple[float, float]] = []  # (width_px, distance_cm)
        self._k_value: Optional[float] = None

    def add_sample(self, known_distance_cm: float, face_width_px: float) -> None:
        """Add a calibration sample.

        Args:
            known_distance_cm: Known distance in centimeters.
            face_width_px: Measured face bounding box width in pixels.

        Raises:
            ValueError: If distance or width is non-positive.
        """
        if known_distance_cm <= 0:
            raise ValueError("known_distance_cm must be positive")
        if face_width_px <= 0:
            raise ValueError("face_width_px must be positive")
        self._samples.append((float(face_width_px), float(known_distance_cm)))

    def fit(self) -> float:
        """Fit parameter k using least squares.

        Returns:
            Fitted k value: ``k = sum(d_i / w_i) / sum(1 / w_i^2)``.

        Raises:
            CalibrationError: If fewer than 3 samples have been added.
        """
        if len(self._samples) < 3:
            raise CalibrationError("At least 3 calibration samples are required")
        sum_d_over_w = sum(d / w for w, d in self._samples)
        sum_inv_w2 = sum(1.0 / (w * w) for w, _ in self._samples)
        if sum_inv_w2 == 0:
            raise CalibrationError("Cannot fit: sum of 1/w^2 is zero")
        self._k_value = sum_d_over_w / sum_inv_w2
        return self._k_value

    @property
    def k_value(self) -> Optional[float]:
        """Current fitted k value, or None if not yet fitted."""
        return self._k_value

    @property
    def sample_count(self) -> int:
        """Number of calibration samples currently collected."""
        return len(self._samples)

    def estimate_distance(self, face_width_px: float) -> Optional[float]:
        """Estimate distance from face width using fitted k.

        Args:
            face_width_px: Face bounding box width in pixels.

        Returns:
            Estimated distance in cm, or None if not calibrated.

        Raises:
            ValueError: If face_width_px is non-positive.
        """
        if self._k_value is None:
            return None
        if face_width_px <= 0:
            raise ValueError("face_width_px must be positive")
        return self._k_value / face_width_px

    def save(self, path: Path) -> None:
        """Save calibration data and k value to JSON file.

        Args:
            path: Output file path.
        """
        data = {
            "k": self._k_value,
            "samples": [
                {"distance_cm": d, "face_width_px": w}
                for w, d in self._samples
            ],
        }
        Path(path).write_text(json.dumps(data, indent=2))

    def load(self, path: Path) -> None:
        """Load calibration data from JSON file.

        Args:
            path: Input file path.

        Raises:
            CalibrationError: If file is missing, unreadable, or invalid.
        """
        try:
            text = Path(path).read_text()
        except OSError as exc:
            raise CalibrationError(
                f"Calibration file not found or unreadable: {path}"
            ) from exc

        try:
            data = json.loads(text)
        except json.JSONDecodeError as exc:
            raise CalibrationError(f"Invalid calibration JSON: {path}") from exc

        if not isinstance(data, dict) or "k" not in data or "samples" not in data:
            raise CalibrationError(f"Invalid calibration data in: {path}")

        k = data["k"]
        samples = data["samples"]
        if k is None or not isinstance(samples, list):
            raise CalibrationError(f"Invalid calibration data in: {path}")

        parsed: list[tuple[float, float]] = []
        for sample in samples:
            if not isinstance(sample, dict):
                raise CalibrationError(f"Invalid calibration sample in: {path}")
            d = sample.get("distance_cm")
            w = sample.get("face_width_px")
            if not isinstance(d, (int, float)) or not isinstance(w, (int, float)):
                raise CalibrationError(f"Invalid calibration sample in: {path}")
            if d <= 0 or w <= 0:
                raise CalibrationError(f"Invalid calibration sample in: {path}")
            parsed.append((float(w), float(d)))

        self._samples = parsed
        self._k_value = float(k)
