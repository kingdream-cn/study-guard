# StudyGuard Architecture

> 架构设计文档 — 模块职责、数据流、依赖关系

## 1. Module Responsibilities

Each Python file has a single, well-defined responsibility:

| Module | Responsibility | Depends On |
|--------|---------------|------------|
| `main.py` | Entry point. Parse arguments, load config, orchestrate the main loop. | `config`, `capture`, `detector`, `metrics`, `reminder`, `logger`, `hud`, `report` |
| `config.py` | Load, validate, and provide access to JSON configuration. | (stdlib only) |
| `capture.py` | Abstract video input: open file or camera, read frames, release resources. | (OpenCV only) |
| `detector.py` | Face detection using Haar Cascade. Return bounding boxes. | (OpenCV only) |
| `calibrator.py` | Three-point distance calibration. Fit parameter k. Save/load JSON. | `config` |
| `metrics.py` | Compute distance estimate, posture score, brightness level from detection results; track sustained anomalies (AnomalyTracker). | `calibrator` |
| `reminder.py` | 20-20-20 timer, sedentary timer. Consume AnomalyTracker output to emit anomaly reminders. | `metrics`, (stdlib only) |
| `logger.py` | Write session data to CSV at configured interval. Distinguish valid/invalid/anomaly. | `metrics` |
| `report.py` | Generate session summary report (JSON + optional charts). | `logger`, `metrics` |
| `hud.py` | Draw overlay on video frames: bounding boxes, distance, posture, brightness, FPS, reminders. | (OpenCV, Pillow) |

## 2. Data Flow

```
┌─────────────┐
│  Video Input │  (file or camera)
│  capture.py  │
└──────┬───────┘
       │ frame (numpy array)
       ▼
┌─────────────┐
│ Face Detect  │
│ detector.py  │
└──────┬───────┘
       │ list of (x, y, w, h) bounding boxes
       ▼
┌─────────────┐
│  Calibration │  (loads saved k parameter)
│ calibrator.py│
└──────┬───────┘
       │ calibrated k value
       ▼
┌─────────────┐
│   Metrics    │  → distance, posture score, brightness level
│  metrics.py  │
└──────┬───────┘
       │ metrics dict
       ├──────────────────┐
       ▼                  ▼
┌─────────────┐   ┌─────────────┐
│   Reminder   │   │   Logger     │
│  reminder.py │   │   logger.py  │
│  (timers,    │   │  (CSV write) │
│   anomaly    │   └──────┬───────┘
│   tracking)  │          │
└──────┬───────┘          ▼
       │            ┌─────────────┐
       │            │   Report     │
       │            │  report.py   │
       │            └─────────────┘
       ▼
┌─────────────┐
│     HUD      │  → overlay on frame
│    hud.py    │
└─────────────┘
```

## 3. Configuration Loading

```
configs/default.json  ──load──▶  config.py  ──provide──▶  all modules
                                         ▲
                                         │
configs/calibration.json  ──load──┘  (calibration parameters)
```

- `config.py` loads `configs/default.json` at startup.
- Missing keys fall back to hardcoded defaults defined in `config.py`.
- Invalid JSON or out-of-range values raise `ConfigError` at startup (fail-fast).
- Calibration parameters are stored separately in `configs/calibration.json`.

## 4. Error Handling Strategy

| Scenario | Behavior |
|----------|----------|
| Video file not found | Log error, exit with message |
| Camera open failure | Log error, suggest checking device permissions |
| End of video (EOF) | Release resources, generate report, exit cleanly |
| Face not detected in frame | Log as "face_lost", pause timers, continue processing |
| Corrupted config file | Raise `ConfigError` at startup, do not proceed |
| Invalid calibration data | Raise `CalibrationError`, suggest re-calibration |
| Interrupted input (Ctrl+C) | Catch `KeyboardInterrupt`, release resources, save partial report |

## 5. State Management

The application maintains a session state machine:

```
IDLE → RUNNING → PAUSED → RUNNING
                  ↓
              ENDED (report generated)
```

- **IDLE**: Config loaded, no video opened yet.
- **RUNNING**: Processing frames, all timers active.
- **PAUSED**: User pressed pause key; timers frozen, resources held.
- **ENDED**: Video EOF or user quit; report generated, resources released.

Face loss is NOT a state transition — it is tracked within `reminder.py` as a sub-state that pauses distance/posture timers but keeps the session RUNNING.
