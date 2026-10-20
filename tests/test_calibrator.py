"""Tests for the distance calibrator (calibrator.py)."""

import pytest

from calibrator import CalibrationError, DistanceCalibrator


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
