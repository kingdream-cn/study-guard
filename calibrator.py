"""Three-point distance calibration using face box width."""

import json
import os
import tempfile
from pathlib import Path
from typing import Any, Optional

VALID_BACKENDS = ("haar", "yunet")


class CalibrationError(Exception):
    """Raised when calibration data is invalid or insufficient."""


class DistanceCalibrator:
    """Three-point distance calibration using face box width for one backend.

    Model: ``d = k / w`` where ``d`` is distance in cm and ``w`` is face box
    width in pixels. The parameter ``k`` is fitted by least squares:

        k = sum(d_i / w_i) / sum(1 / w_i^2)

    Calibration data is stored per detector backend. The legacy top-level
    ``k``/``samples`` entries are the Haar calibration (the mirror); other
    backends live under ``backends.<name>``. ``load()`` never falls back to a
    different backend's ``k``.

    Writes are atomic (temporary file + ``os.replace``), but no lock is taken:
    multiple processes writing the same calibration file concurrently are an
    unsupported (last-writer-wins) scenario.
    """

    def __init__(self, *, backend: str = "haar") -> None:
        """Initialize with no calibration data for ``backend``.

        Args:
            backend: Detector backend this calibrator belongs to, either
                ``"haar"`` (default) or ``"yunet"``. Keyword-only so existing
                ``DistanceCalibrator()`` call sites keep working.

        Raises:
            ValueError: If ``backend`` is not supported.
        """
        if backend not in VALID_BACKENDS:
            raise ValueError(
                f"Unknown detector backend: {backend!r} "
                "(expected 'haar' or 'yunet')"
            )
        self._backend = backend
        self._samples: list[tuple[float, float]] = []  # (width_px, distance_cm)
        self._k_value: Optional[float] = None

    @property
    def backend(self) -> str:
        """Detector backend this calibrator belongs to."""
        return self._backend

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
        """Merge this backend's calibration into a JSON file atomically.

        The existing file is read first; only this backend's entry is replaced,
        so another backend's data is preserved. For ``"haar"`` the top-level
        ``k``/``samples`` are refreshed (and ``backends.haar`` too, when that
        mirror entry already exists). For other backends only
        ``backends.<backend>`` is written and the top-level entries are left
        byte-for-byte unchanged.

        Args:
            path: Output file path.

        Raises:
            CalibrationError: If ``fit()`` has not produced a ``k`` value, the
                existing file is unreadable/invalid (including a non-object
                ``backends``), or the atomic write fails.
        """
        if self._k_value is None:
            raise CalibrationError(
                "Cannot save calibration: fit() has not produced a k value"
            )

        target = Path(path)
        data = self._read_for_merge(target)
        entry = self._entry()

        if self._backend == "haar":
            data["k"] = entry["k"]
            data["samples"] = entry["samples"]
            backends = data.get("backends")
            if isinstance(backends, dict) and "haar" in backends:
                backends["haar"] = entry
        else:
            backends = data.get("backends")
            if backends is None:
                backends = {}
            backends[self._backend] = entry
            data["backends"] = backends

        self._write_atomic(target, data)

    def load(self, path: Path) -> None:
        """Load this backend's calibration from a JSON file.

        Resolution order:

        1. ``backends.<backend>`` when that key exists (it wins even for
           ``"haar"``, and even when the top-level mirror differs).
        2. For ``"haar"`` only: the legacy top-level ``k``/``samples`` mirror.
        3. Otherwise raise :class:`CalibrationError`; never fall back to
           another backend's ``k``.

        Args:
            path: Input file path.

        Raises:
            CalibrationError: If the file is missing, unreadable, invalid, or
                has no calibration for this backend (该后端尚未标定).
        """
        target = Path(path)
        try:
            text = target.read_text(encoding="utf-8")
        except OSError as exc:
            raise CalibrationError(
                f"Calibration file not found or unreadable: {target}"
            ) from exc

        try:
            data = json.loads(text)
        except json.JSONDecodeError as exc:
            raise CalibrationError(
                f"Invalid calibration JSON: {target}"
            ) from exc

        if not isinstance(data, dict):
            raise CalibrationError(f"Invalid calibration data in: {target}")

        backends = data.get("backends")
        if "backends" in data and not isinstance(backends, dict):
            raise CalibrationError(f"Invalid calibration data in: {target}")

        if isinstance(backends, dict) and self._backend in backends:
            entry = backends[self._backend]
        elif self._backend == "haar" and "k" in data and "samples" in data:
            # Legacy/mirror path: backends.haar is absent.
            entry = {"k": data.get("k"), "samples": data.get("samples")}
        else:
            raise CalibrationError(
                f"No calibration for backend '{self._backend}' in: {target} "
                "(该后端尚未标定)"
            )

        k_value, parsed = self._parse_entry(entry, target)
        self._samples = parsed
        self._k_value = k_value

    # -- internal helpers ------------------------------------------------------

    def _entry(self) -> dict[str, Any]:
        """Build this calibrator's JSON entry."""
        return {
            "k": self._k_value,
            "samples": [
                {"distance_cm": d, "face_width_px": w}
                for w, d in self._samples
            ],
        }

    @staticmethod
    def _read_for_merge(path: Path) -> dict[str, Any]:
        """Read the current file for a read-modify-write save.

        Missing files start from an empty object. Existing but invalid files
        are rejected rather than overwritten, so unrelated data is not lost.
        """
        if not path.exists():
            return {}

        try:
            text = path.read_text(encoding="utf-8")
        except OSError as exc:
            raise CalibrationError(
                f"Cannot read calibration file: {path}"
            ) from exc
        try:
            data = json.loads(text)
        except json.JSONDecodeError as exc:
            raise CalibrationError(
                f"Refusing to overwrite invalid calibration JSON: {path}"
            ) from exc
        if not isinstance(data, dict):
            raise CalibrationError(
                f"Refusing to overwrite non-object calibration JSON: {path}"
            )
        if "backends" in data and not isinstance(data["backends"], dict):
            raise CalibrationError(
                f"Invalid backends object in calibration file: {path}"
            )
        return data

    @staticmethod
    def _write_atomic(path: Path, data: dict[str, Any]) -> None:
        """Write JSON via a same-directory temporary file and os.replace."""
        temp_path: Optional[Path] = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=path.parent,
                prefix=f".{path.name}.",
                suffix=".tmp",
                delete=False,
            ) as handle:
                temp_path = Path(handle.name)
                json.dump(data, handle, indent=2)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temp_path, path)
            temp_path = None
        except OSError as exc:
            raise CalibrationError(
                f"Cannot write calibration file: {path}"
            ) from exc
        finally:
            if temp_path is not None:
                try:
                    temp_path.unlink()
                except OSError:
                    pass

    @staticmethod
    def _parse_entry(
        entry: Any, path: Path
    ) -> tuple[float, list[tuple[float, float]]]:
        """Validate one calibration entry and return (k, samples)."""
        if not isinstance(entry, dict):
            raise CalibrationError(f"Invalid calibration data in: {path}")

        k = entry.get("k")
        samples = entry.get("samples")
        if (
            k is None
            or isinstance(k, bool)
            or not isinstance(k, (int, float))
            or not isinstance(samples, list)
        ):
            raise CalibrationError(f"Invalid calibration data in: {path}")

        parsed: list[tuple[float, float]] = []
        for sample in samples:
            if not isinstance(sample, dict):
                raise CalibrationError(
                    f"Invalid calibration sample in: {path}"
                )
            d = sample.get("distance_cm")
            w = sample.get("face_width_px")
            if (
                isinstance(d, bool)
                or isinstance(w, bool)
                or not isinstance(d, (int, float))
                or not isinstance(w, (int, float))
            ):
                raise CalibrationError(
                    f"Invalid calibration sample in: {path}"
                )
            if d <= 0 or w <= 0:
                raise CalibrationError(
                    f"Invalid calibration sample in: {path}"
                )
            parsed.append((float(w), float(d)))
        return float(k), parsed
