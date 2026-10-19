# StudyGuard Architecture Decision Records

> 决策记录 — ADR (Architecture Decision Record) 格式

---

## ADR-001: Use Python 3.12 + OpenCV 4.x as Core Stack

**Date**: 2026-10-19
**Status**: Accepted

### Context

StudyGuard requires real-time video processing, face detection, and image analysis on Ubuntu 24.04 Linux. The developer uses Python as primary language and needs a mature computer vision library.

### Decision

- Python 3.12 (system default on Ubuntu 24.04)
- OpenCV 4.6.0+ via `opencv-python` pip package
- NumPy for numerical operations

### Alternatives Considered

| Alternative | Rejected Because |
|------------|-----------------|
| C++ with OpenCV | Higher development cost, harder to test and iterate |
| MediaPipe | Requires model download, heavier dependency, overkill for P0 |
| YOLO-based detection | Requires GPU or heavy CPU, not suitable for P0 lightweight approach |

### Consequences

- Fast development iteration
- Easy testing with pytest
- No GPU dependency
- Limited to Haar Cascade accuracy for face detection (acceptable for P0)

---

## ADR-002: Haar Cascade as P0 Face Detector

**Date**: 2026-10-19
**Status**: Accepted

### Context

Face detection is the foundation of all distance and posture metrics. The detector must work without downloading external models.

### Decision

Use OpenCV's built-in Haar Cascade (`haarcascade_frontalface_default.xml`).

### Alternatives Considered

| Alternative | Rejected Because |
|------------|-----------------|
| YuNet (OpenCV DNN) | Better accuracy but requires model file download — deferred to P1 |
| MediaPipe Face Detection | Requires `mediapipe` package and model download |
| MTCNN | Requires TensorFlow/PyTorch — too heavy for P0 |

### Consequences

- Zero external model dependencies
- Works out of the box with `opencv-python`
- Lower detection accuracy than deep learning alternatives
- Acceptable for P0 proof-of-concept; upgrade path to YuNet in P1

---

## ADR-003: Dual Input — Video File + Camera as First-Class Inputs

**Date**: 2026-10-19
**Status**: Accepted

### Context

The original plan assumed no camera was available. Hardware check revealed a USB2.0 HD UVC WebCam at `/dev/video0`. Both input modes should be formally supported.

### Decision

Both local video files and webcam capture are primary input modes. The `capture.py` module abstracts both behind a unified interface.

### Alternatives Considered

| Alternative | Rejected Because |
|------------|-----------------|
| Camera-only | Cannot run automated tests without a camera; video files are essential for CI |
| Video-file-only | Wastes available hardware; real-time mode is a core use case |

### Consequences

- `capture.py` must provide a unified `VideoCapture` interface
- All tests use video file mode (no camera dependency)
- Users can switch between modes via config or CLI argument

---

## ADR-004: Distance Model d = k / w with Least Squares Fitting

**Date**: 2026-10-19
**Status**: Accepted

### Context

Distance estimation uses the inverse relationship between face bounding box width and distance. The model needs a single parameter k.

### Decision

Model: `d = k / w` where d = distance (cm), w = face width (pixels).
Fit k using least squares: `k = Σ(wᵢ × dᵢ) / Σ(wᵢ²)`.
Require minimum 3 calibration samples, each collected over multiple frames for stability.

### Alternatives Considered

| Alternative | Rejected Because |
|------------|-----------------|
| Single-point calibration | Too sensitive to measurement error |
| Multi-parameter model | Overfitting risk with limited training data |
| Deep learning depth estimation | Requires model download and GPU |

### Consequences

- Simple, transparent, testable
- Accuracy depends on consistent face detection and individual variation
- **Must be documented as non-precision** (see PROJECT_SPEC.md §5.1)

---

## ADR-005: Use venv for Environment Management

**Date**: 2026-10-19
**Status**: Accepted

### Context

System Python already has all dependencies installed. However, for a project that will be open-sourced and reproduced by others, dependency isolation is important.

### Decision

Use `python3 -m venv .venv` for project isolation.

### Alternatives Considered

| Alternative | Rejected Because |
|------------|-----------------|
| System Python directly | Not reproducible; risky to modify system packages |
| conda | Heavier; unnecessary for this project's needs |
| pipenv / poetry | Additional tooling overhead for a small project |

### Consequences

- Clean dependency isolation
- `requirements.txt` can be tested in fresh venv for reproducibility
- `.venv/` added to `.gitignore`
