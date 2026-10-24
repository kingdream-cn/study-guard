"""Tests for session report generation (report.py)."""

import csv
import json
from pathlib import Path

import pytest

from calibrator import DistanceCalibrator
from config import AppConfig
from report import ReportGenerator

HEADER = [
    "timestamp",
    "face_detected",
    "face_x",
    "face_y",
    "face_w",
    "face_h",
    "distance_cm",
    "distance_category",
    "posture_score",
    "brightness_level",
    "reminder_triggered",
]


def _write_log(path: Path, rows: list[list]) -> Path:
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(HEADER)
        writer.writerows(rows)
    return path


def _config(
    tmp_path: Path,
    generate_charts: bool = False,
    interval: float = 1.0,
    backend: str = "haar",
) -> AppConfig:
    detection: dict = {"backend": backend}
    if backend != "haar":
        # The report path never loads a model, but AppConfig requires the
        # configured model file to exist when backend="yunet".
        model = tmp_path / "model.onnx"
        model.write_bytes(b"dummy")
        detection["model_path"] = str(model)
    cfg_path = tmp_path / "config.json"
    cfg_path.write_text(
        json.dumps(
            {
                "logging": {"interval_sec": interval},
                "report": {"generate_charts": generate_charts},
                "detection": detection,
            }
        ),
        encoding="utf-8",
    )
    return AppConfig(cfg_path)


def _face_row(
    ts: float,
    distance: str = "50.00",
    category: str = "normal",
    posture: str = "0.80",
    bright: str = "3",
    reminders: str = "",
) -> list[str]:
    return [
        f"{ts}", "1", "10", "20", "100", "80",
        distance, category, posture, bright, reminders,
    ]


def _no_face_row(ts: float, bright: str = "2") -> list[str]:
    return [
        f"{ts}", "0", "0", "0", "0", "0",
        "nan", "unknown", "0.000", bright, "",
    ]


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_report_generate_normal(tmp_path):
    log = _write_log(
        tmp_path / "s.csv",
        [
            _face_row(0.0, "40.00", "normal", "0.80", "3"),
            _face_row(1.0, "20.00", "too_close", "0.50", "3", "distance_warning"),
            _face_row(2.0, "60.00", "normal", "0.90", "4"),
        ],
    )
    generator = ReportGenerator(_config(tmp_path, generate_charts=False))
    out = generator.generate(log, tmp_path / "reports")

    assert out.exists()
    data = _read_json(out)
    assert data["insufficient_data"] is False
    assert data["session"]["row_count"] == 3
    assert data["session"]["face_detection_rate"] == 1.0
    assert data["distance"]["stats"]["mean_cm"] == pytest.approx(40.0)
    assert data["distance"]["stats"]["min_cm"] == 20.0
    assert data["distance"]["stats"]["max_cm"] == 60.0
    assert data["distance"]["stats"]["median_cm"] == 40.0
    assert data["distance"]["category_ratio"]["too_close"] == pytest.approx(
        1 / 3, abs=0.0001
    )
    assert data["posture"]["max"] == pytest.approx(0.9)
    assert data["reminders"]["distance_warning"] == 1
    assert data["brightness_distribution"]["3"] == 2
    assert data["brightness_distribution"]["4"] == 1


def test_report_empty_log(tmp_path):
    log = _write_log(tmp_path / "s.csv", [])  # header only, no data rows
    out = ReportGenerator(_config(tmp_path)).generate(log, tmp_path / "reports")

    data = _read_json(out)
    assert data["insufficient_data"] is True
    assert data["distance"] is None
    assert data["posture"] is None
    assert data["reminders"] is None


def test_report_all_face_lost(tmp_path):
    log = _write_log(
        tmp_path / "s.csv",
        [_no_face_row(0.0), _no_face_row(1.0), _no_face_row(2.0)],
    )
    out = ReportGenerator(_config(tmp_path)).generate(log, tmp_path / "reports")

    data = _read_json(out)
    assert data["insufficient_data"] is True
    assert data["session"] is None


def test_report_corrupted_log(tmp_path):
    log = _write_log(
        tmp_path / "s.csv",
        [
            _face_row(0.0),                              # good
            ["0.5"],                                     # bad: wrong column count
            _face_row(1.0, distance="abc"),              # bad: distance not a number
            _face_row(2.0),                              # good
        ],
    )
    out = ReportGenerator(_config(tmp_path)).generate(log, tmp_path / "reports")

    data = _read_json(out)
    assert data["insufficient_data"] is False
    assert data["session"]["row_count"] == 2  # only the two good rows


def test_report_corrupted_log_all_bad(tmp_path):
    log = _write_log(tmp_path / "s.csv", [["0.5"], ["x"], ["1", "2", "3"]])
    out = ReportGenerator(_config(tmp_path)).generate(log, tmp_path / "reports")

    data = _read_json(out)
    assert data["insufficient_data"] is True


def test_report_chart_toggle(tmp_path):
    log = _write_log(tmp_path / "s.csv", [_face_row(0.0), _face_row(1.0)])

    with_charts = ReportGenerator(_config(tmp_path, generate_charts=True)).generate(
        log, tmp_path / "reports_on"
    )
    data = _read_json(with_charts)
    assert data["insufficient_data"] is False
    assert len(list((tmp_path / "reports_on").glob("*.png"))) == 1

    without_charts = ReportGenerator(
        _config(tmp_path, generate_charts=False)
    ).generate(log, tmp_path / "reports_off")
    assert len(list((tmp_path / "reports_off").glob("*.png"))) == 0


def test_report_includes_calibration_k(tmp_path):
    calibrator = DistanceCalibrator()
    calibrator.add_sample(30.0, 280.0)
    calibrator.add_sample(50.0, 150.0)
    calibrator.add_sample(70.0, 90.0)
    calibrator.fit()
    cal_path = tmp_path / "calibration.json"
    calibrator.save(cal_path)

    log = _write_log(tmp_path / "s.csv", [_face_row(0.0)])
    generator = ReportGenerator(_config(tmp_path), calibration_path=cal_path)
    out = generator.generate(log, tmp_path / "reports")

    data = _read_json(out)
    assert data["session"]["calibration_k"] == pytest.approx(calibrator.k_value)


def test_report_uses_configured_backend_k(tmp_path):
    haar = DistanceCalibrator(backend="haar")
    for distance, width in ((30.0, 280.0), (50.0, 150.0), (70.0, 90.0)):
        haar.add_sample(distance, width)
    haar.fit()

    yunet = DistanceCalibrator(backend="yunet")
    for distance, width in ((30.0, 200.0), (50.0, 120.0), (70.0, 80.0)):
        yunet.add_sample(distance, width)
    yunet.fit()
    assert haar.k_value != pytest.approx(yunet.k_value)

    cal_path = tmp_path / "calibration.json"
    haar.save(cal_path)
    yunet.save(cal_path)

    log = _write_log(tmp_path / "s.csv", [_face_row(0.0)])
    for backend, expected in (("haar", haar.k_value), ("yunet", yunet.k_value)):
        generator = ReportGenerator(
            _config(tmp_path, backend=backend), calibration_path=cal_path
        )
        out = generator.generate(log, tmp_path / f"reports_{backend}")
        data = _read_json(out)
        assert data["session"]["calibration_k"] == pytest.approx(expected)


def test_report_yunet_without_calibration_k_is_null(tmp_path):
    haar = DistanceCalibrator(backend="haar")
    for distance, width in ((30.0, 280.0), (50.0, 150.0), (70.0, 90.0)):
        haar.add_sample(distance, width)
    haar.fit()
    cal_path = tmp_path / "calibration.json"
    haar.save(cal_path)

    log = _write_log(tmp_path / "s.csv", [_face_row(0.0)])
    generator = ReportGenerator(
        _config(tmp_path, backend="yunet"), calibration_path=cal_path
    )
    out = generator.generate(log, tmp_path / "reports")
    data = _read_json(out)
    assert data["session"]["calibration_k"] is None
