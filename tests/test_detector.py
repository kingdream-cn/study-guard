"""Tests for the Haar/YuNet face detector wrapper (detector.py)."""

import os
from pathlib import Path

import cv2
import numpy as np
import pytest

from config import DEFAULT_CONFIG
from detector import (
    DEFAULT_BACKEND,
    DEFAULT_MIN_FACE_SIZE,
    DEFAULT_MIN_NEIGHBORS,
    DEFAULT_NMS_THRESHOLD,
    DEFAULT_SCALE_FACTOR,
    DEFAULT_SCORE_THRESHOLD,
    DEFAULT_TOP_K,
    FaceBox,
    FaceDetector,
    yunet_faces_to_boxes,
)

MODEL_PATH = Path(
    os.path.expanduser(DEFAULT_CONFIG["detection"]["model_path"])
)


def _require_model() -> Path:
    if not MODEL_PATH.is_file():
        pytest.skip(f"YuNet model not found: {MODEL_PATH}")
    return MODEL_PATH


def _raw_face(x: float, y: float, w: float, h: float) -> np.ndarray:
    """Build one YuNet-style (15,) row; landmarks/score are filled later."""
    row = np.zeros(15, dtype=np.float32)
    row[0:4] = (x, y, w, h)
    row[14] = 0.9
    return row


def test_face_box_center():
    assert FaceBox(10, 20, 100, 80).center == (60, 60)


def test_face_box_area():
    assert FaceBox(0, 0, 100, 80).area == 8000


def test_detector_detect_no_faces():
    detector = FaceDetector()
    blank = np.zeros((240, 320, 3), dtype=np.uint8)
    assert detector.detect(blank) == []


def test_detector_detect_faces():
    """Verify detection results are converted to FaceBox objects.

    This test injects a fake cascade to exercise the wrapper's conversion
    logic (grayscale conversion + raw detection -> FaceBox mapping) without
    requiring a real face image. Real-face detection is covered by the manual
    video/camera acceptance runs.
    """

    class FakeCascade:
        def detectMultiScale(self, gray, scaleFactor, minNeighbors, minSize):
            return np.array([[10, 20, 100, 80]], dtype=np.int32)

    detector = FaceDetector()
    detector._cascade = FakeCascade()  # noqa: SLF001 - test seam

    frame = np.zeros((240, 320, 3), dtype=np.uint8)
    faces = detector.detect(frame)

    assert len(faces) == 1
    assert isinstance(faces[0], FaceBox)
    assert (faces[0].x, faces[0].y, faces[0].w, faces[0].h) == (10, 20, 100, 80)


def test_detector_defaults_match_module_constants():
    detector = FaceDetector()
    assert detector.scale_factor == DEFAULT_SCALE_FACTOR
    assert detector.min_neighbors == DEFAULT_MIN_NEIGHBORS
    assert detector.min_face_size == DEFAULT_MIN_FACE_SIZE


def test_detector_accepts_custom_parameters():
    detector = FaceDetector(scale_factor=1.3, min_neighbors=7, min_face_size=60)
    assert detector.scale_factor == 1.3
    assert detector.min_neighbors == 7
    assert detector.min_face_size == 60


def test_detector_forwards_parameters_to_cascade():
    """Verify detect() passes instance parameters (not module constants)."""

    class RecordingCascade:
        def __init__(self):
            self.calls = []

        def detectMultiScale(self, gray, scaleFactor, minNeighbors, minSize):
            self.calls.append((scaleFactor, minNeighbors, minSize))
            return []

    cascade = RecordingCascade()
    detector = FaceDetector(scale_factor=1.2, min_neighbors=8, min_face_size=40)
    detector._cascade = cascade  # noqa: SLF001 - test seam

    frame = np.zeros((240, 320, 3), dtype=np.uint8)
    assert detector.detect(frame) == []
    assert cascade.calls == [(1.2, 8, (40, 40))]


def test_detector_backend_defaults_to_haar():
    detector = FaceDetector()
    assert DEFAULT_BACKEND == "haar"
    assert detector.backend == "haar"
    assert detector.model_path is None


def test_haar_backend_does_not_create_yunet(monkeypatch):
    """The default Haar path must not touch any YuNet code."""

    def fail(*args, **kwargs):
        raise AssertionError("YuNet must not be created for the Haar backend")

    monkeypatch.setattr(cv2, "FaceDetectorYN_create", fail)
    detector = FaceDetector()
    blank = np.zeros((240, 320, 3), dtype=np.uint8)
    assert detector.detect(blank) == []


def test_invalid_backend_rejected():
    with pytest.raises(ValueError, match="Unknown detector backend"):
        FaceDetector(backend="mediapipe")


def test_yunet_backend_requires_model_path():
    with pytest.raises(RuntimeError, match="model_path"):
        FaceDetector(backend="yunet")


def test_yunet_backend_missing_model_file_raises(tmp_path):
    missing = tmp_path / "missing.onnx"
    with pytest.raises(RuntimeError) as excinfo:
        FaceDetector(backend="yunet", model_path=str(missing))
    assert str(missing) in str(excinfo.value)


def test_yunet_boxes_none_returns_empty():
    assert yunet_faces_to_boxes(None, (320, 240), (320, 240)) == []


def test_yunet_boxes_empty_array_returns_empty():
    empty = np.zeros((0, 15), dtype=np.float32)
    assert yunet_faces_to_boxes(empty, (320, 240), (320, 240)) == []


def test_yunet_boxes_identity_scale():
    faces = np.stack([_raw_face(10.0, 20.0, 30.0, 40.0)])
    boxes = yunet_faces_to_boxes(faces, (320, 240), (320, 240))
    assert len(boxes) == 1
    assert isinstance(boxes[0], FaceBox)
    assert (boxes[0].x, boxes[0].y, boxes[0].w, boxes[0].h) == (10, 20, 30, 40)


def test_yunet_boxes_uniform_scale():
    faces = np.stack([_raw_face(10.0, 20.0, 30.0, 40.0)])
    boxes = yunet_faces_to_boxes(faces, (320, 240), (640, 480))
    assert (boxes[0].x, boxes[0].y, boxes[0].w, boxes[0].h) == (20, 40, 60, 80)


def test_yunet_boxes_non_uniform_scale():
    # sx = 800/320 = 2.5, sy = 360/240 = 1.5
    faces = np.stack([_raw_face(10.0, 20.0, 30.0, 40.0)])
    boxes = yunet_faces_to_boxes(faces, (320, 240), (800, 360))
    assert (boxes[0].x, boxes[0].y, boxes[0].w, boxes[0].h) == (
        25,
        30,
        75,
        60,
    )


def test_yunet_boxes_use_int_round():
    """Rounding must be exactly ``int(round(v))`` (banker's rounding)."""
    faces = np.stack([_raw_face(10.5, 11.5, 20.5, 21.5)])
    boxes = yunet_faces_to_boxes(faces, (100, 100), (100, 100))
    assert (boxes[0].x, boxes[0].y, boxes[0].w, boxes[0].h) == (
        10,
        12,
        20,
        22,
    )


def test_yunet_boxes_clamp_to_frame_and_drop_empty():
    faces = np.stack(
        [
            _raw_face(-10.0, -5.0, 200.0, 50.0),
            _raw_face(90.0, 90.0, 50.0, 50.0),
            _raw_face(200.0, 20.0, 50.0, 50.0),
        ]
    )
    boxes = yunet_faces_to_boxes(faces, (100, 100), (100, 100))
    assert [(b.x, b.y, b.w, b.h) for b in boxes] == [
        (0, 0, 100, 50),
        (90, 90, 10, 10),
    ]
    for box in boxes:
        assert box.x >= 0 and box.y >= 0
        assert box.x + box.w <= 100 and box.y + box.h <= 100


def test_yunet_boxes_ignore_landmarks_and_score():
    row = _raw_face(10.0, 20.0, 30.0, 40.0)
    row[4:14] = 999.0
    row[14] = 0.01
    boxes = yunet_faces_to_boxes(np.stack([row]), (100, 100), (100, 100))
    assert (boxes[0].x, boxes[0].y, boxes[0].w, boxes[0].h) == (
        10,
        20,
        30,
        40,
    )


def test_yunet_boxes_invalid_size_raises():
    faces = np.stack([_raw_face(10.0, 20.0, 30.0, 40.0)])
    with pytest.raises(ValueError):
        yunet_faces_to_boxes(faces, (0, 240), (320, 240))


def test_yunet_model_path_expands_user():
    model = _require_model()
    home_path = DEFAULT_CONFIG["detection"]["model_path"]
    assert home_path.startswith("~")
    detector = FaceDetector(backend="yunet", model_path=home_path)
    assert detector.model_path == model


def test_yunet_blank_frame_returns_empty_list():
    model = _require_model()
    detector = FaceDetector(backend="yunet", model_path=str(model))
    blank = np.zeros((240, 320, 3), dtype=np.uint8)
    assert detector.detect(blank) == []


def test_yunet_frame_size_change_updates_input_size():
    model = _require_model()
    detector = FaceDetector(backend="yunet", model_path=str(model))
    assert detector.detect(np.zeros((240, 320, 3), dtype=np.uint8)) == []
    assert detector.detect(np.zeros((480, 640, 3), dtype=np.uint8)) == []


def test_yunet_boxes_kept_when_exactly_min_size():
    faces = np.stack([_raw_face(10.0, 20.0, 30.0, 30.0)])
    boxes = yunet_faces_to_boxes(faces, (100, 100), (100, 100), min_size=30)
    assert [(b.x, b.y, b.w, b.h) for b in boxes] == [(10, 20, 30, 30)]


def test_yunet_boxes_width_one_below_min_size_dropped():
    faces = np.stack([_raw_face(10.0, 20.0, 29.0, 30.0)])
    boxes = yunet_faces_to_boxes(faces, (100, 100), (100, 100), min_size=30)
    assert boxes == []


def test_yunet_boxes_height_one_below_min_size_dropped():
    faces = np.stack([_raw_face(10.0, 20.0, 30.0, 29.0)])
    boxes = yunet_faces_to_boxes(faces, (100, 100), (100, 100), min_size=30)
    assert boxes == []


def test_yunet_boxes_multi_drops_only_small_and_keeps_order():
    faces = np.stack(
        [
            _raw_face(5.0, 5.0, 40.0, 40.0),
            _raw_face(50.0, 5.0, 10.0, 40.0),
            _raw_face(5.0, 50.0, 40.0, 10.0),
            _raw_face(50.0, 50.0, 30.0, 30.0),
        ]
    )
    boxes = yunet_faces_to_boxes(faces, (100, 100), (100, 100), min_size=30)
    assert [(b.x, b.y, b.w, b.h) for b in boxes] == [
        (5, 5, 40, 40),
        (50, 50, 30, 30),
    ]


def test_yunet_boxes_clamp_then_min_size():
    """Clamping runs before the size test: the visible box size is judged."""
    # Reported 40 px wide but starting at x=90 in a 100 px frame: clamping
    # leaves only 10 px visible, so min_size=30 must drop it.
    faces = np.stack([_raw_face(90.0, 10.0, 40.0, 40.0)])
    assert (
        yunet_faces_to_boxes(faces, (100, 100), (100, 100), min_size=30) == []
    )
    # Without the filter it survives as the 10x40 clipped box.
    assert [
        (b.x, b.y, b.w, b.h)
        for b in yunet_faces_to_boxes(faces, (100, 100), (100, 100))
    ] == [(90, 10, 10, 40)]
    # min_size=10 keeps it (the clipped width is exactly the minimum).
    assert [
        (b.x, b.y, b.w, b.h)
        for b in yunet_faces_to_boxes(faces, (100, 100), (100, 100), min_size=10)
    ] == [(90, 10, 10, 40)]


def test_yunet_boxes_negative_min_size_raises():
    faces = np.stack([_raw_face(10.0, 20.0, 30.0, 30.0)])
    with pytest.raises(ValueError):
        yunet_faces_to_boxes(faces, (100, 100), (100, 100), min_size=-1)
