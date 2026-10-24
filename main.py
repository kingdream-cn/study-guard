"""StudyGuard application entry point (M6: testing & stability)."""

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
from reminder import ReminderEvent, ReminderManager, select_banner
from report import ReportGenerator

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
    parser = argparse.ArgumentParser(description="StudyGuard")
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
    parser.add_argument(
        "--config",
        type=str,
        default=str(CONFIG_FILE),
        help="path to JSON config file (default: configs/default.json)",
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="run without a display window (no imshow/waitKey)",
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
        config = AppConfig(Path(args.config))
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

    detector = FaceDetector(
        scale_factor=config.get("detection.scale_factor"),
        min_neighbors=config.get("detection.min_neighbors"),
        min_face_size=config.get("detection.min_face_size"),
        backend=config.get("detection.backend"),
        model_path=config.get("detection.model_path"),
        score_threshold=config.get("detection.score_threshold"),
        nms_threshold=config.get("detection.nms_threshold"),
        top_k=config.get("detection.top_k"),
    )
    hud = HUDOverlay(language=config.get("hud.language"))

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
    auto_baseline = bool(config.get("posture.auto_baseline"))

    log_dir = PROJECT_ROOT / str(config.get("logging.log_dir", "logs"))
    try:
        logger: Optional[SessionLogger] = SessionLogger(config, log_dir)
    except OSError as exc:
        print(f"[ERROR] Cannot write log directory {log_dir}: {exc}", file=sys.stderr)
        logger = None

    frame_count = 0
    start_time = time.monotonic()
    fps = 0.0
    # Most recent triggered event batch; select_banner applies the 3 s hold.
    banner_events: list[ReminderEvent] = []

    try:
        while capture.is_opened:
            success, frame = capture.read()
            if not success or frame is None:
                break

            faces = detector.detect(frame)
            metrics = calculator.compute(frame, faces)
            events = reminders.update(metrics)
            if logger is not None:
                logger.log(metrics, events)

            if events:
                banner_events = events
            now = time.monotonic()
            banner = select_banner(
                now, banner_events, reminders.active_warnings(), BANNER_HOLD_SEC
            )

            frame_count += 1
            elapsed = now - start_time
            if elapsed > 0:
                fps = frame_count / elapsed

            baseline_hint = None
            if auto_baseline:
                if calculator.is_collecting:
                    baseline_hint = (
                        f"Baseline: {calculator.baseline_progress}/"
                        f"{calculator.baseline_frames}"
                    )
                elif calculator.baseline_ready:
                    baseline_hint = "baseline ready"
                else:
                    baseline_hint = "Sit upright, press b to set posture baseline"

            display = hud.draw(
                frame, metrics, fps, len(faces), banner, baseline_hint
            )
            if args.headless:
                key = -1
            else:
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
            elif key == ord("b"):
                if auto_baseline:
                    calculator.begin_baseline()
                    print("[INFO] Posture baseline: sit upright for 30 frames")
                else:
                    print(
                        "[WARN] posture.auto_baseline is disabled; "
                        "using configured ideal ratios",
                        file=sys.stderr,
                    )
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
        if not args.headless:
            cv2.destroyAllWindows()

        if logger is not None:
            log_path = logger.close()
            print(f"[INFO] Session log: {log_path}")

            report_dir = PROJECT_ROOT / str(config.get("report.output_dir", "reports"))
            try:
                report_path = ReportGenerator(config).generate(log_path, report_dir)
                print(f"[INFO] Session report: {report_path}")
            except Exception as exc:  # report must not block a clean exit
                print(f"[WARN] Report generation failed: {exc}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
