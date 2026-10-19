# StudyGuard Project Specification

> 明眸 StudyGuard — 项目规格说明书

## 1. Project Overview

StudyGuard is an OpenCV-based desktop tool that assists students in monitoring study behavior and eye-care habits. It processes video frames (from local video files or a webcam) to detect faces, estimate relative distance, evaluate posture heuristics, and provide timely reminders.

**Target Users**: Students and self-learners who want to maintain healthy study habits at a desk.

**Core Value**: Provide real-time, local-only feedback on study posture and eye usage — no cloud services, no data upload.

## 2. Input Modes

| Input Mode   | Status in P0 | Notes |
|-------------|-------------|-------|
| Local video file | **Primary** | Must work from Day 1; all automated tests use this mode |
| Webcam (USB camera) | **Primary** | `/dev/video0` confirmed available; real-time capture mode |

Both input modes are first-class citizens. The application must support seamless switching between them via configuration or command-line argument.

## 3. Feature Priority Levels

### P0 — Must Complete (MVP)

| Feature | Acceptance Criteria |
|---------|-------------------|
| Video file reading | Open, read frames, report FPS, release resources on EOF |
| Webcam capture | Open camera device, read frames, release on exit |
| Haar face detection | Detect faces with bounding boxes in every processed frame |
| Distance calibration | Three-point calibration, save/load parameters as JSON |
| Distance estimation | Estimate relative distance from face bounding box width |
| Posture scoring | Heuristic score based on face position and size in frame |
| Brightness level | Relative brightness grade from frame luminance |
| Anomaly state machine | Detect sustained anomalies with duration threshold and cooldown |
| 20-20-20 reminder | Remind to look far away after 20 min continuous eye use |
| Sedentary reminder | Remind to stand up after configurable sitting duration |
| CSV session log | Record metrics at configurable interval (not every frame) |
| JSON configuration | All thresholds and parameters in external config file |
| Session report | Generate summary with distance distribution, posture stats, brightness stats, reminder count |
| Error handling | Graceful handling of EOF, missing files, corrupted config, face loss |
| Automated tests | pytest suite covering all P0 modules without requiring a real camera |

### P1 — After MVP Stabilizes

| Feature | Notes |
|---------|-------|
| YuNet detector | Replace Haar for better accuracy |
| Head pose estimation | 6-DOF pose from facial landmarks |
| Blink detection | Eye aspect ratio for fatigue monitoring |
| UI improvements | Better HUD layout, color coding |
| Report trend charts | matplotlib time-series in reports |
| PyInstaller packaging | Standalone executable for distribution |

### P2 — Not Scheduled

| Feature | Notes |
|---------|-------|
| YOLO phone detection | Object detection for distraction monitoring |
| Focus model | ML-based attention scoring |
| ROS 2 smart lamp integration | Hardware automation |
| Cloud sync | Multi-device data synchronization |
| Family sharing | Parent dashboard |
| Account system | User authentication |
| Weekly report platform | Multi-session aggregation web app |

## 4. Technology Stack

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| Language | Python | 3.10–3.12 | Business logic and module organization |
| Vision library | OpenCV | 4.x | Video I/O, image processing, face detection, HUD |
| Face detector | Haar Cascade | OpenCV built-in | P0 face detection (no model download required) |
| Numerical computing | NumPy | ≥1.24 | Array operations, calibration math |
| Charting | matplotlib | ≥3.6 | Report trend charts |
| Image rendering | Pillow | ≥10.0 | Chinese text overlay on HUD |
| Testing | pytest | ≥7.0 | Automated test suite |
| Configuration | JSON | — | Config files, calibration parameters |
| Logging | CSV | — | Session data records |
| Packaging | pathlib | stdlib | Cross-platform path handling |

### Not Used in P0

- PyQt / Tkinter / any GUI framework
- YOLO / MediaPipe / deep learning models
- ROS 2
- Cloud services / databases
- GPU / CUDA dependencies

## 5. Technical Boundary Declarations

These limitations **must** be documented in the README and all user-facing materials:

### 5.1 Distance Estimation Is Not Precision Ranging

Face bounding box width is affected by head angle, detector accuracy, resolution, and individual facial variation. Three-point calibration improves estimation under specific conditions but **cannot guarantee ±5 cm accuracy across all scenes**.

### 5.2 Posture Score Is a Heuristic Indicator

Face position and size alone cannot reliably detect all slouching behaviors. The first version can only identify **limited suspected poor postures** based on simple geometric rules.

### 5.3 Brightness Level Is Not True Illuminance

Camera auto-exposure alters frame brightness. The reported value is a **relative brightness grade**, not a measurement in lux. It indicates trends (getting darker/brighter) but not absolute light levels.

## 6. Data Privacy

- All processing is local. No video frames, face images, or personal data are uploaded.
- Session logs (CSV) and reports are stored locally in the `logs/` and `reports/` directories.
- No network connection is required for core functionality.
- Configuration files contain no personal identifiers.

## 7. Scope Freeze Rule

> P0 must be fully verified before any P1 or P2 work begins.
> No feature, technology, or architecture change may be made without explicit user approval.
> When in doubt, stick to the plan.
