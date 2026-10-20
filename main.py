"""StudyGuard application entry point (M3: behavior metrics & anomaly state machine)."""

import argparse
import statistics
import sys
import time
from pathlib import Path
from typing import Optional

import cv2

from calibrator import CalibrationError, DistanceCalibrator
from capture import InputSource, VideoCapture
from detector import FaceDetector
from hud import HUDOverlay
from metrics import (
    COOLDOWN_SEC,
    DISTANCE_ANOMALY_THRESHOLD_SEC,
    POSTURE_ANOMALY_SCORE,
    POSTURE_ANOMALY_THRESHOLD_SEC,
    AnomalyTracker,
    DistanceCategory,
    MetricsCalculator,
)

WINDOW_NAME = "StudyGuard"
PROJECT_ROOT = Path(__file__).resolve().parent
CALIBRATION_FILE = PROJECT_ROOT / "configs" / "calibration.json"

# Number of frames to collect (and median-filter) for one calibration sample.
CALIBRATION_FRAMES = 30


def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    """Parse command-line arguments.

    Args:
        argv: Optional argument list (defaults to ``sys.argv[1:]``).

    Returns:
        Parsed arguments namespace.
    """
    parser = argparse.ArgumentParser(
        description="StudyGuard - behavior metrics & anomaly state machine (M3)"
    )
    parser.add_argument(
        "--source",
        choices=["file", "camera"],
        default="camera",
        help="input source (default: camera)",
    )
    parser.add_argument(
        "--path",
        type=str,
        default=None,
        help="video file path (required when --source file)",
    )
    parser.add_argument(
        "--camera-index",
        type=int,
        default=0,
        help="camera device index (default: 0)",
    )
    return parser.parse_args(argv)


def collect_sample(
    capture: VideoCapture, detector: FaceDetector
) -> Optional[tuple[float, float]]:
    """Collect one calibration sample at a user-specified distance.

    Prompts for the known distance, then reads ``CALIBRATION_FRAMES`` frames,
    taking the median face width as the stable measurement.

    Args:
        capture: Open video capture.
        detector: Face detector.

    Returns:
        Tuple of ``(distance_cm, median_face_width_px)``, or None if input was
        invalid or too few valid frames were collected.
    """
    try:
        distance_cm = float(input("Known distance (cm): "))
    except (EOFError, ValueError):
        print("[ERROR] Invalid distance input.", file=sys.stderr)
        return None
    if distance_cm <= 0:
        print("[ERROR] Distance must be positive.", file=sys.stderr)
        return None

    widths: list[float] = []
    while len(widths) < CALIBRATION_FRAMES:
        success, frame = capture.read()
        if not success or frame is None:
            break
        faces = detector.detect(frame)
        if faces:
            largest = max(faces, key=lambda f: f.area)
            widths.append(float(largest.w))

    if len(widths) < 3:
        print(
            f"[WARN] Only {len(widths)} valid frames collected; sample skipped.",
            file=sys.stderr,
        )
        return None

    median_width = statistics.median(widths)
    print(
        f"[CALIB] distance={distance_cm:.1f} cm, "
        f"frames={len(widths)}, median_width={median_width:.1f} px"
    )
    return distance_cm, median_width


def main(argv: Optional[list[str]] = None) -> int:
    """Run the M3 loop: detect, compute metrics, track anomalies, draw HUD.

    Keyboard shortcuts: ``q``/``Esc`` quit, ``c`` collect a calibration sample,
    ``s`` fit and save calibration.

    Args:
        argv: Optional argument list (defaults to ``sys.argv[1:]``).

    Returns:
        Exit code (0 on success, 1 on input open failure).
    """
    args = parse_args(argv)
    source = InputSource.FILE if args.source == "file" else InputSource.CAMERA

    try:
        if source is InputSource.FILE:
            capture = VideoCapture(InputSource.FILE, path=Path(args.path))
        else:
            capture = VideoCapture(InputSource.CAMERA, camera_index=args.camera_index)
    except (ValueError, FileNotFoundError, RuntimeError) as exc:
        print(f"[ERROR] Failed to open input: {exc}", file=sys.stderr)
        return 1

    detector = FaceDetector()
    hud = HUDOverlay()

    calibrator = DistanceCalibrator()
    if CALIBRATION_FILE.exists():
        try:
            calibrator.load(CALIBRATION_FILE)
            print(f"[INFO] Loaded calibration: k={calibrator.k_value:.1f}")
        except CalibrationError as exc:
            print(f"[WARN] Could not load calibration: {exc}", file=sys.stderr)

    calculator = MetricsCalculator(calibrator)
    tracker = AnomalyTracker()

    frame_count = 0
    start_time = time.monotonic()
    fps = 0.0

    try:
        while capture.is_opened:
            success, frame = capture.read()
            if not success or frame is None:
                break

            faces = detector.detect(frame)
            metrics = calculator.compute(frame, faces)

            distance_anomaly = metrics.distance_category in (
                DistanceCategory.TOO_CLOSE,
                DistanceCategory.TOO_FAR,
            )
            posture_anomaly = (
                metrics.face_detected
                and metrics.posture_score < POSTURE_ANOMALY_SCORE
            )

            if tracker.update(
                "distance",
                distance_anomaly,
                DISTANCE_ANOMALY_THRESHOLD_SEC,
                COOLDOWN_SEC,
            ):
                print("[ANOMALY] distance sustained out of range")
            if tracker.update(
                "posture",
                posture_anomaly,
                POSTURE_ANOMALY_THRESHOLD_SEC,
                COOLDOWN_SEC,
            ):
                print("[ANOMALY] posture sustained out of range")

            active = tracker.active_metrics()

            frame_count += 1
            elapsed = time.monotonic() - start_time
            if elapsed > 0:
                fps = frame_count / elapsed

            display = hud.draw(frame, metrics, fps, len(faces), active)
            cv2.imshow(WINDOW_NAME, display)

            key = cv2.waitKey(1) & 0xFF
            if key in (ord("q"), 27):  # q or Esc
                break
            elif key == ord("c"):
                sample = collect_sample(capture, detector)
                if sample is not None:
                    distance, width = sample
                    try:
                        calibrator.add_sample(distance, width)
                        print(f"[INFO] samples collected: {calibrator.sample_count}")
                    except ValueError as exc:
                        print(f"[ERROR] {exc}", file=sys.stderr)
            elif key == ord("s"):
                try:
                    calibrator.fit()
                    calibrator.save(CALIBRATION_FILE)
                    print(
                        f"[INFO] Calibration saved to {CALIBRATION_FILE} "
                        f"(k={calibrator.k_value:.1f})"
                    )
                except CalibrationError as exc:
                    print(f"[ERROR] {exc}", file=sys.stderr)
    except KeyboardInterrupt:
        pass
    finally:
        capture.release()
        cv2.destroyAllWindows()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
