# StudyGuard Roadmap

> 5-Day MVP Development Plan

## Overview

| Day | Session | Milestone | Focus |
|-----|---------|-----------|-------|
| Day 1 AM | — | **M0** | Project initialization (COMPLETED) |
| Day 1 PM | — | **M1** | Visual foundation |
| Day 2 | All day | **M2** | Distance calibration & estimation |
| Day 3 | All day | **M3** | Behavior metrics & anomaly state machine |
| Day 4 AM | — | **M4** | Reminders & logging |
| Day 4 PM | — | **M5** | Report generation |
| Day 5 AM | — | **M6** | Testing & stability |
| Day 5 PM | — | **M7** | Open-source release |

---

## M0: Project Initialization ✅ COMPLETED

**Duration**: Day 1 AM (completed by Qoder)

**Deliverables**:
- Project directory structure
- All planning documents (SPEC, RULES, ARCHITECTURE, INTERFACE_SPEC, CODING_STANDARDS, TEST_PLAN, DECISIONS)
- Engineering files (.gitignore, requirements.txt, pyproject.toml, LICENSE, README)
- Virtual environment with dependencies
- GitHub repository initialized

**Acceptance**: Directory complete, docs comprehensive, git initialized, GitHub repo ready.

---

## M1: Visual Foundation

**Duration**: Day 1 PM

**Tasks**:
- `capture.py` — Unified video input (file + camera)
- `detector.py` — Haar face detection with bounding boxes
- `hud.py` — Basic HUD overlay (FPS, face count, bounding box)
- `main.py` — Main loop: open input → detect → display → handle quit

**Acceptance Criteria**:
- [ ] Local video file opens and displays face boxes in real-time
- [ ] Camera input opens and displays face boxes in real-time
- [ ] FPS counter shows on HUD
- [ ] Pressing `q` or `Esc` exits cleanly and releases resources
- [ ] Missing video file produces clear error message
- [ ] All M1 tests pass (`pytest tests/test_capture.py tests/test_detector.py`)

---

## M2: Distance Calibration & Estimation

**Duration**: Day 2 (all day)

**Tasks**:
- `calibrator.py` — Three-point calibration, least squares fit, save/load JSON
- `metrics.py` (partial) — Distance estimation from face width
- HUD update — Show distance value and category

**Acceptance Criteria**:
- [ ] Can collect calibration samples at known distances
- [ ] `k` parameter fitted via least squares
- [ ] Calibration saved to and loaded from `configs/calibration.json`
- [ ] Distance displayed on HUD in real-time
- [ ] Distance categories (too_close / normal / too_far) correctly classified
- [ ] All M2 tests pass (`pytest tests/test_calibrator.py`)
- [ ] Error recorded for known-distance test samples

---

## M3: Behavior Metrics & Anomaly State Machine

**Duration**: Day 3 (all day)

**Tasks**:
- `metrics.py` (complete) — Posture score, brightness level
- Anomaly tracking — Duration threshold, cooldown mechanism
- State machine — Normal / warning / critical states

**Acceptance Criteria**:
- [ ] Posture score computed from face position and size (0.0–1.0)
- [ ] Brightness level computed from frame luminance (1–5)
- [ ] Anomaly detected when metric stays out of range for configured duration
- [ ] Cooldown prevents duplicate warnings within configured period
- [ ] All M3 tests pass (`pytest tests/test_metrics.py`)
- [ ] Each metric has clear, interpretable output

---

## M4: Reminders & Logging

**Duration**: Day 4 AM

**Tasks**:
- `reminder.py` — 20-20-20 timer, sedentary timer, injectable clock
- `logger.py` — CSV session logging at configured interval
- `config.py` — Full JSON configuration loading and validation

**Acceptance Criteria**:
- [ ] 20-20-20 reminder triggers after 20 min of effective study time
- [ ] Sedentary reminder triggers after configured sitting duration
- [ ] Timers pause when face is lost, resume when face returns
- [ ] CSV log written at configured interval (not every frame)
- [ ] CSV format matches INTERFACE_SPEC.md
- [ ] JSON config loads all parameters with fallback defaults
- [ ] Invalid config raises ConfigError at startup
- [ ] All M4 tests pass (`pytest tests/test_reminder.py tests/test_config.py`)

---

## M5: Report Generation

**Duration**: Day 4 PM

**Tasks**:
- `report.py` — Session summary with statistics and charts
- matplotlib integration — Distance distribution, posture/brightness trends

**Acceptance Criteria**:
- [ ] Report generated at session end
- [ ] Report includes: session duration, effective study time, distance stats, posture stats, brightness stats, reminder count
- [ ] Charts rendered with matplotlib (if enabled in config)
- [ ] Empty or insufficient data produces "Insufficient data" message, not misleading stats
- [ ] Report does not crash on corrupted log files
- [ ] All M5 tests pass (`pytest tests/test_report.py`)

---

## M6: Testing & Stability

**Duration**: Day 5 AM

**Tasks**:
- Complete all test cases from TEST_PLAN.md
- Edge case handling: EOF, no face, corrupted config, missing files
- Resource cleanup verification

**Acceptance Criteria**:
- [ ] All tests in TEST_PLAN.md pass
- [ ] Zero-length video handled gracefully
- [ ] Corrupted video file does not crash
- [ ] Face never detected → runs to completion
- [ ] Keyboard interrupt → resources released, partial report saved
- [ ] No memory leaks in extended processing
- [ ] Test coverage report generated

---

## M7: Open-Source Release

**Duration**: Day 5 PM

**Tasks**:
- README.md finalization (English + Chinese)
- Screenshots and demo video capture
- LICENSE verification
- GitHub Actions CI setup (run pytest on push)
- Release tag (v0.1.0)

**Acceptance Criteria**:
- [ ] README contains: intro, screenshots, features, install, run, test, algorithm notes, limitations, license
- [ ] Fresh `git clone` + `pip install` + `pytest` passes in clean venv
- [ ] GitHub Actions workflow runs tests automatically
- [ ] No sensitive data, real face videos, or credentials in repository
- [ ] Release tagged as v0.1.0

---

## Post-MVP (P1 — Not Scheduled)

- YuNet detector upgrade
- Head pose estimation
- Blink detection
- UI improvements
- Report trend charts enhancement
- PyInstaller packaging

## Future (P2 — Not Scheduled)

- YOLO phone detection
- Focus/attention model
- ROS 2 smart lamp integration
- Cloud sync, family sharing, account system
