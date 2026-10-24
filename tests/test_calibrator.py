"""Tests for the distance calibrator (calibrator.py)."""

import inspect
import json

import pytest

from calibrator import CalibrationError, DistanceCalibrator


LEGACY_HAAR = {
    "k": 11488.340120138406,
    "samples": [
        {"distance_cm": 30.0, "face_width_px": 318.0},
        {"distance_cm": 50.0, "face_width_px": 234.5},
        {"distance_cm": 70.0, "face_width_px": 168.5},
    ],
}


def _fitted(backend: str = "haar") -> DistanceCalibrator:
    calibrator = DistanceCalibrator(backend=backend)
    for distance, width in ((30.0, 280.0), (50.0, 150.0), (70.0, 90.0)):
        calibrator.add_sample(distance, width)
    calibrator.fit()
    return calibrator


def _write_json(path, data) -> None:
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def _canon(value) -> str:
    return json.dumps(value, sort_keys=True)


def test_add_sample_valid():
    calibrator = DistanceCalibrator()
    calibrator.add_sample(known_distance_cm=30.0, face_width_px=200.0)
    assert calibrator.sample_count == 1


def test_add_sample_invalid_distance():
    calibrator = DistanceCalibrator()
    with pytest.raises(ValueError):
        calibrator.add_sample(known_distance_cm=0.0, face_width_px=200.0)
    with pytest.raises(ValueError):
        calibrator.add_sample(known_distance_cm=-30.0, face_width_px=200.0)


def test_add_sample_invalid_width():
    calibrator = DistanceCalibrator()
    with pytest.raises(ValueError):
        calibrator.add_sample(known_distance_cm=30.0, face_width_px=0.0)
    with pytest.raises(ValueError):
        calibrator.add_sample(known_distance_cm=30.0, face_width_px=-200.0)


def test_fit_with_three_samples():
    calibrator = DistanceCalibrator()
    calibrator.add_sample(30.0, 280.0)
    calibrator.add_sample(50.0, 150.0)
    calibrator.add_sample(70.0, 90.0)
    k = calibrator.fit()
    assert k > 0
    assert calibrator.k_value == k


def test_fit_insufficient_samples():
    calibrator = DistanceCalibrator()
    calibrator.add_sample(30.0, 280.0)
    calibrator.add_sample(50.0, 150.0)
    with pytest.raises(CalibrationError):
        calibrator.fit()


def test_estimate_distance_calibrated():
    calibrator = DistanceCalibrator()
    calibrator.add_sample(30.0, 280.0)
    calibrator.add_sample(50.0, 150.0)
    calibrator.add_sample(70.0, 90.0)
    calibrator.fit()
    assert calibrator.estimate_distance(150.0) > 0


def test_estimate_distance_not_calibrated():
    calibrator = DistanceCalibrator()
    calibrator.add_sample(30.0, 280.0)
    calibrator.add_sample(50.0, 150.0)
    calibrator.add_sample(70.0, 90.0)
    # Samples added but fit() not called yet.
    assert calibrator.estimate_distance(150.0) is None


def test_save_and_load(tmp_path):
    calibrator = DistanceCalibrator()
    calibrator.add_sample(30.0, 280.0)
    calibrator.add_sample(50.0, 150.0)
    calibrator.add_sample(70.0, 90.0)
    calibrator.fit()

    path = tmp_path / "calibration.json"
    calibrator.save(path)

    loaded = DistanceCalibrator()
    loaded.load(path)
    assert loaded.k_value == pytest.approx(calibrator.k_value)
    assert loaded.sample_count == calibrator.sample_count


def test_load_missing_file(tmp_path):
    calibrator = DistanceCalibrator()
    with pytest.raises(CalibrationError):
        calibrator.load(tmp_path / "does_not_exist.json")


def test_load_corrupted_file(tmp_path):
    path = tmp_path / "bad.json"
    path.write_text("{ this is not valid json")
    calibrator = DistanceCalibrator()
    with pytest.raises(CalibrationError):
        calibrator.load(path)


def test_least_squares_accuracy():
    """Fit must recover a known k for data generated from d = k / w."""
    k_true = 8000.0
    calibrator = DistanceCalibrator()
    for width in (100.0, 200.0, 400.0, 800.0):
        calibrator.add_sample(known_distance_cm=k_true / width, face_width_px=width)
    k = calibrator.fit()
    assert abs(k - k_true) / k_true < 0.01


# -- backend identity -------------------------------------------------------


def test_backend_defaults_to_haar():
    assert DistanceCalibrator().backend == "haar"


def test_backend_is_keyword_only():
    param = inspect.signature(DistanceCalibrator).parameters["backend"]
    assert param.kind is inspect.Parameter.KEYWORD_ONLY
    assert param.default == "haar"


def test_invalid_backend_rejected():
    with pytest.raises(ValueError, match="Unknown detector backend"):
        DistanceCalibrator(backend="mediapipe")


# -- save: three starting states -------------------------------------------


def test_save_unfitted_rejected(tmp_path):
    path = tmp_path / "calibration.json"
    with pytest.raises(CalibrationError, match="fit"):
        DistanceCalibrator().save(path)
    assert not path.exists()


def test_save_new_file_haar_writes_top_level_only(tmp_path):
    path = tmp_path / "calibration.json"
    calibrator = _fitted("haar")
    calibrator.save(path)
    data = _read_json(path)
    assert set(data) == {"k", "samples"}
    assert data["k"] == pytest.approx(calibrator.k_value)


def test_save_new_file_yunet_writes_backends_only(tmp_path):
    path = tmp_path / "calibration.json"
    calibrator = _fitted("yunet")
    calibrator.save(path)
    data = _read_json(path)
    assert set(data) == {"backends"}
    assert data["backends"]["yunet"]["k"] == pytest.approx(calibrator.k_value)
    assert "k" not in data and "samples" not in data


def test_save_yunet_preserves_haar_top_level(tmp_path):
    path = tmp_path / "calibration.json"
    _write_json(path, LEGACY_HAAR)
    calibrator = _fitted("yunet")
    calibrator.save(path)

    after = _read_json(path)
    assert _canon(after["k"]) == _canon(LEGACY_HAAR["k"])
    assert _canon(after["samples"]) == _canon(LEGACY_HAAR["samples"])
    assert after["backends"]["yunet"]["k"] == pytest.approx(
        calibrator.k_value
    )


def test_save_haar_preserves_other_backend(tmp_path):
    path = tmp_path / "calibration.json"
    yunet_entry = {
        "k": 9000.0,
        "samples": [{"distance_cm": 40.0, "face_width_px": 120.0}],
    }
    _write_json(
        path,
        {"k": 1.0, "samples": [], "backends": {"yunet": yunet_entry}},
    )
    calibrator = _fitted("haar")
    calibrator.save(path)

    after = _read_json(path)
    assert _canon(after["backends"]["yunet"]) == _canon(yunet_entry)
    assert after["k"] == pytest.approx(calibrator.k_value)


def test_save_haar_refreshes_backends_haar_mirror(tmp_path):
    path = tmp_path / "calibration.json"
    yunet_entry = {"k": 9000.0, "samples": []}
    _write_json(
        path,
        {
            "k": 1.0,
            "samples": [],
            "backends": {
                "haar": {"k": 2.0, "samples": []},
                "yunet": yunet_entry,
            },
        },
    )
    calibrator = _fitted("haar")
    calibrator.save(path)

    after = _read_json(path)
    assert after["k"] == pytest.approx(calibrator.k_value)
    assert after["backends"]["haar"]["k"] == pytest.approx(calibrator.k_value)
    assert after["backends"]["haar"]["samples"] == after["samples"]
    assert _canon(after["backends"]["yunet"]) == _canon(yunet_entry)


def test_save_same_backend_replaces_only_its_entry(tmp_path):
    path = tmp_path / "calibration.json"
    first = _fitted("yunet")
    first.save(path)
    first_k = _read_json(path)["backends"]["yunet"]["k"]

    second = DistanceCalibrator(backend="yunet")
    for distance, width in ((30.0, 200.0), (50.0, 120.0), (70.0, 80.0)):
        second.add_sample(distance, width)
    second.fit()
    second.save(path)

    data = _read_json(path)
    assert set(data["backends"]) == {"yunet"}
    assert data["backends"]["yunet"]["k"] == pytest.approx(second.k_value)
    assert data["backends"]["yunet"]["k"] != pytest.approx(first_k)


def test_save_refuses_corrupted_existing_file(tmp_path):
    path = tmp_path / "calibration.json"
    path.write_text("{ this is not valid json", encoding="utf-8")
    with pytest.raises(CalibrationError, match="Refusing to overwrite"):
        _fitted("yunet").save(path)
    assert path.read_text(encoding="utf-8") == "{ this is not valid json"


def test_save_refuses_non_object_backends(tmp_path):
    path = tmp_path / "calibration.json"
    original = json.dumps({"k": 1.0, "samples": [], "backends": []})
    path.write_text(original, encoding="utf-8")
    with pytest.raises(CalibrationError, match="backends"):
        _fitted("yunet").save(path)
    assert path.read_text(encoding="utf-8") == original


def test_save_leaves_no_temp_file(tmp_path):
    path = tmp_path / "calibration.json"
    _fitted("yunet").save(path)
    assert list(tmp_path.glob(".*.tmp")) == []


# -- load: six-state decision table ----------------------------------------


def test_load_legacy_file_for_haar(tmp_path):
    path = tmp_path / "calibration.json"
    _write_json(path, LEGACY_HAAR)
    calibrator = DistanceCalibrator(backend="haar")
    calibrator.load(path)
    assert calibrator.k_value == pytest.approx(LEGACY_HAAR["k"])
    assert calibrator.sample_count == len(LEGACY_HAAR["samples"])


def test_load_legacy_file_for_yunet_raises_without_fallback(tmp_path):
    path = tmp_path / "calibration.json"
    _write_json(path, LEGACY_HAAR)
    calibrator = DistanceCalibrator(backend="yunet")
    with pytest.raises(CalibrationError, match="尚未标定"):
        calibrator.load(path)
    assert calibrator.k_value is None
    assert calibrator.sample_count == 0


def test_load_backends_entry_for_yunet(tmp_path):
    path = tmp_path / "calibration.json"
    data = dict(LEGACY_HAAR)
    data["backends"] = {
        "yunet": {
            "k": 9000.0,
            "samples": [{"distance_cm": 40.0, "face_width_px": 120.0}],
        }
    }
    _write_json(path, data)
    calibrator = DistanceCalibrator(backend="yunet")
    calibrator.load(path)
    assert calibrator.k_value == pytest.approx(9000.0)
    assert calibrator.sample_count == 1


def test_load_backends_haar_wins_over_top_level(tmp_path):
    path = tmp_path / "calibration.json"
    data = dict(LEGACY_HAAR)
    data["k"] = 111.0
    data["backends"] = {"haar": {"k": 222.0, "samples": []}}
    _write_json(path, data)
    calibrator = DistanceCalibrator(backend="haar")
    calibrator.load(path)
    assert calibrator.k_value == pytest.approx(222.0)


def test_load_backends_haar_without_top_level(tmp_path):
    path = tmp_path / "calibration.json"
    _write_json(
        path,
        {"backends": {"haar": {"k": 7000.0, "samples": []}}},
    )
    calibrator = DistanceCalibrator(backend="haar")
    calibrator.load(path)
    assert calibrator.k_value == pytest.approx(7000.0)


def test_load_haar_uses_top_level_mirror(tmp_path):
    path = tmp_path / "calibration.json"
    data = dict(LEGACY_HAAR)
    data["backends"] = {"yunet": {"k": 9000.0, "samples": []}}
    _write_json(path, data)
    calibrator = DistanceCalibrator(backend="haar")
    calibrator.load(path)
    assert calibrator.k_value == pytest.approx(LEGACY_HAAR["k"])


def test_load_missing_requested_backend_raises(tmp_path):
    path = tmp_path / "calibration.json"
    data = dict(LEGACY_HAAR)
    data["backends"] = {"haar": {"k": 222.0, "samples": []}}
    _write_json(path, data)
    calibrator = DistanceCalibrator(backend="yunet")
    with pytest.raises(CalibrationError, match="尚未标定"):
        calibrator.load(path)
    assert calibrator.k_value is None


def test_load_missing_backend_without_top_level_raises(tmp_path):
    path = tmp_path / "calibration.json"
    _write_json(path, {"backends": {"yunet": {"k": 9000.0, "samples": []}}})
    calibrator = DistanceCalibrator(backend="haar")
    with pytest.raises(CalibrationError, match="尚未标定"):
        calibrator.load(path)
    assert calibrator.k_value is None


def test_load_rejects_non_dict_backends(tmp_path):
    path = tmp_path / "calibration.json"
    _write_json(path, {"k": 1.0, "samples": [], "backends": []})
    with pytest.raises(CalibrationError, match="Invalid calibration data"):
        DistanceCalibrator(backend="haar").load(path)


def test_load_invalid_backends_haar_does_not_fall_back(tmp_path):
    path = tmp_path / "calibration.json"
    data = dict(LEGACY_HAAR)
    data["backends"] = {"haar": {"k": None, "samples": []}}
    _write_json(path, data)
    calibrator = DistanceCalibrator(backend="haar")
    with pytest.raises(CalibrationError, match="Invalid calibration data"):
        calibrator.load(path)
    assert calibrator.k_value is None
