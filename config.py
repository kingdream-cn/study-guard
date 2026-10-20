"""Application configuration loading and validation (M4)."""

import json
from pathlib import Path
from typing import Any

DEFAULT_CONFIG: dict[str, Any] = {
    "input": {
        "source": "camera",
        "video_path": "",
        "camera_index": 0,
    },
    "detection": {
        "scale_factor": 1.1,
        "min_neighbors": 5,
        "min_face_size": 30,
    },
    "distance": {
        "too_close_cm": 30.0,
        "too_far_cm": 80.0,
        "smoothing_window": 5,
    },
    "posture": {
        "ideal_y_ratio": 0.4,
        "ideal_w_ratio": 0.25,
        "tolerance": 0.15,
        "auto_baseline": True,
        "baseline_frames": 30,
        "anomaly_score": 0.5,
    },
    "brightness": {
        "levels": 5,
        "thresholds": [51.0, 102.0, 153.0, 204.0],
    },
    "reminder": {
        "eye_care_interval_min": 20.0,
        "eye_care_look_far_sec": 20.0,
        "sedentary_interval_min": 45.0,
        "posture_anomaly_threshold_sec": 8.0,
        "distance_anomaly_threshold_sec": 3.0,
        "cooldown_sec": 60.0,
        "face_lost_sec": 10.0,
    },
    "logging": {
        "interval_sec": 1.0,
        "log_dir": "logs",
    },
    "report": {
        "output_dir": "reports",
        "generate_charts": True,
    },
}


class ConfigError(Exception):
    """Raised when configuration is invalid or missing required keys."""


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Recursively merge ``override`` into a copy of ``base``."""
    merged = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


class AppConfig:
    """Application configuration container."""

    def __init__(self, config_path: Path) -> None:
        """Load and validate configuration from a JSON file.

        Args:
            config_path: Path to the JSON configuration file.

        Raises:
            ConfigError: If the file is missing, unreadable, not a JSON object,
                or contains invalid values.
        """
        path = Path(config_path)
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except FileNotFoundError as exc:
            raise ConfigError(f"Config file not found: {path}") from exc
        except json.JSONDecodeError as exc:
            raise ConfigError(f"Invalid JSON in config file: {path}") from exc
        except OSError as exc:
            raise ConfigError(f"Cannot read config file: {path}") from exc

        if not isinstance(raw, dict):
            raise ConfigError("Config root must be a JSON object")

        self._data = _deep_merge(DEFAULT_CONFIG, raw)
        self._validate()

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value by dot-separated key path.

        Args:
            key: Dot-separated key, e.g. ``"reminder.eye_care_interval_min"``.
            default: Value to return if the key is not found.

        Returns:
            Configuration value or ``default``.
        """
        node: Any = self._data
        for part in key.split("."):
            if not isinstance(node, dict) or part not in node:
                return default
            node = node[part]
        return node

    def _number(self, key: str) -> float:
        value = self.get(key)
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ConfigError(f"{key} must be a number")
        return float(value)

    def _integer(self, key: str) -> int:
        value = self.get(key)
        if isinstance(value, bool) or not isinstance(value, int):
            raise ConfigError(f"{key} must be an integer")
        return value

    def _validate(self) -> None:
        if self.get("input.source") not in ("file", "camera"):
            raise ConfigError("input.source must be 'file' or 'camera'")
        if self._integer("input.camera_index") < 0:
            raise ConfigError("input.camera_index must be >= 0")

        if self._number("detection.scale_factor") <= 1.0:
            raise ConfigError("detection.scale_factor must be > 1.0")
        if self._integer("detection.min_neighbors") < 0:
            raise ConfigError("detection.min_neighbors must be >= 0")
        if self._integer("detection.min_face_size") <= 0:
            raise ConfigError("detection.min_face_size must be > 0")

        too_close = self._number("distance.too_close_cm")
        too_far = self._number("distance.too_far_cm")
        if too_close <= 0:
            raise ConfigError("distance.too_close_cm must be > 0")
        if too_far <= too_close:
            raise ConfigError("distance.too_far_cm must be > distance.too_close_cm")
        if self._integer("distance.smoothing_window") < 1:
            raise ConfigError("distance.smoothing_window must be >= 1")

        for key in ("posture.ideal_y_ratio", "posture.ideal_w_ratio"):
            value = self._number(key)
            if not 0.0 <= value <= 1.0:
                raise ConfigError(f"{key} must be within [0.0, 1.0]")
        if self._number("posture.tolerance") <= 0:
            raise ConfigError("posture.tolerance must be > 0")
        if not isinstance(self.get("posture.auto_baseline"), bool):
            raise ConfigError("posture.auto_baseline must be a boolean")
        if self._integer("posture.baseline_frames") < 1:
            raise ConfigError("posture.baseline_frames must be >= 1")
        anomaly_score = self._number("posture.anomaly_score")
        if not 0.0 < anomaly_score < 1.0:
            raise ConfigError("posture.anomaly_score must be within (0.0, 1.0)")

        levels = self._integer("brightness.levels")
        if levels < 2:
            raise ConfigError("brightness.levels must be >= 2")
        thresholds = self.get("brightness.thresholds")
        if not isinstance(thresholds, list) or len(thresholds) != levels - 1:
            raise ConfigError("brightness.thresholds must be a list of length levels - 1")
        previous = -1.0
        for threshold in thresholds:
            if isinstance(threshold, bool) or not isinstance(threshold, (int, float)):
                raise ConfigError("brightness.thresholds must contain numbers")
            if float(threshold) <= previous:
                raise ConfigError("brightness.thresholds must be strictly increasing")
            previous = float(threshold)

        for key in (
            "reminder.eye_care_interval_min",
            "reminder.eye_care_look_far_sec",
            "reminder.sedentary_interval_min",
            "reminder.posture_anomaly_threshold_sec",
            "reminder.distance_anomaly_threshold_sec",
        ):
            if self._number(key) <= 0:
                raise ConfigError(f"{key} must be > 0")
        if self._number("reminder.cooldown_sec") < 0:
            raise ConfigError("reminder.cooldown_sec must be >= 0")
        if self._number("reminder.face_lost_sec") < 0:
            raise ConfigError("reminder.face_lost_sec must be >= 0")

        if self._number("logging.interval_sec") <= 0:
            raise ConfigError("logging.interval_sec must be > 0")

        if not isinstance(self.get("report.generate_charts"), bool):
            raise ConfigError("report.generate_charts must be a boolean")
