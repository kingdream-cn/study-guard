"""Tests for configuration loading and validation (config.py)."""

import json
import subprocess
import sys
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


def test_detection_backend_invalid_rejected(tmp_path):
    path = _write(tmp_path, {"detection": {"backend": "yolo"}})
    with pytest.raises(ConfigError, match="backend"):
        AppConfig(path)


def test_detection_score_threshold_zero_rejected(tmp_path):
    path = _write(tmp_path, {"detection": {"score_threshold": 0.0}})
    with pytest.raises(ConfigError, match="score_threshold"):
        AppConfig(path)


def test_detection_score_threshold_above_one_rejected(tmp_path):
    path = _write(tmp_path, {"detection": {"score_threshold": 1.1}})
    with pytest.raises(ConfigError, match="score_threshold"):
        AppConfig(path)


def test_detection_nms_threshold_zero_rejected(tmp_path):
    path = _write(tmp_path, {"detection": {"nms_threshold": 0.0}})
    with pytest.raises(ConfigError, match="nms_threshold"):
        AppConfig(path)


def test_detection_nms_threshold_above_one_rejected(tmp_path):
    path = _write(tmp_path, {"detection": {"nms_threshold": 1.1}})
    with pytest.raises(ConfigError, match="nms_threshold"):
        AppConfig(path)


def test_detection_top_k_zero_rejected(tmp_path):
    path = _write(tmp_path, {"detection": {"top_k": 0}})
    with pytest.raises(ConfigError, match="top_k"):
        AppConfig(path)


def test_detection_threshold_boundaries_accepted(tmp_path):
    path = _write(
        tmp_path,
        {
            "detection": {
                "score_threshold": 1.0,
                "nms_threshold": 1.0,
                "top_k": 1,
            }
        },
    )
    config = AppConfig(path)
    assert config.get("detection.score_threshold") == 1.0
    assert config.get("detection.nms_threshold") == 1.0
    assert config.get("detection.top_k") == 1


def test_yunet_backend_missing_model_rejected(tmp_path):
    missing = tmp_path / "missing.onnx"
    path = _write(
        tmp_path,
        {"detection": {"backend": "yunet", "model_path": str(missing)}},
    )
    with pytest.raises(ConfigError, match="does not exist"):
        AppConfig(path)


def test_yunet_backend_existing_model_accepted(tmp_path):
    model = tmp_path / "model.onnx"
    model.write_bytes(b"dummy")
    path = _write(
        tmp_path,
        {"detection": {"backend": "yunet", "model_path": str(model)}},
    )
    config = AppConfig(path)
    assert config.get("detection.backend") == "yunet"
    assert config.get("detection.model_path") == str(model)


def test_haar_backend_does_not_require_model_file(tmp_path):
    missing = tmp_path / "missing.onnx"
    path = _write(
        tmp_path,
        {"detection": {"backend": "haar", "model_path": str(missing)}},
    )
    config = AppConfig(path)
    assert config.get("detection.backend") == "haar"


def test_detection_model_path_must_be_string(tmp_path):
    path = _write(tmp_path, {"detection": {"model_path": 123}})
    with pytest.raises(ConfigError, match="model_path"):
        AppConfig(path)


def test_detection_defaults_match_yunet_demo_values():
    config = AppConfig(DEFAULT_CONFIG_PATH)
    assert config.get("detection.backend") == "haar"
    assert config.get("detection.score_threshold") == 0.9
    assert config.get("detection.nms_threshold") == 0.3
    assert config.get("detection.top_k") == 5000
    assert config.get("detection.model_path") == (
        "~/study_models/face_detection_yunet_2023mar.onnx"
    )


def test_main_exits_when_yunet_model_missing(tmp_path):
    """A missing YuNet model must abort startup, not fall back to Haar."""
    missing = tmp_path / "missing.onnx"
    config_path = _write(
        tmp_path,
        {"detection": {"backend": "yunet", "model_path": str(missing)}},
    )
    result = subprocess.run(
        [
            sys.executable,
            str(PROJECT_ROOT / "main.py"),
            "--config",
            str(config_path),
        ],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 1
    assert "does not exist" in result.stderr
