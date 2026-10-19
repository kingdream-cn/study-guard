# StudyGuard Coding Standards

> 编码规范 — 所有 P0 开发必须遵循

## 1. Naming Conventions

| Element | Convention | Example |
|---------|-----------|---------|
| Module (file) | `snake_case.py` | `calibrator.py` |
| Class | `PascalCase` | `DistanceCalibrator` |
| Function / method | `snake_case` | `estimate_distance` |
| Variable | `snake_case` | `face_width_px` |
| Constant | `UPPER_SNAKE_CASE` | `DEFAULT_SCALE_FACTOR` |
| Config JSON key | `snake_case` | `eye_care_interval_min` |
| Enum member | `UPPER_SNAKE_CASE` | `DistanceCategory.TOO_CLOSE` |
| Enum value | `snake_case` string | `"too_close"` |
| Private member | `_leading_underscore` | `_k_value` |

## 2. Type Annotations

All public functions **must** have type annotations for parameters and return values.

```python
# Good
def estimate_distance(self, face_width_px: float) -> Optional[float]:
    ...

# Bad — missing return type
def estimate_distance(self, face_width_px: float):
    ...
```

Use `Optional[T]` for values that may be `None`. Use `list[T]` not `List[T]` (Python 3.10+).

## 3. Docstrings

Use **Google style** docstrings. All public classes and functions must have docstrings.

```python
class DistanceCalibrator:
    """Three-point distance calibration using face box width.

    Model: d = k / w
    Where d = distance (cm), w = face box width (pixels), k = fitted constant.
    """

    def fit(self) -> float:
        """Fit parameter k using least squares.

        Returns:
            Fitted k value.

        Raises:
            CalibrationError: If fewer than 3 samples have been added.
        """
```

## 4. Error Handling

| Situation | Action |
|-----------|--------|
| Invalid config at startup | Raise `ConfigError`, exit immediately (fail-fast) |
| Invalid calibration data | Raise `CalibrationError` |
| Video file not found | Raise `FileNotFoundError` with clear message |
| Camera open failure | Raise `RuntimeError` with device index |
| Face not detected in a frame | Return fallback metrics, log warning — do NOT raise |
| Unexpected runtime error | Log error, continue processing next frame if possible |

**Rules**:
- Never use bare `except:` — always catch specific exception types.
- Never swallow exceptions silently — always log or re-raise.
- Use custom exception classes (`ConfigError`, `CalibrationError`) for domain errors.

## 5. Timing

- Use `time.monotonic()` for all duration measurements and timers.
- Never use `time.time()` for interval tracking (system clock can jump).
- The `ReminderManager` accepts an injectable `clock` parameter for testing:

```python
class ReminderManager:
    def __init__(self, config: AppConfig,
                 clock: Optional[Callable[[], float]] = None) -> None:
        self._clock = clock or time.monotonic
```

## 6. Path Handling

- Always use `pathlib.Path`, never string concatenation for paths.
- Never hardcode absolute paths.
- Resolve project-relative paths from the project root:

```python
PROJECT_ROOT = Path(__file__).resolve().parent
DEFAULT_CONFIG = PROJECT_ROOT / "configs" / "default.json"
```

## 7. Resource Management

- Always use `try/finally` or context managers for video capture.
- `VideoCapture.release()` must be safe to call multiple times.
- On `KeyboardInterrupt`, release all resources before exiting.

```python
capture = VideoCapture(InputSource.FILE, path=video_path)
try:
    while capture.is_opened:
        success, frame = capture.read()
        if not success:
            break
        # process frame
finally:
    capture.release()
```

## 8. Testing Standards

| Rule | Detail |
|------|--------|
| Test file naming | `test_<module>.py` |
| Test function naming | `test_<behavior>_<condition>` |
| Camera dependency | **Forbidden** — all tests must use mock data or synthetic video |
| Time dependency | Use injectable clock, never real time in tests |
| Fixture scope | Use `@pytest.fixture` for reusable setup |
| Assertions | One logical assertion per test when possible |
| Coverage target | Core modules (calibrator, metrics, reminder) must have tests |

```python
# Good test name
def test_fit_raises_with_fewer_than_three_samples():
    ...

# Bad test name
def test_calibrator():
    ...
```

## 9. Import Order

1. Standard library imports
2. Third-party imports (cv2, numpy, etc.)
3. Local project imports

```python
import time
from pathlib import Path
from typing import Optional

import cv2
import numpy as np

from study_guard.calibrator import DistanceCalibrator
```

## 10. Constants and Thresholds

- Never hardcode magic numbers in business logic.
- All thresholds go in `configs/default.json` and are accessed via `AppConfig`.
- Module-level constants (like OpenCV cascade paths) go at the top of the module:

```python
DEFAULT_CASCADE_PATH = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
```
