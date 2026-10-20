"""Unified video input abstraction for file and camera sources."""

from enum import Enum
from pathlib import Path
from typing import Optional

import cv2
import numpy as np


class InputSource(Enum):
    """Available video input sources."""

    FILE = "file"
    CAMERA = "camera"


class VideoCapture:
    """Unified video input abstraction for file and camera sources.

    Provides a single interface over ``cv2.VideoCapture`` so the rest of the
    application does not need to care whether the frames come from a local
    video file or a webcam.
    """

    def __init__(
        self,
        source: InputSource,
        path: Optional[Path] = None,
        camera_index: int = 0,
    ) -> None:
        """Initialize a video capture for the requested source.

        Args:
            source: ``InputSource.FILE`` or ``InputSource.CAMERA``.
            path: Path to the video file (required when source is FILE).
            camera_index: Camera device index (default 0).

        Raises:
            ValueError: If source is FILE but path is None.
            FileNotFoundError: If the video file does not exist.
            RuntimeError: If the file or camera device cannot be opened.
        """
        if source is InputSource.FILE:
            if path is None:
                raise ValueError("path is required when source is InputSource.FILE")
            file_path = Path(path)
            if not file_path.exists():
                raise FileNotFoundError(f"Video file not found: {file_path}")
            self._capture = cv2.VideoCapture(str(file_path))
        else:
            self._capture = cv2.VideoCapture(camera_index)

        if not self._capture.isOpened():
            self._capture.release()
            if source is InputSource.FILE:
                raise RuntimeError(f"Failed to open video file: {path}")
            raise RuntimeError(
                f"Failed to open camera device at index {camera_index}"
            )

    def read(self) -> tuple[bool, Optional[np.ndarray]]:
        """Read the next frame from the source.

        Returns:
            Tuple of ``(success, frame)``. ``frame`` is None if the read failed.
        """
        success, frame = self._capture.read()
        return success, frame

    @property
    def fps(self) -> float:
        """Reported FPS of the video source. Returns 0.0 if unavailable."""
        value = self._capture.get(cv2.CAP_PROP_FPS)
        return float(value) if value and value > 0 else 0.0

    @property
    def frame_width(self) -> int:
        """Frame width in pixels."""
        return int(self._capture.get(cv2.CAP_PROP_FRAME_WIDTH))

    @property
    def frame_height(self) -> int:
        """Frame height in pixels."""
        return int(self._capture.get(cv2.CAP_PROP_FRAME_HEIGHT))

    @property
    def is_opened(self) -> bool:
        """Whether the capture device is currently open."""
        return self._capture.isOpened()

    def release(self) -> None:
        """Release the capture device. Safe to call multiple times."""
        self._capture.release()
