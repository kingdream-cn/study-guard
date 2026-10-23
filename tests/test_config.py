"""Tests for configuration loading and validation (config.py)."""

import json
from pathlib import Path

import pytest

from config import AppConfig, ConfigError

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "configs" / "default.json"


def _write(tmp_path: Path, data: dict) -> Path:
    path = tmp_path / "config.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def test_json_config_load(tmp_path):
    path = _write(
        tmp_path,
        {
            "distance": {"too_close_cm": 35.0, "too_far_cm": 85.0},
            "reminder": {"eye_care_interval_min": 25.0},
        },
    )
    config = AppConfig(path)
    assert config.get("distance.too_close_cm") == 35.0
    assert config.get("reminder.eye_care_interval_min") == 25.0


def test_json_config_missing_key(tmp_path):
    config = AppConfig(_write(tmp_path, {}))
    assert config.get("reminder.eye_care_interval_min") == 20.0
    assert config.get("posture.auto_baseline") is True


def test_get_unknown_key_returns_default(tmp_path):
    config = AppConfig(_write(tmp_path, {}))
    assert config.get("no.such.key", 42) == 42


def test_json_config_invalid_value(tmp_path):
    path = _write(
        tmp_path, {"distance": {"too_close_cm": 90.0, "too_far_cm": 80.0}}
    )
    with pytest.raises(ConfigError):
        AppConfig(path)


def test_load_missing_file(tmp_path):
    with pytest.raises(ConfigError):
        AppConfig(tmp_path / "missing.json")


def test_load_corrupted_file(tmp_path):
    path = tmp_path / "bad.json"
    path.write_text("{ not json", encoding="utf-8")
    with pytest.raises(ConfigError):
        AppConfig(path)


def test_project_default_config_loads():
    config = AppConfig(DEFAULT_CONFIG_PATH)
    assert config.get("distance.too_close_cm") > 0
    assert config.get("distance.too_far_cm") > config.get("distance.too_close_cm")
    assert config.get("reminder.eye_care_interval_min") > 0
    assert isinstance(config.get("posture.auto_baseline"), bool)


def test_hardcoded_defaults_match_spec():
    from config import DEFAULT_CONFIG

    reminder = DEFAULT_CONFIG["reminder"]
    assert reminder["distance_anomaly_threshold_sec"] == 3.0
    assert reminder["posture_anomaly_threshold_sec"] == 8.0
    assert reminder["face_lost_sec"] == 10.0
    assert DEFAULT_CONFIG["posture"]["auto_baseline"] is True


def test_detection_scale_factor_below_min_rejected(tmp_path):
    path = _write(tmp_path, {"detection": {"scale_factor": 1.0}})
    with pytest.raises(ConfigError):
        AppConfig(path)


def test_detection_scale_factor_above_max_rejected(tmp_path):
    path = _write(tmp_path, {"detection": {"scale_factor": 2.1}})
    with pytest.raises(ConfigError):
        AppConfig(path)


def test_detection_min_face_size_zero_rejected(tmp_path):
    path = _write(tmp_path, {"detection": {"min_face_size": 0}})
    with pytest.raises(ConfigError):
        AppConfig(path)


def test_detection_min_face_size_negative_rejected(tmp_path):
    path = _write(tmp_path, {"detection": {"min_face_size": -5}})
    with pytest.raises(ConfigError):
        AppConfig(path)
