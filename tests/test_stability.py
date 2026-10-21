"""M6 stability and edge-case tests."""

import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

import cv2
import numpy as np
import pytest

from calibrator import DistanceCalibrator
from capture import InputSource, VideoCapture
from config import AppConfig
from detector import FaceDetector
from logger import SessionLogger
from metrics import DistanceCategory, FrameMetrics, MetricsCalculator
from reminder import ReminderManager, ReminderType

PROJECT_ROOT = Path(__file__).resolve().parents[1]
MAIN = PROJECT_ROOT / "main.py"


def _make_video(path: Path, num_frames: int, width: int = 320, height: int = 240) -> Path:
    """Write a synthetic video with plain (face-free) frames."""
    writer = cv2.VideoWriter(
        str(path), cv2.VideoWriter_fourcc(*"MJPG"), 15.0, (width, height)
    )
    assert writer.isOpened(), "could not open VideoWriter"
    for i in range(num_frames):
        frame = np.full((height, width, 3), 0, dtype=np.uint8)
        cv2.rectangle(frame, (40, 40), (120, 160), (255, 255, 255), -1)
        writer.write(frame)
    writer.release()
    return path


def _write_config(tmp_path: Path, log_dir: Path, report_dir: Path) -> Path:
    cfg = tmp_path / "config.json"
    cfg.write_text(
        json.dumps(
            {
                "logging": {"interval_sec": 0.05, "log_dir": str(log_dir)},
                "report": {"output_dir": str(report_dir), "generate_charts": False},
            }
        ),
        encoding="utf-8",
    )
    return cfg


class _FakeClock:
    def __init__(self) -> None:
        self.t = 0.0

    def __call__(self) -> float:
        return self.t

    def advance(self, seconds: float) -> None:
        self.t += seconds


def _metrics(face: bool) -> FrameMetrics:
    return FrameMetrics(
        timestamp=0.0,
        distance_cm=50.0 if face else None,
        distance_category=DistanceCategory.NORMAL if face else DistanceCategory.UNKNOWN,
        posture_score=0.8 if face else 0.0,
        brightness_level=3,
        face_detected=face,
        face_box=None,
    )


# --- edge cases ---


def test_zero_length_video(tmp_path):
    video = _make_video(tmp_path / "zero.avi", 0)
    try:
        capture = VideoCapture(InputSource.FILE, path=video)
    except RuntimeError:
        return  # not openable -> clean error path handled in main

    success, frame = capture.read()
    assert success is False
    assert frame is None
    capture.release()


def test_corrupted_video_file(tmp_path):
    bad = tmp_path / "corrupt.mp4"
    bad.write_bytes(b"\x00\x01\x02\x03" * 256)
    with pytest.raises(RuntimeError):
        VideoCapture(InputSource.FILE, path=bad)


def test_all_frames_no_face(tmp_path):
    video = _make_video(tmp_path / "noface.avi", 20)
    log_dir = tmp_path / "logs"
    report_dir = tmp_path / "reports"
    cfg = _write_config(tmp_path, log_dir, report_dir)

    proc = subprocess.run(
        [
            sys.executable, str(MAIN),
            "--source", "file", "--path", str(video),
            "--config", str(cfg), "--headless",
        ],
        capture_output=True, text=True, timeout=60, cwd=str(PROJECT_ROOT),
    )
    assert proc.returncode == 0, proc.stderr

    reports = list(report_dir.glob("session_summary_*.json"))
    assert len(reports) == 1
    data = json.loads(reports[0].read_text(encoding="utf-8"))
    assert data["insufficient_data"] is True


def test_rapid_face_appear_disappear():
    config = AppConfig(PROJECT_ROOT / "configs" / "default.json")
    clock = _FakeClock()
    manager = ReminderManager(config, clock=clock)

    events = []
    for i in range(50):
        events += manager.update(_metrics(face=(i % 2 == 0)))
        clock.advance(0.2)

    # Gaps are 0.2 s, far below face_lost_sec, so no face-lost warning.
    assert all(e.reminder_type is not ReminderType.FACE_LOST for e in events)
    # Effective study time only counts the ~half of updates with a face.
    assert manager.effective_study_time == pytest.approx(4.8, abs=0.2)


def test_keyboard_interrupt(tmp_path):
    video = _make_video(tmp_path / "long.avi", 800)
    log_dir = tmp_path / "logs"
    report_dir = tmp_path / "reports"
    cfg = _write_config(tmp_path, log_dir, report_dir)

    proc = subprocess.Popen(
        [
            sys.executable, str(MAIN),
            "--source", "file", "--path", str(video),
            "--config", str(cfg), "--headless",
        ],
        cwd=str(PROJECT_ROOT),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    deadline = time.monotonic() + 30
    while not list(log_dir.glob("session_*.csv")) and time.monotonic() < deadline:
        if proc.poll() is not None:
            break
        time.sleep(0.05)

    time.sleep(0.2)
    if proc.poll() is None:
        proc.send_signal(signal.SIGINT)

    try:
        proc.communicate(timeout=60)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.communicate()
        pytest.fail("process did not exit after SIGINT")

    assert proc.returncode == 0
    # A partial report must still be written on interrupt.
    assert len(list(report_dir.glob("session_summary_*.json"))) == 1


def test_config_file_deleted_mid_session(tmp_path):
    cfg_path = tmp_path / "config.json"
    cfg_path.write_text(json.dumps({}), encoding="utf-8")
    config = AppConfig(cfg_path)

    cfg_path.unlink()  # deleted while running; config is already in memory
    assert config.get("reminder.eye_care_interval_min") > 0


def test_log_directory_not_writable(tmp_path):
    if os.name == "posix" and os.geteuid() == 0:
        pytest.skip("running as root; directory permissions are not enforced")

    readonly = tmp_path / "readonly"
    readonly.mkdir()
    readonly.chmod(0o555)

    try:
        config = AppConfig(_write_config(tmp_path, readonly, tmp_path / "reports"))
        with pytest.raises(OSError):
            SessionLogger(config, readonly)
    finally:
        readonly.chmod(0o755)


def test_very_large_frame_4k():
    frame = np.full((2160, 3840, 3), 128, dtype=np.uint8)
    detector = FaceDetector()
    calculator = MetricsCalculator(DistanceCalibrator())

    start = time.perf_counter()
    faces = detector.detect(frame)
    metrics = calculator.compute(frame, faces)
    elapsed = time.perf_counter() - start

    assert isinstance(faces, list)
    assert 0.0 <= metrics.posture_score <= 1.0
    assert elapsed < 10.0
    print(f"\n[INFO] 4K frame detect+compute: {elapsed * 1000:.1f} ms")
