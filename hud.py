"""Heads-up display overlay for video frames."""

import cv2
import numpy as np

from detector import FaceBox

BOX_COLOR = (0, 255, 0)  # BGR green
TEXT_COLOR = (0, 255, 0)  # BGR green


class HUDOverlay:
    """Draw heads-up display overlay on video frames."""

    def draw(self, frame: np.ndarray, faces: list[FaceBox], fps: float) -> np.ndarray:
        """Draw overlay on a copy of the frame.

        M1 scope: FPS counter, face count, and face bounding boxes. Additional
        fields (distance, posture, brightness, reminders) are added in later
        milestones once those metrics exist.

        Args:
            frame: BGR image to draw on.
            faces: Detected face boxes.
            fps: Current processing FPS.

        Returns:
            New image with overlay drawn. Original frame is not modified.
        """
        out = frame.copy()

        for face in faces:
            cv2.rectangle(
                out,
                (face.x, face.y),
                (face.x + face.w, face.y + face.h),
                BOX_COLOR,
                2,
            )

        cv2.putText(
            out,
            f"FPS: {fps:.1f}",
            (10, 25),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            TEXT_COLOR,
            2,
        )
        cv2.putText(
            out,
            f"Faces: {len(faces)}",
            (10, 50),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            TEXT_COLOR,
            2,
        )

        return out
