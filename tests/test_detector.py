"""Tests for the Haar Cascade face detector wrapper (detector.py)."""

import numpy as np

from detector import FaceBox, FaceDetector


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
