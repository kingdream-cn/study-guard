# StudyGuard (明眸)

**OpenCV-based desktop study behavior & eye care assistant**

[中文说明](README_zh.md)

[![tests](https://github.com/kingdream-cn/study-guard/actions/workflows/tests.yml/badge.svg)](https://github.com/kingdream-cn/study-guard/actions/workflows/tests.yml)

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

### Delivered after the MVP (v0.2.x – v0.3.0)

- **Configurable detection parameters** — `scale_factor`, `min_neighbors` and `min_face_size`
  drive detection at runtime instead of being validated and ignored
- **Localized HUD** — Chinese overlay labels; logs, reports and CSV fields stay English
- **Directional distance reminders** — "too close" and "too far" have independent cooldowns,
  so one direction no longer silences the other for a minute
- **Actionable banner text** — the banner says whether to move back or move closer
- **Per-backend calibration** — `k` is stored per detector backend; a backend without its own
  calibration reports `--` rather than borrowing another backend's `k`
- **Optional YuNet backend** — see below

### Optional: YuNet detector backend (v0.3.0)

Haar Cascade drops the face box on small pose changes. Measured on real hardware
(4 poses, ~10 s each, same seat, same machine; lost frames / samples):

| Pose | Haar | YuNet |
|---|---|---|
| Upright, frontal | 1/10 | 0/10 |
| Side face ~45° | 2/10 | 0/10 |
| **Slight head down** | **10/10 (whole segment lost)** | 1/10 |
| Forehead covered by fringe | 7/10 | 1/8 |

YuNet is therefore **wired in but not the default**, for two reasons: the `.onnx` model is not
committed to this repository, and distance calibration is backend-bound — YuNet measures face
width differently, so `k = 11488.3` does not transfer (see
[Algorithm notes](#distance-estimation)).

To enable it:

```bash
mkdir -p ~/study_models
curl -L -o ~/study_models/face_detection_yunet_2023mar.onnx \
  https://github.com/opencv/opencv_zoo/raw/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx
```

Then set `detection.backend` to `"yunet"` in your config and re-run the three-point calibration
(`c` three times, then `s`). Until you do, distance reads `--` under YuNet; nothing else breaks.
The default backend stays Haar so that a fresh clone runs with no downloads.

### Not planned (scope frozen)

Head pose estimation, blink/fatigue detection, and PyInstaller standalone packaging were
considered and **deliberately dropped** — this project stops at v0.3.0.

## Installation

### Requirements

- Python 3.10–3.12
- Ubuntu 24.04 (primary), other Linux distributions should work
- OpenCV-compatible webcam (optional — video files also work)

### Steps

```bash
# Clone the repository
git clone https://github.com/kingdream-cn/study-guard.git
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
python main.py --source file --path path/to/video.mp4
```

### Run with webcam

```bash
python main.py --source camera --camera-index 0
```

### Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `q` / `Esc` | Quit and generate report |
| `Space` | Pause / Resume |
| `c` | Enter calibration mode |
| `s` | Save calibration |
| `b` | Calibrate posture baseline |
| `r` | Reset session |

## Configuration

All parameters are in `configs/default.json`. Key settings:

- `input.source` — `"file"` or `"camera"`
- `distance.too_close_cm` — Distance threshold for "too close" warning (default: 30)
- `reminder.eye_care_interval_min` — 20-20-20 interval in minutes (default: 20)
- `reminder.sedentary_interval_min` — Sitting reminder interval (default: 45)
- `logging.interval_sec` — CSV log write interval (default: 1.0)
- `detection.backend` — `"haar"` (default) or `"yunet"`; `"yunet"` requires a local model file and
  its own calibration
- `detection.model_path` — YuNet model location (default: `~/study_models/face_detection_yunet_2023mar.onnx`,
  **not** shipped with this repository)
- `hud.language` — `"en"` (default) or `"zh"`, HUD overlay only

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

> If your shell has ROS 2 sourced (which sets `PYTHONPATH`), prefix the test command with
> `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1`, e.g. `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest tests/ -v`.

## Algorithm Notes & Limitations

### Distance Estimation

Distance is estimated using the inverse relationship between face bounding box width and distance (`d = k / w`). Three-point calibration improves accuracy under specific conditions, but **this is not precision ranging**. Results are affected by head angle, detector accuracy, resolution, and individual facial variation.

#### Measured accuracy (v0.1.0)

Using one reference calibration (`k = 11488.3`) and a straight data-cable ground truth
(screen top edge → nose tip, ±2–3 cm uncertainty), independent samples measured:

| Ground truth | HUD reading | Relative error |
|---|---|---|
| 40 cm | 44–45 cm | +10–12% |
| 60 cm | 61–62 cm | +2–3% |

The systematic error converges at longer distances; near range is most sensitive to head
angle and posture. These are relative estimates, not precision ranging.

#### The calibration constant is backend-bound

`k` is fitted from the face-box width a specific detector produces, so it does not transfer
between backends. The YuNet/Haar width ratio measured 0.771 on a real seat but 0.864 on an
offline test image — **not a constant**, which is why there is no conversion factor and each
backend needs its own three-point calibration. Calibration data lives in
`configs/calibration.json`: the top-level `k`/`samples` are the Haar entry, other backends live
under `backends.<name>`. A backend with no entry of its own raises
`该后端尚未标定` at startup and reports `--`; it never falls back to another backend's `k`.

#### Known limits we chose to keep

- `too_close_cm = 30.0` sits inside the Haar width noise band (the same pose measures
  143–430 px, i.e. 26.7–80.9 cm), so whether a genuine 28 cm triggers depends on how wide the
  detector draws the box that frame. Re-tuning it is backend-bound work and was **explicitly
  dropped** with v0.3.0, not overlooked.
- `min_face_size`, `scale_factor` and `min_neighbors` all change the box width itself, so they
  are ranging inputs, not harmless filters. Do not adjust them after calibrating.
- A symmetric background pattern (e.g. a cube logo on a wall) can still be detected as a face by
  Haar; the code takes the largest box and a 30-frame median, which covers most of it.

Full records: [ALGORITHM_NOTES.md](docs/ALGORITHM_NOTES.md) (§8 parameters, §10 defect history,
§11 backend comparison).

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
