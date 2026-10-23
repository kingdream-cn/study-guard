"""Haar Cascade face detection wrapper."""

from dataclasses import dataclass
from typing import Optional

import cv2
import numpy as np

DEFAULT_CASCADE_PATH = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"

# Detection parameter defaults. These mirror the ``detection`` section of
# ``configs/default.json``; AppConfig supplies runtime values in ``main.py``.
DEFAULT_SCALE_FACTOR = 1.1
DEFAULT_MIN_NEIGHBORS = 5
DEFAULT_MIN_FACE_SIZE = 30


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


class FaceDetector:
    """Haar Cascade face detector wrapper."""

    def __init__(
        self,
        cascade_path: Optional[str] = None,
        scale_factor: float = DEFAULT_SCALE_FACTOR,
        min_neighbors: int = DEFAULT_MIN_NEIGHBORS,
        min_face_size: int = DEFAULT_MIN_FACE_SIZE,
    ) -> None:
        """Initialize with OpenCV's default Haar cascade.

        Args:
            cascade_path: Optional path to a custom cascade XML. Defaults to
                OpenCV's built-in frontal face cascade.
            scale_factor: Detection pyramid scale factor (default 1.1).
            min_neighbors: Minimum neighbors per candidate rectangle (default 5).
            min_face_size: Minimum face size in pixels, both width and height
                (default 30).

        Raises:
            RuntimeError: If the cascade XML cannot be loaded.
        """
        path = cascade_path or DEFAULT_CASCADE_PATH
        self._cascade = cv2.CascadeClassifier(path)
        if self._cascade.empty():
            raise RuntimeError(f"Failed to load Haar cascade from: {path}")

        self.scale_factor = scale_factor
        self.min_neighbors = min_neighbors
        self.min_face_size = min_face_size

    def detect(self, frame: np.ndarray) -> list[FaceBox]:
        """Detect faces in a BGR frame.

        Args:
            frame: BGR image as a numpy array.

        Returns:
            List of :class:`FaceBox` detections. Empty list if no faces found.
        """
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
