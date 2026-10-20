"""Heads-up display overlay for video frames."""

from typing import Optional

import cv2
import numpy as np

from detector import FaceBox

BOX_COLOR = (0, 255, 0)  # BGR green
TEXT_COLOR = (0, 255, 0)  # BGR green


class HUDOverlay:
    """Draw heads-up display overlay on video frames."""

    def draw(
        self,
        frame: np.ndarray,
        faces: list[FaceBox],
        fps: float,
        distance_cm: Optional[float] = None,
        distance_category: Optional[str] = None,
    ) -> np.ndarray:
        """Draw overlay on a copy of the frame.

        M2 scope: FPS counter, face count, face bounding boxes, distance value
        and distance category. Posture and brightness fields are added in M3.

        Args:
            frame: BGR image to draw on.
            faces: Detected face boxes.
            fps: Current processing FPS.
            distance_cm: Estimated distance in cm, or None if unavailable.
            distance_category: Distance category label, or None.

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

        if distance_cm is not None:
            category = distance_category or "unknown"
            distance_text = f"Distance: {distance_cm:.1f} cm [{category}]"
        else:
            distance_text = "Distance: -- cm [unknown]"
        cv2.putText(
            out,
            distance_text,
            (10, 75),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            TEXT_COLOR,
            2,
        )

        return out
