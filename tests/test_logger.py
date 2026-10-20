"""Tests for session CSV logging (logger.py)."""

import csv
from pathlib import Path

from config import AppConfig
from detector import FaceBox
from logger import SessionLogger
from metrics import DistanceCategory, FrameMetrics
from reminder import ReminderEvent, ReminderType

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = PROJECT_ROOT / "configs" / "default.json"


def _metrics(timestamp: float, face: bool = True) -> FrameMetrics:
    return FrameMetrics(
        timestamp=timestamp,
        distance_cm=50.0 if face else None,
        distance_category=(
            DistanceCategory.NORMAL if face else DistanceCategory.UNKNOWN
        ),
        posture_score=0.8,
        brightness_level=3,
        face_detected=face,
        face_box=FaceBox(10, 20, 100, 80) if face else None,
    )


def test_csv_log_interval(tmp_path):
    logger = SessionLogger(AppConfig(CONFIG_PATH), tmp_path)
    for timestamp in (0.0, 0.5, 1.0, 1.5):
        logger.log(_metrics(timestamp), [])
    path = logger.close()

    with path.open(newline="", encoding="utf-8") as fh:
        rows = list(csv.reader(fh))
    # Header + writes at t=0.0 and t=1.0 only (interval 1.0 s).
    assert len(rows) == 3


def test_csv_log_format(tmp_path):
    logger = SessionLogger(AppConfig(CONFIG_PATH), tmp_path)
    event = ReminderEvent(ReminderType.DISTANCE_WARNING, "adjust", 0.0)
    logger.log(_metrics(0.0), [event])
    path = logger.close()

    with path.open(newline="", encoding="utf-8") as fh:
        rows = list(csv.reader(fh))

    header, row = rows[0], rows[1]
    assert header == [
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
    assert row[1] == "1"
    assert row[6] == "50.00"
    assert row[10] == "distance_warning"
