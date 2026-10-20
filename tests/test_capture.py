"""Tests for the unified video capture abstraction (capture.py)."""

import cv2
import numpy as np
import pytest

from capture import InputSource, VideoCapture

WIDTH = 160
HEIGHT = 120
NUM_FRAMES = 10


def _make_test_video(path, num_frames: int = NUM_FRAMES) -> None:
    """Write a small synthetic video file for camera-free tests."""
    writer = cv2.VideoWriter(
        str(path),
        cv2.VideoWriter_fourcc(*"MJPG"),
        10.0,
        (WIDTH, HEIGHT),
    )
    assert writer.isOpened(), "test fixture could not open VideoWriter"
    for i in range(num_frames):
        frame = np.full((HEIGHT, WIDTH, 3), (i * 20) % 255, dtype=np.uint8)
        writer.write(frame)
    writer.release()


@pytest.fixture
def test_video_path(tmp_path):
    """Create a synthetic video file in a temporary directory."""
    path = tmp_path / "test_video.avi"
    _make_test_video(path)
    return path


def test_capture_open_file(test_video_path):
    cap = VideoCapture(InputSource.FILE, path=test_video_path)
    assert cap.is_opened is True
    cap.release()


def test_capture_open_missing_file(tmp_path):
    missing = tmp_path / "does_not_exist.avi"
    with pytest.raises(FileNotFoundError):
        VideoCapture(InputSource.FILE, path=missing)


def test_capture_read_frame(test_video_path):
    cap = VideoCapture(InputSource.FILE, path=test_video_path)
    success, frame = cap.read()
    assert success is True
    assert isinstance(frame, np.ndarray)
    assert frame.shape == (HEIGHT, WIDTH, 3)
    cap.release()


def test_capture_read_eof(test_video_path):
    cap = VideoCapture(InputSource.FILE, path=test_video_path)
    frames_read = 0
    while True:
        success, frame = cap.read()
        if not success:
            break
        frames_read += 1
    assert frames_read >= NUM_FRAMES
    success, frame = cap.read()
    assert success is False
    assert frame is None
    cap.release()


def test_capture_release(test_video_path):
    cap = VideoCapture(InputSource.FILE, path=test_video_path)
    cap.release()
    assert cap.is_opened is False
    cap.release()  # second call must be safe
    assert cap.is_opened is False


def test_capture_open_camera(monkeypatch):
    captured_index = {}

    class FakeCapture:
        def __init__(self, index: int) -> None:
            self._opened = True

        def isOpened(self) -> bool:
            return self._opened

        def release(self) -> None:
            self._opened = False

    def fake_video_capture(index: int = 0):
        captured_index["index"] = index
        return FakeCapture(index)

    monkeypatch.setattr(cv2, "VideoCapture", fake_video_capture)

    cap = VideoCapture(InputSource.CAMERA, camera_index=0)
    assert cap.is_opened is True
    assert captured_index["index"] == 0
    cap.release()
