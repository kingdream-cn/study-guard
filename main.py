"""StudyGuard application entry point (M1: visual foundation)."""

import argparse
import sys
import time
from pathlib import Path

import cv2

from capture import InputSource, VideoCapture
from detector import FaceDetector
from hud import HUDOverlay

WINDOW_NAME = "StudyGuard"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments.

    Args:
        argv: Optional argument list (defaults to ``sys.argv[1:]``).

    Returns:
        Parsed arguments namespace.
    """
    parser = argparse.ArgumentParser(
        description="StudyGuard - visual foundation (M1)"
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


def main(argv: list[str] | None = None) -> int:
    """Run the M1 processing loop: open input, detect faces, draw HUD, quit.

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

    frame_count = 0
    start_time = time.monotonic()
    fps = 0.0

    try:
        while capture.is_opened:
            success, frame = capture.read()
            if not success or frame is None:
                break

            faces = detector.detect(frame)

            frame_count += 1
            elapsed = time.monotonic() - start_time
            if elapsed > 0:
                fps = frame_count / elapsed

            display = hud.draw(frame, faces, fps)
            cv2.imshow(WINDOW_NAME, display)

            key = cv2.waitKey(1) & 0xFF
            if key in (ord("q"), 27):  # q or Esc
                break
    except KeyboardInterrupt:
        pass
    finally:
        capture.release()
        cv2.destroyAllWindows()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
