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
        active_anomalies: Optional[list[str]] = None,
    ) -> np.ndarray:
        """Draw overlay on a copy of the frame.

        M3 scope: FPS, face count, face box, distance, posture score,
        brightness level, and an anomaly banner. The reminder banner in
        INTERFACE_SPEC §1.9 will be wired to reminder events in M4.

        Args:
            frame: BGR image to draw on.
            metrics: Computed frame metrics.
            fps: Current processing FPS.
            face_count: Number of faces detected in this frame.
            active_anomalies: Metric names currently in a warning state.

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

        if active_anomalies:
            banner = "WARNING: " + ", ".join(active_anomalies)
            cv2.putText(
                out, banner, (10, out.shape[0] - 20),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, WARN_COLOR, 2,
            )

        return out
