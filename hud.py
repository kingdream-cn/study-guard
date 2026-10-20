"""Heads-up display overlay for video frames."""

from typing import Optional

import cv2
import numpy as np

from metrics import FrameMetrics

BOX_COLOR = (0, 255, 0)  # BGR green
TEXT_COLOR = (0, 255, 0)  # BGR green
WARN_COLOR = (0, 0, 255)  # BGR red


class HUDOverlay:
    """Draw heads-up display overlay on video frames."""

    def draw(
        self,
        frame: np.ndarray,
        metrics: FrameMetrics,
        fps: float,
        face_count: int = 0,
        warning: Optional[str] = None,
        baseline_hint: Optional[str] = None,
    ) -> np.ndarray:
        """Draw overlay on a copy of the frame.

        M4 scope: FPS, face count, face box, distance, posture, brightness,
        an active reminder/warning banner (INTERFACE_SPEC §1.9 banner), and the
        posture-baseline prompt/status.

        Args:
            frame: BGR image to draw on.
            metrics: Computed frame metrics.
            fps: Current processing FPS.
            face_count: Number of faces detected in this frame.
            warning: Active warning text, or None.
            baseline_hint: Posture-baseline prompt/status, or None.

        Returns:
            New image with overlay drawn. Original frame is not modified.
        """
        out = frame.copy()

        if metrics.face_box is not None:
            f = metrics.face_box
            cv2.rectangle(out, (f.x, f.y), (f.x + f.w, f.y + f.h), BOX_COLOR, 2)

        cv2.putText(
            out, f"FPS: {fps:.1f}", (10, 25),
            cv2.FONT_HERSHEY_SIMPLEX, 0.6, TEXT_COLOR, 2,
        )
        cv2.putText(
            out, f"Faces: {face_count}", (10, 50),
            cv2.FONT_HERSHEY_SIMPLEX, 0.6, TEXT_COLOR, 2,
        )

        if metrics.distance_cm is not None:
            dist_text = (
                f"Distance: {metrics.distance_cm:.1f} cm "
                f"[{metrics.distance_category.value}]"
            )
        else:
            dist_text = "Distance: -- cm [unknown]"
        cv2.putText(
            out, dist_text, (10, 75),
            cv2.FONT_HERSHEY_SIMPLEX, 0.6, TEXT_COLOR, 2,
        )

        cv2.putText(
            out, f"Posture: {metrics.posture_score:.2f}", (10, 100),
            cv2.FONT_HERSHEY_SIMPLEX, 0.6, TEXT_COLOR, 2,
        )
        cv2.putText(
            out, f"Light: Lv.{metrics.brightness_level}", (10, 125),
            cv2.FONT_HERSHEY_SIMPLEX, 0.6, TEXT_COLOR, 2,
        )

        if baseline_hint:
            cv2.putText(
                out, baseline_hint, (10, out.shape[0] - 45),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 255), 2,
            )

        if warning:
            cv2.putText(
                out, warning, (10, out.shape[0] - 20),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, WARN_COLOR, 2,
            )

        return out
