"""Session CSV logging (M4)."""

import csv
from datetime import datetime
from pathlib import Path
from typing import Optional

from config import AppConfig
from metrics import FrameMetrics
from reminder import ReminderEvent

CSV_HEADER = [
    "timestamp",
    "face_detected",
    "face_x",
    "face_y",
    "face_w",
    "face_h",
    "distance_cm",
    "distance_category",
    "posture_score",
    "brightness_level",
    "reminder_triggered",
]


class SessionLogger:
    """Write session metrics to CSV at the configured interval."""

    def __init__(self, config: AppConfig, log_dir: Path) -> None:
        """Open a new session CSV file.

        Args:
            config: Application configuration.
            log_dir: Directory for CSV log files.
        """
        self._interval = float(config.get("logging.interval_sec"))
        directory = Path(log_dir)
        directory.mkdir(parents=True, exist_ok=True)

        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self._path = directory / f"session_{stamp}.csv"
        self._file = open(self._path, "w", newline="", encoding="utf-8")
        self._writer = csv.writer(self._file)
        self._writer.writerow(CSV_HEADER)
        self._last_write: Optional[float] = None
        self._pending_reminders: list[ReminderEvent] = []
        self._closed = False

    def log(self, metrics: FrameMetrics, reminders: list[ReminderEvent]) -> None:
        """Log metrics if the logging interval has elapsed.

        Args:
            metrics: Current frame metrics.
            reminders: Reminder events triggered for this frame.
        """
        if self._closed:
            return

        # Buffer events from non-write frames so they are not lost.
        self._pending_reminders.extend(reminders)

        if (
            self._last_write is not None
            and metrics.timestamp - self._last_write < self._interval
        ):
            return

        self._last_write = metrics.timestamp
        face = metrics.face_box
        reminder_text = ",".join(
            event.reminder_type.value for event in self._pending_reminders
        )
        self._pending_reminders.clear()
        row = [
            f"{metrics.timestamp:.3f}",
            int(metrics.face_detected),
            face.x if face else 0,
            face.y if face else 0,
            face.w if face else 0,
            face.h if face else 0,
            f"{metrics.distance_cm:.2f}" if metrics.distance_cm is not None else "nan",
            metrics.distance_category.value,
            f"{metrics.posture_score:.3f}",
            metrics.brightness_level,
            reminder_text,
        ]
        self._writer.writerow(row)
        self._file.flush()

    def close(self) -> Path:
        """Flush and close the CSV file.

        Returns:
            Path to the completed log file.
        """
        if not self._closed:
            self._file.flush()
            self._file.close()
            self._closed = True
        return self._path
