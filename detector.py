"""Haar Cascade and YuNet face detection wrappers."""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import cv2
import numpy as np

DEFAULT_CASCADE_PATH = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"

# Detection parameter defaults. These mirror the ``detection`` section of
# ``configs/default.json``; AppConfig supplies runtime values in ``main.py``.
DEFAULT_SCALE_FACTOR = 1.1
DEFAULT_MIN_NEIGHBORS = 5
DEFAULT_MIN_FACE_SIZE = 30
DEFAULT_BACKEND = "haar"

# Official OpenCV Zoo YuNet demo defaults (score 0.9 / NMS 0.3 / top_k 5000).
DEFAULT_SCORE_THRESHOLD = 0.9
DEFAULT_NMS_THRESHOLD = 0.3
DEFAULT_TOP_K = 5000

# Only used to create the detector; each frame's real size is applied with
# FaceDetectorYN.setInputSize() before inference.
YUNET_INITIAL_INPUT_SIZE = (320, 320)


@dataclass
class FaceBox:
    """A detected face bounding box."""

    x: int  # Top-left x
    y: int  # Top-left y
    w: int  # Width
    h: int  # Height

    @property
    def center(self) -> tuple[int, int]:
        """Center point of the bounding box."""
        return (self.x + self.w // 2, self.y + self.h // 2)

    @property
    def area(self) -> int:
        """Area of the bounding box in pixels."""
        return self.w * self.h


def yunet_faces_to_boxes(
    faces: Optional[np.ndarray],
    input_size: tuple[int, int],
    frame_size: tuple[int, int],
    min_size: int = 0,
) -> list[FaceBox]:
    """Convert YuNet detections to ``FaceBox`` objects in frame coordinates.

    YuNet returns a ``(N, 15)`` float32 array in the coordinate system of the
    image passed to ``detect`` (or ``None`` when no face is found). Landmarks
    and the score column are intentionally ignored in O2-A; only columns 0-3
    (``x, y, w, h``) are used.

    The conversion is done here, independent of OpenCV and the camera, so it
    can be unit-tested. In the current production path ``input_size`` equals
    ``frame_size`` (scale 1:1), but non-1:1 scales are supported and tested.

    Each coordinate is rounded with ``int(round(value))`` before clamping.
    Results are clamped to the frame (``x >= 0``, ``y >= 0``,
    ``x + w <= frame_w``, ``y + h <= frame_h``); boxes that collapse to zero
    width or height are dropped.

    Filtering happens **after** clamping, so the size test applies to the
    visible box: a box that YuNet reports partly outside the frame is judged by
    the part actually inside it. The test itself mirrors Haar's ``minSize``:
    a box is kept when ``w >= min_size and h >= min_size`` (equal is kept).

    Args:
        faces: Raw YuNet output of shape ``(N, 15)``, or ``None`` when no face
            was detected.
        input_size: ``(width, height)`` of the image passed to ``detect``.
        frame_size: ``(width, height)`` of the original frame.
        min_size: Minimum box width and height in frame pixels (default 0,
            no filtering). Matches Haar's ``min_face_size`` semantics.

    Returns:
        List of :class:`FaceBox` in the original frame coordinate system.

    Raises:
        ValueError: If any size component is not positive, or ``min_size`` is
            negative.
    """
    if faces is None or len(faces) == 0:
        return []

    in_w, in_h = int(input_size[0]), int(input_size[1])
    out_w, out_h = int(frame_size[0]), int(frame_size[1])
    if in_w <= 0 or in_h <= 0 or out_w <= 0 or out_h <= 0:
        raise ValueError("input_size and frame_size must be positive")
    if min_size < 0:
        raise ValueError("min_size must be >= 0")

    scale_x = out_w / float(in_w)
    scale_y = out_h / float(in_h)
    boxes: list[FaceBox] = []
    for face in faces:
        x = int(round(float(face[0]) * scale_x))
        y = int(round(float(face[1]) * scale_y))
        w = int(round(float(face[2]) * scale_x))
        h = int(round(float(face[3]) * scale_y))

        x = max(0, min(x, out_w))
        y = max(0, min(y, out_h))
        w = max(0, min(w, out_w - x))
        h = max(0, min(h, out_h - y))
        if w <= 0 or h <= 0:
            continue
        if w < min_size or h < min_size:
            continue
        boxes.append(FaceBox(x, y, w, h))
    return boxes


class FaceDetector:
    """Face detector with selectable Haar or YuNet backend.

    The default backend is Haar and preserves the previous behavior. YuNet is
    optional and requires a local ONNX model; switching backends changes the
    face-box width definition, so the Haar-based calibration k is not
    interchangeable (O2-B).
    """

    def __init__(
        self,
        cascade_path: Optional[str] = None,
        scale_factor: float = DEFAULT_SCALE_FACTOR,
        min_neighbors: int = DEFAULT_MIN_NEIGHBORS,
        min_face_size: int = DEFAULT_MIN_FACE_SIZE,
        backend: str = DEFAULT_BACKEND,
        model_path: Optional[str] = None,
        score_threshold: float = DEFAULT_SCORE_THRESHOLD,
        nms_threshold: float = DEFAULT_NMS_THRESHOLD,
        top_k: int = DEFAULT_TOP_K,
    ) -> None:
        """Initialize the requested detector backend.

        Args:
            cascade_path: Optional path to a custom Haar cascade XML. Defaults
                to OpenCV's built-in frontal face cascade.
            scale_factor: Haar detection pyramid scale factor (default 1.1).
            min_neighbors: Minimum Haar neighbors per candidate rectangle
                (default 5).
            min_face_size: Minimum face size in pixels, both width and height
                (default 30). Applied to both backends: Haar via ``minSize``,
                YuNet via ``yunet_faces_to_boxes(min_size=...)``.
            backend: ``"haar"`` (default) or ``"yunet"``.
            model_path: Local path to the YuNet ONNX model. ``~`` is expanded.
                Required only when ``backend="yunet"``.
            score_threshold: YuNet score threshold (default 0.9).
            nms_threshold: YuNet NMS threshold (default 0.3).
            top_k: YuNet boxes kept before NMS (default 5000).

        Raises:
            ValueError: If ``backend`` is not ``"haar"`` or ``"yunet"``.
            RuntimeError: If the Haar cascade or YuNet model cannot be loaded.
        """
        if backend not in ("haar", "yunet"):
            raise ValueError(
                f"Unknown detector backend: {backend!r} "
                "(expected 'haar' or 'yunet')"
            )

        self.backend = backend
        self.scale_factor = scale_factor
        self.min_neighbors = min_neighbors
        self.min_face_size = min_face_size
        self.score_threshold = score_threshold
        self.nms_threshold = nms_threshold
        self.top_k = top_k
        self.model_path = (
            Path(os.path.expanduser(model_path)) if model_path else None
        )
        self._cascade: Optional[cv2.CascadeClassifier] = None
        self._yunet: Optional[cv2.FaceDetectorYN] = None
        self._yunet_input_size: Optional[tuple[int, int]] = None

        if backend == "haar":
            path = cascade_path or DEFAULT_CASCADE_PATH
            self._cascade = cv2.CascadeClassifier(path)
            if self._cascade.empty():
                raise RuntimeError(f"Failed to load Haar cascade from: {path}")
            return

        if self.model_path is None:
            raise RuntimeError(
                "YuNet backend requires a model_path (detection.model_path)"
            )
        if not self.model_path.is_file():
            raise RuntimeError(
                f"Failed to load YuNet model from: {self.model_path}"
            )
        self._yunet = cv2.FaceDetectorYN_create(
            str(self.model_path),
            "",
            YUNET_INITIAL_INPUT_SIZE,
            score_threshold,
            nms_threshold,
            top_k,
        )

    def detect(self, frame: np.ndarray) -> list[FaceBox]:
        """Detect faces in a BGR frame using the configured backend.

        Args:
            frame: BGR image as a numpy array.

        Returns:
            List of :class:`FaceBox` detections in frame coordinates. Empty
            list if no faces are found.
        """
        if self.backend == "yunet":
            return self._detect_yunet(frame)

        assert self._cascade is not None
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        detections = self._cascade.detectMultiScale(
            gray,
            scaleFactor=self.scale_factor,
            minNeighbors=self.min_neighbors,
            minSize=(self.min_face_size, self.min_face_size),
        )
        return [
            FaceBox(int(x), int(y), int(w), int(h))
            for (x, y, w, h) in detections
        ]

    def _detect_yunet(self, frame: np.ndarray) -> list[FaceBox]:
        """Run YuNet on the native frame and convert boxes back to it."""
        assert self._yunet is not None
        height, width = frame.shape[:2]
        size = (int(width), int(height))
        if size != self._yunet_input_size:
            self._yunet.setInputSize(size)
            self._yunet_input_size = size
        _, faces = self._yunet.detect(frame)
        return yunet_faces_to_boxes(
            faces,
            input_size=size,
            frame_size=size,
            min_size=self.min_face_size,
        )
