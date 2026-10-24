# StudyGuard Interface Specification

> 接口规范文档 — 模块间接口、数据格式、显示规范

## 1. Module Interfaces

### 1.1 `config.py`

```python
from pathlib import Path
from typing import Any

class ConfigError(Exception):
    """Raised when configuration is invalid or missing required keys."""

class AppConfig:
    """Application configuration container."""

    def __init__(self, config_path: Path) -> None:
        """Load and validate configuration from JSON file.

        Args:
            config_path: Path to JSON configuration file.

        Raises:
            ConfigError: If file is missing, unreadable, or contains invalid values.
        """

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value by dot-separated key path.

        Args:
            key: Dot-separated key, e.g. "reminder.eye_care_interval_min".
            default: Value to return if key is not found.

        Returns:
            Configuration value or default.
        """
```

### 1.2 `capture.py`

```python
from enum import Enum
from pathlib import Path
from typing import Optional
import numpy as np

class InputSource(Enum):
    FILE = "file"
    CAMERA = "camera"

class VideoCapture:
    """Unified video input abstraction for file and camera sources."""

    def __init__(self, source: InputSource, path: Optional[Path] = None,
                 camera_index: int = 0) -> None:
        """Initialize video capture.

        Args:
            source: InputSource.FILE or InputSource.CAMERA.
            path: Path to video file (required if source is FILE).
            camera_index: Camera device index (default 0 for /dev/video0).

        Raises:
            ValueError: If source is FILE but path is None.
            RuntimeError: If device/file cannot be opened.
        """

    def read(self) -> tuple[bool, Optional[np.ndarray]]:
        """Read next frame.

        Returns:
            Tuple of (success, frame). Frame is None if read failed.
        """

    @property
    def fps(self) -> float:
        """Reported FPS of the video source. Returns 0.0 if unavailable."""

    @property
    def frame_width(self) -> int:
        """Frame width in pixels."""

    @property
    def frame_height(self) -> int:
        """Frame height in pixels."""

    @property
    def is_opened(self) -> bool:
        """Whether the capture device is currently open."""

    def release(self) -> None:
        """Release the capture device. Safe to call multiple times."""
```

### 1.3 `detector.py`

```python
from dataclasses import dataclass
import numpy as np

@dataclass
class FaceBox:
    """A detected face bounding box."""
    x: int        # Top-left x
    y: int        # Top-left y
    w: int        # Width
    h: int        # Height

    @property
    def center(self) -> tuple[int, int]:
        """Center point of the bounding box."""

    @property
    def area(self) -> int:
        """Area of the bounding box in pixels."""

def yunet_faces_to_boxes(
    faces: Optional[np.ndarray],
    input_size: tuple[int, int],
    frame_size: tuple[int, int],
    min_size: int = 0,
) -> list[FaceBox]:
    """Convert YuNet (N,15) output to FaceBoxes in original frame coordinates.

    Args:
        faces: Raw YuNet output, or None when no face was detected.
        input_size: (width, height) of the image passed to detect().
        frame_size: (width, height) of the original frame.
        min_size: Minimum box width and height in frame pixels (default 0).
            Same semantics as Haar's minSize: dropped when
            w < min_size or h < min_size.

    Returns:
        Boxes rounded with int(round(value)), clamped to the frame, then
        size-filtered (clamp first, then filter); zero-size boxes are dropped.
        Landmarks/score are ignored.
    """

class FaceDetector:
    """Face detector with selectable Haar (default) or YuNet backend."""

    def __init__(
        self,
        cascade_path: Optional[str] = None,
        scale_factor: float = 1.1,
        min_neighbors: int = 5,
        min_face_size: int = 30,
        backend: str = "haar",
        model_path: Optional[str] = None,
        score_threshold: float = 0.9,
        nms_threshold: float = 0.3,
        top_k: int = 5000,
    ) -> None:
        """Initialize the requested detector backend.

        Args:
            cascade_path: Optional path to custom cascade XML.
            scale_factor: Haar pyramid scale factor (default 1.1).
            min_neighbors: Haar minimum neighbors (default 5).
            min_face_size: Minimum face size in pixels (default 30), applied to
                both backends (Haar minSize / YuNet min_size filter).
            backend: "haar" (default) or "yunet".
            model_path: Local YuNet ONNX path; "~" is expanded. Required for
                backend="yunet".
            score_threshold: YuNet score threshold (default 0.9).
            nms_threshold: YuNet NMS threshold (default 0.3).
            top_k: YuNet boxes kept before NMS (default 5000).

        Raises:
            ValueError: If backend is not "haar" or "yunet".
            RuntimeError: If the cascade or YuNet model cannot be loaded.
        """

    def detect(self, frame: np.ndarray) -> list[FaceBox]:
        """Detect faces in a BGR frame using the configured backend.

        Args:
            frame: BGR image as numpy array.

        Returns:
            List of FaceBox detections in frame coordinates. Empty list if no
            faces are found. For YuNet, setInputSize() is applied when the
            frame size changes; the production path uses the native frame size,
            so the coordinate scale is 1:1.
        """
```

Backend notes: `backend` defaults to `"haar"` and the Haar path is unchanged.
`"yunet"` requires `detection.model_path`; a missing model aborts startup with
`ConfigError` (config layer) or `RuntimeError` (direct construction), never
falls back to Haar. `yunet_faces_to_boxes()` is pure and supports both 1:1 and
non-1:1 scales; production uses the native frame size, so the scale is 1:1.
`min_face_size` is enforced on both backends: YuNet boxes are clamped to the
frame first and then filtered by `w >= min_size and h >= min_size`.
The ONNX model is not committed to the repository.

### 1.4 `calibrator.py`

```python
from pathlib import Path
import numpy as np

class CalibrationError(Exception):
    """Raised when calibration data is invalid or insufficient."""

class DistanceCalibrator:
    """Three-point distance calibration using face box width.

    Model: d = k / w
    Where d = distance (cm), w = face box width (pixels), k = fitted constant.
    """

    def __init__(self) -> None:
        """Initialize with no calibration data."""

    def add_sample(self, known_distance_cm: float, face_width_px: float) -> None:
        """Add a calibration sample.

        Args:
            known_distance_cm: Known distance in centimeters.
            face_width_px: Measured face bounding box width in pixels.

        Raises:
            ValueError: If distance or width is non-positive.
        """

    def fit(self) -> float:
        """Fit parameter k using least squares: k = sum(w_i * d_i) / sum(w_i^2).

        Returns:
            Fitted k value.

        Raises:
            CalibrationError: If fewer than 3 samples have been added.
        """

    @property
    def k_value(self) -> Optional[float]:
        """Current fitted k value, or None if not yet fitted."""

    def estimate_distance(self, face_width_px: float) -> Optional[float]:
        """Estimate distance from face width using fitted k.

        Args:
            face_width_px: Face bounding box width in pixels.

        Returns:
            Estimated distance in cm, or None if not calibrated.
        """

    def save(self, path: Path) -> None:
        """Save calibration data and k value to JSON file.

        Args:
            path: Output file path.
        """

    def load(self, path: Path) -> None:
        """Load calibration data from JSON file.

        Args:
            path: Input file path.

        Raises:
            CalibrationError: If file is missing or data is invalid.
        """
```

### 1.5 `metrics.py`

```python
from dataclasses import dataclass
from enum import Enum
from typing import Optional

class DistanceCategory(Enum):
    TOO_CLOSE = "too_close"
    NORMAL = "normal"
    TOO_FAR = "too_far"
    UNKNOWN = "unknown"

@dataclass
class FrameMetrics:
    """Computed metrics for a single frame."""
    timestamp: float           # monotonic time
    distance_cm: Optional[float]
    distance_category: DistanceCategory
    posture_score: float       # 0.0 (worst) to 1.0 (best)
    brightness_level: int      # 1 (darkest) to 5 (brightest)
    face_detected: bool
    face_box: Optional[FaceBox]

class MetricsCalculator:
    """Compute frame-level metrics from detection results."""

    def __init__(self, calibrator: DistanceCalibrator, config: AppConfig) -> None:
        """
        Args:
            calibrator: Fitted distance calibrator.
            config: Application configuration.
        """

    def compute(self, frame: np.ndarray, faces: list[FaceBox]) -> FrameMetrics:
        """Compute all metrics for a single frame.

        Args:
            frame: BGR image.
            faces: List of detected face boxes.

        Returns:
            FrameMetrics for this frame. If no face detected, distance and
            posture fields use fallback values.
        """
```

### 1.6 `reminder.py`

```python
from enum import Enum
from typing import Callable, Optional

class ReminderType(Enum):
    EYE_CARE_20_20 = "eye_care_20_20"
    SEDENTARY = "sedentary"
    POSTURE_WARNING = "posture_warning"
    DISTANCE_WARNING = "distance_warning"
    BRIGHTNESS_WARNING = "brightness_warning"
    FACE_LOST = "face_lost"

@dataclass
class ReminderEvent:
    """A triggered reminder."""
    reminder_type: ReminderType
    message: str
    timestamp: float

class ReminderManager:
    """Manage all reminder timers and anomaly tracking."""

    def __init__(self, config: AppConfig, clock: Optional[Callable[[], float]] = None) -> None:
        """
        Args:
            config: Application configuration.
            clock: Optional injectable clock function (defaults to time.monotonic).
                   MUST be injectable for testing.
        """

    def update(self, metrics: FrameMetrics) -> list[ReminderEvent]:
        """Process new metrics and return any triggered reminders.

        Args:
            metrics: Current frame metrics.

        Returns:
            List of ReminderEvents triggered since last update.
            Empty list if no reminders.
        """

    def pause(self) -> None:
        """Pause all timers. Call when user pauses or face is lost."""

    def resume(self) -> None:
        """Resume all timers. Call when user resumes or face is regained."""

    def reset(self) -> None:
        """Reset all timers and counters. Call at session start."""

    @property
    def effective_study_time(self) -> float:
        """Total seconds of valid face-present study time."""

    @property
    def session_elapsed_time(self) -> float:
        """Total seconds since session start (including face-lost time)."""

    def active_warnings(self) -> list[str]:
        """Labels of warnings currently active (for the HUD banner).

        Returns:
            Zero or more of "face_lost", "distance_too_close",
            "distance_too_far", "posture".
        """

def select_banner(
    now: float,
    events: list[ReminderEvent],
    active_labels: list[str],
    hold_sec: float,
) -> str:
    """Select the HUD banner text for the current frame.

    ``events`` is the most recent triggered batch; the caller (``main.py``)
    keeps it across frames until a newer batch arrives.

    Priority:
        1. ``events[-1].message`` while that event is within ``hold_sec``
           (inclusive).
        2. ``"WARNING: " + ", ".join(active_labels)`` when warnings are active.
        3. An empty string when neither applies.
    """
```

Distance anomalies are tracked per direction (`distance_close` /
`distance_far`): a too-far warning never silences a subsequent too-close
warning, while `reminder.cooldown_sec` still applies to each direction
separately. The distance messages are `"Too close — move back"` and
`"Too far — move closer"`. `ReminderType` values and CSV columns are
unchanged.

### 1.7 `logger.py`

```python
from pathlib import Path

class SessionLogger:
    """Write session metrics to CSV at configured interval."""

    def __init__(self, config: AppConfig, log_dir: Path) -> None:
        """
        Args:
            config: Application configuration.
            log_dir: Directory for CSV log files.
        """

    def log(self, metrics: FrameMetrics, reminders: list[ReminderEvent]) -> None:
        """Log metrics if logging interval has elapsed since last write.

        Does NOT write every frame — respects config interval.
        """

    def close(self) -> Path:
        """Flush and close the CSV file.

        Returns:
            Path to the completed log file.
        """
```

### 1.8 `report.py`

```python
from pathlib import Path

class ReportGenerator:
    """Generate session summary report from logged data."""

    def __init__(self, config: AppConfig) -> None:
        """
        Args:
            config: Application configuration.
        """

    def generate(self, log_path: Path, output_dir: Path) -> Path:
        """Generate a session report.

        Args:
            log_path: Path to session CSV log file.
            output_dir: Directory for report output.

        Returns:
            Path to generated report file.

        Note:
            If log data is insufficient (e.g., no valid measurements),
            the report will contain "Insufficient data" instead of
            misleading statistics.
        """
```

### 1.9 `hud.py`

```python
import numpy as np

class HUDOverlay:
    """Draw heads-up display overlay on video frames."""

    def __init__(self, language: str = "en") -> None:
        """
        Args:
            language: Display language, either "en" or "zh" (default "en").
                "zh" renders via Pillow with a system CJK font; it falls back
                to the English cv2 path when no CJK font is available.
        """

    def draw(self, frame: np.ndarray, metrics: FrameMetrics, fps: float,
             face_count: int = 0, warning: Optional[str] = None,
             baseline_hint: Optional[str] = None) -> np.ndarray:
        """Draw overlay on a copy of the frame.

        Args:
            frame: BGR image to draw on.
            metrics: Current frame metrics.
            fps: Current processing FPS.
            face_count: Number of faces detected in this frame.
            warning: Active warning text, or None.
            baseline_hint: Posture-baseline prompt/status, or None.

        Returns:
            New image with overlay drawn. Original frame is not modified.
        """
```

Banner localization (rendering layer only, when `language == "zh"`): a warning
banner is translated by (a) exact whole-message match for the fixed reminder
strings (including `"Too close — move back"` / `"Too far — move closer"`),
then (b) `"WARNING: "` prefix plus per-label lookup joined by `、`
(e.g. `"WARNING: distance_too_close, posture"` → `"警告：距离过近、坐姿不良"`);
any text matching neither rule is shown verbatim (no exception, no guessing).
The legacy `"distance"` label and `"Adjust viewing distance"` message mappings
are retained for older logs/banners. The English `cv2` path and `reminder.py`
strings are unchanged.

---

## 2. Configuration Schema

File: `configs/default.json`

```json
{
  "input": {
    "source": "file | camera",
    "video_path": "string (relative or absolute path, required if source=file)",
    "camera_index": "int (default: 0)"
  },
  "detection": {
    "scale_factor": "float (default: 1.1)",
    "min_neighbors": "int (default: 5)",
    "min_face_size": "int (default: 30) — minimum face size in pixels, applied to both backends (Haar minSize / YuNet min_size filter)",
    "backend": "\"haar\" | \"yunet\" (default: \"haar\")",
    "score_threshold": "float (0.0, 1.0] (default: 0.9, YuNet demo value)",
    "nms_threshold": "float (0.0, 1.0] (default: 0.3, YuNet demo value)",
    "top_k": "int >= 1 (default: 5000, YuNet demo value)",
    "model_path": "string (default: ~/study_models/face_detection_yunet_2023mar.onnx; must exist when backend=yunet)"
  },
  "distance": {
    "too_close_cm": "float (default: 30.0)",
    "too_far_cm": "float (default: 80.0)",
    "smoothing_window": "int (default: 5)"
  },
  "posture": {
    "ideal_y_ratio": "float (default: 0.4) — ideal face center Y / frame height",
    "ideal_w_ratio": "float (default: 0.25) — ideal face width / frame width",
    "tolerance": "float (default: 0.15)"
  },
  "brightness": {
    "levels": "int (default: 5)",
    "thresholds": "[float] — boundaries between levels"
  },
  "reminder": {
    "eye_care_interval_min": "float (default: 20.0)",
    "eye_care_look_far_sec": "float (default: 20.0)",
    "sedentary_interval_min": "float (default: 45.0)",
    "posture_anomaly_threshold_sec": "float (default: 10.0)",
    "distance_anomaly_threshold_sec": "float (default: 5.0)",
    "cooldown_sec": "float (default: 60.0)"
  },
  "logging": {
    "interval_sec": "float (default: 1.0)",
    "log_dir": "string (default: logs)"
  },
  "report": {
    "output_dir": "string (default: reports)",
    "generate_charts": "bool (default: true)"
  },
  "hud": {
    "language": "\"zh\" | \"en\" (default: zh)"
  }
}
```

## 3. CSV Log Format

File: `logs/session_YYYYMMDD_HHMMSS.csv`

| Column | Type | Unit | Description |
|--------|------|------|-------------|
| `timestamp` | float | seconds | Monotonic clock timestamp |
| `face_detected` | bool | — | Whether a face was detected |
| `face_x` | int | pixels | Face box top-left x (0 if not detected) |
| `face_y` | int | pixels | Face box top-left y |
| `face_w` | int | pixels | Face box width |
| `face_h` | int | pixels | Face box height |
| `distance_cm` | float | cm | Estimated distance (NaN if not detected) |
| `distance_category` | str | — | too_close / normal / too_far / unknown |
| `posture_score` | float | 0.0–1.0 | Heuristic posture score |
| `brightness_level` | int | 1–5 | Relative brightness grade |
| `reminder_triggered` | str | — | Comma-separated reminder types, or empty |

## 4. HUD Display Specification

Overlay items drawn on each frame (top-left origin):

| Position | Content | Format |
|----------|---------|--------|
| Top-left | FPS | `FPS: {fps:.1f}` |
| Top-left, below FPS | Face count | `Faces: {n}` |
| Top-left, below face count | Distance | `Distance: {d:.1f} cm [{category}]` |
| Top-left, below distance | Posture | `Posture: {score:.2f}` |
| Top-left, below posture | Brightness | `Light: Lv.{level}` |
| Top-left, below brightness | Study time | `Study: {mm:ss}` |
| Top-right | Reminder banner | Red/yellow banner text when reminder is active |
| Center | Face box | Green rectangle around detected face |

## 5. Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `q` / `Esc` | Quit application, generate report |
| `Space` | Pause / Resume |
| `c` | Start calibration mode (collect samples) |
| `s` | Save current calibration |
| `b` | Calibrate posture baseline (when `posture.auto_baseline` is true) |
| `r` | Reset session (clear timers and logs) |
| `f` | Toggle fullscreen |
