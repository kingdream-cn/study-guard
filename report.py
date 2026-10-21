"""Session summary report generation (M5)."""

import csv
import json
import logging
import statistics
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import matplotlib

matplotlib.use("Agg")  # headless-safe before importing pyplot
import matplotlib.pyplot as plt

from calibrator import CalibrationError, DistanceCalibrator
from config import AppConfig
from reminder import ReminderType

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent
DEFAULT_CALIBRATION_FILE = PROJECT_ROOT / "configs" / "calibration.json"


def _optional_float(value: str) -> Optional[float]:
    """Parse a float, treating blank/NaN/None as None."""
    text = value.strip()
    if text == "" or text.lower() in ("nan", "none", "null"):
        return None
    return float(text)


class ReportGenerator:
    """Generate a session summary report from a CSV log."""

    def __init__(
        self, config: AppConfig, calibration_path: Optional[Path] = None
    ) -> None:
        """Initialize the generator.

        Args:
            config: Application configuration.
            calibration_path: Path to the calibration file whose k value is
                recorded in the report. Defaults to ``configs/calibration.json``.
        """
        self._config = config
        self._calibration_path = calibration_path or DEFAULT_CALIBRATION_FILE
        self._interval = float(config.get("logging.interval_sec", 1.0))

    def generate(self, log_path: Path, output_dir: Path) -> Path:
        """Generate a session summary report.

        Writes a JSON summary (``session_summary_YYYYmmdd_HHMMSS.json``) and,
        when enabled, a PNG chart next to it. If there is no valid face data,
        the JSON records ``insufficient_data: true`` and null statistics.

        Args:
            log_path: Path to the session CSV log file.
            output_dir: Directory for report output.

        Returns:
            Path to the generated JSON report file.
        """
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        directory = Path(output_dir)
        directory.mkdir(parents=True, exist_ok=True)
        json_path = directory / f"session_summary_{stamp}.json"

        rows = self._load_rows(Path(log_path))
        calibration_k = self._load_calibration_k()

        if not rows:
            summary: dict[str, Any] = {
                "generated_at": datetime.now().isoformat(timespec="seconds"),
                "insufficient_data": True,
                "session": None,
                "distance": None,
                "posture": None,
                "brightness_distribution": None,
                "reminders": None,
            }
        else:
            summary = self._summarize(rows, calibration_k)

        json_path.write_text(
            json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8"
        )

        if not summary.get("insufficient_data") and self._config.get(
            "report.generate_charts"
        ):
            png_path = directory / f"session_summary_{stamp}.png"
            try:
                self._render_charts(rows, png_path)
            except Exception as exc:  # charts must not break report generation
                logger.warning("Chart rendering failed: %s", exc)

        return json_path

    # -- CSV parsing ----------------------------------------------------------

    def _load_rows(self, log_path: Path) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        try:
            fh = Path(log_path).open(newline="", encoding="utf-8")
        except OSError as exc:
            logger.warning("Cannot open log %s: %s", log_path, exc)
            return rows

        with fh:
            reader = csv.reader(fh)
            header = next(reader, None)
            if header is None:
                logger.warning("Empty log file: %s", log_path)
                return rows
            for line_no, row in enumerate(reader, start=2):
                parsed = self._parse_row(row, header, line_no)
                if parsed is not None:
                    rows.append(parsed)
        return rows

    def _parse_row(
        self, row: list[str], header: list[str], line_no: int
    ) -> Optional[dict[str, Any]]:
        if len(row) != len(header):
            logger.warning(
                "Log line %d has %d columns, expected %d; skipped",
                line_no,
                len(row),
                len(header),
            )
            return None

        record = dict(zip(header, row))
        try:
            return {
                "timestamp": float(record["timestamp"]),
                "face_detected": int(record["face_detected"]) == 1,
                "face_box": (
                    int(record["face_x"]),
                    int(record["face_y"]),
                    int(record["face_w"]),
                    int(record["face_h"]),
                ),
                "distance_cm": _optional_float(record["distance_cm"]),
                "distance_category": record["distance_category"],
                "posture_score": float(record["posture_score"]),
                "brightness_level": int(record["brightness_level"]),
                "reminders": [
                    item.strip()
                    for item in record["reminder_triggered"].split(",")
                    if item.strip()
                ],
            }
        except (KeyError, ValueError, TypeError) as exc:
            logger.warning("Log line %d has a bad value (%s); skipped", line_no, exc)
            return None

    # -- summarization ---------------------------------------------------------

    def _load_calibration_k(self) -> Optional[float]:
        if not self._calibration_path.exists():
            return None
        try:
            calibrator = DistanceCalibrator()
            calibrator.load(self._calibration_path)
            return calibrator.k_value
        except CalibrationError as exc:
            logger.warning(
                "Could not load calibration %s: %s", self._calibration_path, exc
            )
            return None

    def _summarize(self, rows: list[dict[str, Any]], calibration_k: Optional[float]) -> dict[str, Any]:
        face_rows = [r for r in rows if r["face_detected"]]
        if not face_rows:
            return {
                "generated_at": datetime.now().isoformat(timespec="seconds"),
                "insufficient_data": True,
                "session": None,
                "distance": None,
                "posture": None,
                "brightness_distribution": None,
                "reminders": None,
            }

        total_rows = len(rows)
        timestamps = [r["timestamp"] for r in rows]
        duration = max(timestamps) - min(timestamps)

        distances = [
            r["distance_cm"] for r in face_rows if r["distance_cm"] is not None
        ]
        distance_stats: Optional[dict[str, Any]]
        if distances:
            distance_stats = {
                "mean_cm": round(statistics.mean(distances), 2),
                "min_cm": round(min(distances), 2),
                "max_cm": round(max(distances), 2),
                "median_cm": round(statistics.median(distances), 2),
            }
        else:
            distance_stats = None

        category_counts: dict[str, int] = {}
        for r in face_rows:
            category = r["distance_category"]
            category_counts[category] = category_counts.get(category, 0) + 1
        category_ratio = {
            name: round(category_counts.get(name, 0) / len(face_rows), 4)
            for name in ("too_close", "normal", "too_far", "unknown")
        }

        posture_values = [r["posture_score"] for r in face_rows]
        posture_stats = {
            "mean": round(statistics.mean(posture_values), 3),
            "min": round(min(posture_values), 3),
            "max": round(max(posture_values), 3),
        }

        brightness_distribution: dict[str, int] = {str(i): 0 for i in range(1, 6)}
        for r in rows:
            level = r["brightness_level"]
            if 1 <= level <= 5:
                brightness_distribution[str(level)] += 1

        reminder_counts = {t.value: 0 for t in ReminderType}
        for r in rows:
            for name in r["reminders"]:
                if name in reminder_counts:
                    reminder_counts[name] += 1

        return {
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "insufficient_data": False,
            "session": {
                "duration_sec": round(duration, 2),
                "effective_study_time_sec": round(len(face_rows) * self._interval, 2),
                "face_detection_rate": round(len(face_rows) / total_rows, 4),
                "calibration_k": calibration_k,
                "row_count": total_rows,
                "face_row_count": len(face_rows),
            },
            "distance": {
                "stats": distance_stats,
                "category_ratio": category_ratio,
            },
            "posture": posture_stats,
            "brightness_distribution": brightness_distribution,
            "reminders": reminder_counts,
        }

    # -- charts ----------------------------------------------------------------

    def _render_charts(self, rows: list[dict[str, Any]], png_path: Path) -> None:
        face_rows = [r for r in rows if r["face_detected"]]
        distances = [r["distance_cm"] for r in face_rows if r["distance_cm"] is not None]
        posture = [r["posture_score"] for r in face_rows]
        levels = [r["brightness_level"] for r in rows]

        fig, axes = plt.subplots(1, 3, figsize=(15, 4))
        fig.suptitle("StudyGuard session summary")

        if distances:
            axes[0].hist(distances, bins=10)
            axes[0].set_title("Distance (cm)")
        else:
            axes[0].text(0.5, 0.5, "no distance data", ha="center", va="center")
            axes[0].set_axis_off()

        axes[1].bar(
            [str(i) for i in range(1, 6)],
            [levels.count(i) for i in range(1, 6)],
        )
        axes[1].set_title("Brightness level")

        if posture:
            axes[2].plot(posture)
            axes[2].set_title("Posture score over time")
        else:
            axes[2].text(0.5, 0.5, "no posture data", ha="center", va="center")
            axes[2].set_axis_off()

        fig.tight_layout()
        fig.savefig(png_path)
        plt.close(fig)
