"""StudyGuard application entry point (M4: reminders & logging)."""

import argparse
import statistics
import sys
import time
from pathlib import Path
from typing import Optional

import cv2

from calibrator import CalibrationError, DistanceCalibrator
from capture import InputSource, VideoCapture
from config import AppConfig, ConfigError
from detector import FaceDetector
from hud import HUDOverlay
from logger import SessionLogger
from metrics import MetricsCalculator
from reminder import ReminderManager

WINDOW_NAME = "StudyGuard"
PROJECT_ROOT = Path(__file__).resolve().parent
CONFIG_FILE = PROJECT_ROOT / "configs" / "default.json"
CALIBRATION_FILE = PROJECT_ROOT / "configs" / "calibration.json"

# Number of frames to collect (and median-filter) for one calibration sample.
CALIBRATION_FRAMES = 30

# How long a triggered reminder message stays on the HUD.
BANNER_HOLD_SEC = 3.0


def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    """Parse command-line arguments.

    Args:
        argv: Optional argument list (defaults to ``sys.argv[1:]``).

    Returns:
        Parsed arguments namespace.
    """
    parser = argparse.ArgumentParser(
        description="StudyGuard - reminders & logging (M4)"
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
    """Run the M4 loop: metrics, reminders, CSV logging, HUD.

    Keyboard shortcuts: ``q``/``Esc`` quit, ``Space`` pause/resume,
    ``c`` collect a calibration sample, ``s`` fit and save calibration.

    Args:
        argv: Optional argument list (defaults to ``sys.argv[1:]``).

    Returns:
        Exit code (0 on success, 1 on configuration or input failure).
    """
    args = parse_args(argv)

    try:
        config = AppConfig(CONFIG_FILE)
    except ConfigError as exc:
        print(f"[ERROR] Invalid configuration: {exc}", file=sys.stderr)
        return 1

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

    calculator = MetricsCalculator(
        calibrator,
        too_close_cm=config.get("distance.too_close_cm"),
        too_far_cm=config.get("distance.too_far_cm"),
        ideal_y_ratio=config.get("posture.ideal_y_ratio"),
        ideal_w_ratio=config.get("posture.ideal_w_ratio"),
        tolerance=config.get("posture.tolerance"),
        brightness_thresholds=tuple(config.get("brightness.thresholds")),
        auto_baseline=config.get("posture.auto_baseline"),
        baseline_frames=config.get("posture.baseline_frames"),
    )
    reminders = ReminderManager(config)

    log_dir = PROJECT_ROOT / str(config.get("logging.log_dir", "logs"))
    logger = SessionLogger(config, log_dir)

    frame_count = 0
    start_time = time.monotonic()
    fps = 0.0
    banner = ""
    banner_until = 0.0

    try:
        while capture.is_opened:
            success, frame = capture.read()
            if not success or frame is None:
                break

            faces = detector.detect(frame)
            metrics = calculator.compute(frame, faces)
            events = reminders.update(metrics)
            logger.log(metrics, events)

            now = time.monotonic()
            if events:
                banner = events[-1].message
                banner_until = now + BANNER_HOLD_SEC
            active = reminders.active_warnings()
            if active:
                banner = "WARNING: " + ", ".join(active)
            elif now >= banner_until:
                banner = ""

            frame_count += 1
            elapsed = now - start_time
            if elapsed > 0:
                fps = frame_count / elapsed

            display = hud.draw(frame, metrics, fps, len(faces), banner)
            cv2.imshow(WINDOW_NAME, display)

            key = cv2.waitKey(1) & 0xFF
            if key in (ord("q"), 27):  # q or Esc
                break
            elif key == ord(" "):
                if reminders.is_paused:
                    reminders.resume()
                    print("[INFO] Resumed")
                else:
                    reminders.pause()
                    print("[INFO] Paused")
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
        log_path = logger.close()
        print(f"[INFO] Session log: {log_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
