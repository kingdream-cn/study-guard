# StudyGuard Test Plan

> 测试方案 — 按里程碑组织

## General Principles

- All tests run via `pytest` from the project root.
- No test may require a real camera. Use mock data, synthetic frames, or synthetic video files.
- Timer-dependent tests must use injectable clock — never rely on real elapsed time.
- Each milestone's tests must pass before moving to the next milestone.

---

## M0: Project Initialization

| Test | Type | Description | Expected |
|------|------|-------------|----------|
| `test_venv_python_version` | Environment | Verify Python version is 3.10–3.12 | Pass |
| `test_opencv_import` | Environment | `import cv2` succeeds | Pass |
| `test_video_read_basic` | Integration | Open a test video file, read one frame, release | Frame is not None, resource released |

**Note**: M0 tests are manual verification commands, not automated pytest.

---

## M1: Visual Foundation

| Test | Type | Description | Expected |
|------|------|-------------|----------|
| `test_capture_open_file` | Unit | Open valid video file | `is_opened` is True |
| `test_capture_open_missing_file` | Unit | Open non-existent file | Raises `FileNotFoundError` |
| `test_capture_read_frame` | Unit | Read frame from valid video | Returns `(True, ndarray)` with correct shape |
| `test_capture_read_eof` | Unit | Read past end of video | Returns `(False, None)` |
| `test_capture_release` | Unit | Release and verify `is_opened` is False | Safe to call twice |
| `test_capture_open_camera` | Unit | Open camera with mocked `cv2.VideoCapture` | `is_opened` is True |
| `test_detector_detect_faces` | Unit | Detect faces in synthetic frame with drawn face-like pattern | Returns non-empty list |
| `test_detector_detect_no_faces` | Unit | Detect in blank/black frame | Returns empty list |
| `test_face_box_center` | Unit | `FaceBox(10, 20, 100, 80).center` | Returns `(60, 60)` |
| `test_face_box_area` | Unit | `FaceBox(0, 0, 100, 80).area` | Returns `8000` |

---

## M2: Distance Calibration

| Test | Type | Description | Expected |
|------|------|-------------|----------|
| `test_add_sample_valid` | Unit | Add valid sample | No exception |
| `test_add_sample_invalid_distance` | Unit | Add sample with distance ≤ 0 | Raises `ValueError` |
| `test_add_sample_invalid_width` | Unit | Add sample with width ≤ 0 | Raises `ValueError` |
| `test_fit_with_three_samples` | Unit | Fit with 3 valid samples | Returns positive k value |
| `test_fit_insufficient_samples` | Unit | Fit with < 3 samples | Raises `CalibrationError` |
| `test_estimate_distance_calibrated` | Unit | Estimate with fitted calibrator | Returns positive distance |
| `test_estimate_distance_not_calibrated` | Unit | Estimate before fitting | Returns `None` |
| `test_save_and_load` | Unit | Save calibration, load into new instance | k values match |
| `test_load_missing_file` | Unit | Load non-existent file | Raises `CalibrationError` |
| `test_load_corrupted_file` | Unit | Load invalid JSON | Raises `CalibrationError` |
| `test_least_squares_accuracy` | Unit | Verify k fits correctly for known data | Error < 1% for synthetic data |

---

## M3: Behavior Metrics & Anomaly State Machine

| Test | Type | Description | Expected |
|------|------|-------------|----------|
| `test_distance_category_too_close` | Unit | Distance < too_close_cm | `TOO_CLOSE` |
| `test_distance_category_normal` | Unit | Distance in range | `NORMAL` |
| `test_distance_category_too_far` | Unit | Distance > too_far_cm | `TOO_FAR` |
| `test_distance_category_no_face` | Unit | No face detected | `UNKNOWN` |
| `test_posture_score_ideal` | Unit | Face at ideal position | Score near 1.0 |
| `test_posture_score_bad_position` | Unit | Face at edge of frame | Score near 0.0 |
| `test_posture_score_no_face` | Unit | No face detected | Score is 0.0 or defined fallback |
| `test_brightness_level_dark` | Unit | Dark frame (low mean luminance) | Level 1–2 |
| `test_brightness_level_bright` | Unit | Bright frame (high mean luminance) | Level 4–5 |
| `test_anomaly_duration_tracking` | Unit | Sustained anomaly for N seconds | Anomaly registered after threshold |
| `test_anomaly_cooldown` | Unit | Reminder triggered, then cooldown period | No duplicate reminder during cooldown |
| `test_anomaly_recovery` | Unit | Anomaly resolves, then re-occurs | New anomaly tracked after recovery |

---

## M4: Reminders & Logging

| Test | Type | Description | Expected |
|------|------|-------------|----------|
| `test_eye_care_reminder_triggers` | Unit | 20 min of effective study time with mock clock | ReminderEvent emitted |
| `test_eye_care_reminder_not_premature` | Unit | 19 min elapsed | No reminder |
| `test_sedentary_reminder_triggers` | Unit | 45 min session time with mock clock | ReminderEvent emitted |
| `test_pause_freezes_timers` | Unit | Pause at 10 min, wait (mock) 30 min, resume | Timer resumes from 10 min |
| `test_face_lost_excluded_from_study_time` | Unit | Face lost for 5 min | `effective_study_time` excludes those 5 min |
| `test_csv_log_interval` | Unit | Log at 1s interval, process 10 frames in 0.5s | Only expected rows written |
| `test_csv_log_format` | Integration | Verify CSV header and data types | Matches INTERFACE_SPEC |
| `test_json_config_load` | Unit | Load valid config | All values accessible |
| `test_json_config_missing_key` | Unit | Config missing optional key | Falls back to default |
| `test_json_config_invalid_value` | Unit | Config with out-of-range value | Raises `ConfigError` |

---

## M5: Report Generation

| Test | Type | Description | Expected |
|------|------|-------------|----------|
| `test_report_generate_normal` | Integration | Generate report from valid log | Report file created with correct content |
| `test_report_empty_log` | Integration | Generate report from empty CSV | Report says "Insufficient data" |
| `test_report_all_face_lost` | Integration | Log where face_detected is always False | Report says "Insufficient data" |
| `test_report_distance_distribution` | Integration | Verify distance stats in report | Correct mean/min/max |
| `test_report_reminder_count` | Integration | Verify reminder counts | Matches log data |
| `test_report_no_crash_on_corrupted_log` | Integration | Feed malformed CSV | Graceful error, no crash |

---

## M6: Stability & Edge Cases

| Test | Type | Description | Expected |
|------|------|-------------|----------|
| `test_zero_length_video` | Integration | Video with 0 frames | Clean exit, no crash |
| `test_corrupted_video_file` | Integration | Truncated/invalid video file | Error logged, clean exit |
| `test_all_frames_no_face` | Integration | Video where no face is ever detected | Runs to completion, report generated |
| `test_rapid_face_appear_disappear` | Integration | Face flickers in/out | State machine handles gracefully |
| `test_keyboard_interrupt` | Integration | Send SIGINT during processing | Resources released, partial report saved |
| `test_config_file_deleted_mid_session` | Integration | Delete config while running | No crash (config loaded at startup) |
| `test_log_directory_not_writable` | Unit | Log to read-only directory | Error logged at startup |
| `test_very_large_frame` | Unit | Process 4K resolution frame | No crash, reasonable performance |

---

## Test Execution Commands

```bash
# Activate virtual environment
source .venv/bin/activate

# Run all tests
pytest tests/ -v

# Run tests for a specific module
pytest tests/test_calibrator.py -v

# Run with coverage
pytest tests/ --cov=. --cov-report=term-missing

# Run without camera-dependent tests (all of them should be camera-free)
pytest tests/ -v -m "not requires_camera"
```
