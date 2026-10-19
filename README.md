# StudyGuard (明眸)

**OpenCV-based desktop study behavior & eye care assistant**

[中文说明](README_zh.md)

---

## Overview

StudyGuard uses your webcam or local video files to detect faces and estimate relative distance, evaluate posture heuristics, and monitor ambient brightness. It provides timely 20-20-20 eye-care reminders, sedentary break alerts, and generates session reports with statistics and charts.

All processing is **100% local** — no video, images, or personal data are uploaded anywhere.

## Features

### P0 (MVP)

- **Face detection** — Haar Cascade via OpenCV, real-time bounding boxes
- **Distance estimation** — Three-point calibration, inverse proportional model
- **Posture scoring** — Heuristic score based on face position and size
- **Brightness monitoring** — Relative brightness level (1–5) from frame luminance
- **20-20-20 reminders** — Every 20 min of study, remind to look 20 feet away for 20 sec
- **Sedentary reminders** — Configurable sitting duration alert
- **Session logging** — CSV format at configurable intervals
- **Session reports** — Summary with distance distribution, posture stats, charts
- **Dual input** — Local video files and webcam, both fully supported

### Planned (P1)

- YuNet detector for improved accuracy
- Head pose estimation
- Blink detection for fatigue monitoring
- PyInstaller standalone packaging

## Installation

### Requirements

- Python 3.10–3.12
- Ubuntu 24.04 (primary), other Linux distributions should work
- OpenCV-compatible webcam (optional — video files also work)

### Steps

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/study-guard.git
cd study-guard

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# (Optional) Install dev dependencies for testing
pip install -r requirements-dev.txt
```

## Usage

### Run with video file

```bash
python main.py --input file --video path/to/video.mp4
```

### Run with webcam

```bash
python main.py --input camera --camera-index 0
```

### Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `q` / `Esc` | Quit and generate report |
| `Space` | Pause / Resume |
| `c` | Enter calibration mode |
| `s` | Save calibration |
| `r` | Reset session |

## Configuration

All parameters are in `configs/default.json`. Key settings:

- `input.source` — `"file"` or `"camera"`
- `distance.too_close_cm` — Distance threshold for "too close" warning (default: 30)
- `reminder.eye_care_interval_min` — 20-20-20 interval in minutes (default: 20)
- `reminder.sedentary_interval_min` — Sitting reminder interval (default: 45)
- `logging.interval_sec` — CSV log write interval (default: 1.0)

## Testing

```bash
# Activate virtual environment
source .venv/bin/activate

# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=. --cov-report=term-missing
```

All tests run without a real camera — they use synthetic video data and mock inputs.

## Algorithm Notes & Limitations

### Distance Estimation

Distance is estimated using the inverse relationship between face bounding box width and distance (`d = k / w`). Three-point calibration improves accuracy under specific conditions, but **this is not precision ranging**. Results are affected by head angle, detector accuracy, resolution, and individual facial variation.

### Posture Score

Posture scoring is a **heuristic indicator** based on face position and size. It cannot reliably detect all slouching behaviors — it identifies limited suspected poor postures only.

### Brightness Level

Brightness is a **relative grade** (1–5), not a measurement in lux. Camera auto-exposure alters frame brightness, so this indicates trends rather than absolute light levels.

## Privacy

- All processing is local. No data is uploaded.
- Session logs and reports are stored locally in `logs/` and `reports/`.
- No network connection required for core functionality.

## License

MIT License. See [LICENSE](LICENSE).

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development workflow and coding standards.

## Project Documentation

| Document | Description |
|----------|-------------|
| [PROJECT_SPEC.md](docs/PROJECT_SPEC.md) | Project specification and feature boundaries |
| [PROJECT_RULES.md](docs/PROJECT_RULES.md) | Development rules (AI assistant constitution) |
| [ARCHITECTURE.md](docs/ARCHITECTURE.md) | Module responsibilities and data flow |
| [INTERFACE_SPEC.md](docs/INTERFACE_SPEC.md) | Interface definitions and data formats |
| [CODING_STANDARDS.md](docs/CODING_STANDARDS.md) | Coding conventions |
| [TEST_PLAN.md](docs/TEST_PLAN.md) | Test scenarios by milestone |
| [DECISIONS.md](docs/DECISIONS.md) | Architecture decision records |
| [ALGORITHM_NOTES.md](docs/ALGORITHM_NOTES.md) | Algorithm details and limitations |
| [ROADMAP.md](ROADMAP.md) | Development milestones and timeline |
| [PROJECT_STATUS.md](PROJECT_STATUS.md) | Current progress |
