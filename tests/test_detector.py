"""Tests for the Haar Cascade face detector wrapper (detector.py)."""

import numpy as np

from detector import (
    DEFAULT_MIN_FACE_SIZE,
    DEFAULT_MIN_NEIGHBORS,
    DEFAULT_SCALE_FACTOR,
    FaceBox,
    FaceDetector,
)


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
