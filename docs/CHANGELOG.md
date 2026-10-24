# Changelog

All notable changes to StudyGuard will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- YuNet detector backend (O2-A): `FaceDetector` gains `backend` (`"haar"` default, `"yunet"` opt-in), `model_path`, `score_threshold` (0.9), `nms_threshold` (0.3), and `top_k` (5000). The YuNet path runs on the native frame size (`setInputSize()` on frame-size changes) and converts `(N,15)` output to `FaceBox` via the pure `yunet_faces_to_boxes()` function (`int(round())` + frame clamping). New `detection.*` config keys are validated; a missing model with `backend="yunet"` aborts startup instead of falling back to Haar. No new pip dependency and the `.onnx` model is not committed.

### Notes

- The default backend remains Haar. The existing `k=11488.3` is based on Haar face widths; switching the default to YuNet requires recalibration or a width-conversion factor (O2-B).

## [0.2.0] - 2026-10-23

### Changed

- Detection parameters wired to configuration (O1-A): `FaceDetector` now accepts `scale_factor`, `min_neighbors`, and `min_face_size` (defaults 1.1 / 5 / 30 unchanged, no-arg construction behavior identical to v0.1.0); `main.py` constructs the detector from the `detection.*` config; `config.py` validates `scale_factor` within [1.01, 2.0] and `min_face_size >= 1` (existing `min_neighbors >= 0` retained).

### Added

- HUD Chinese localization (O1-B): `HUDOverlay` gains a `language` parameter (default `"en"`); `hud.language` config (`"zh"` default) drives Chinese labels via Pillow + a system CJK font, with automatic fallback to the English `cv2.putText` path when no CJK font is found. CSV/JSON logs and `DistanceCategory` enum values remain English (Chinese is rendering-layer only).
- HUD warning-banner Chinese translation (O1-B follow-up): the reminder banner body is now localized in the rendering layer — fixed reminder messages map to Chinese, dynamic `"WARNING: <label>"` banners translate each label (e.g. `face_lost`/`distance`/`posture`), and unmatched text is shown verbatim; `reminder.py`/`logger.py` remain unchanged.

## [0.2.1] - 2026-10-23

### Fixed

- Cross-direction distance warnings no longer silence each other (D1). `too_close` and `too_far` are now tracked under separate anomaly keys (`distance_close` / `distance_far`) instead of sharing one `distance` key and its cooldown. **User-visible:** after a "too far" warning, moving too close now raises a new warning; previously it stayed silent for up to `reminder.cooldown_sec` (60 s). The same-direction cooldown is unchanged.
- Whole-sentence warning banners are reachable again (D3). Banner selection moved to the pure function `select_banner()`; within `BANNER_HOLD_SEC` (3 s) of a trigger the HUD shows the event's full message, after that an active warning falls back to `WARNING: <label>`, and the banner clears when neither applies. **User-visible:** during a sustained too-close period the HUD shows the full sentence for the first 3 s (`Too close — move back` / Chinese "距离过近，请后退"), then `WARNING: distance_too_close` / Chinese "警告：距离过近". Previously the label form overwrote the sentence immediately.

### Changed

- Distance warnings are direction-specific: `active_warnings()` returns `distance_too_close` or `distance_too_far` instead of `distance`, and the distance reminder messages are now `"Too close — move back"` / `"Too far — move closer"` (previously `"Adjust viewing distance"`). Chinese HUD mappings were added for the new labels ("距离过近" / "距离过远") and whole sentences. `ReminderType` values, CSV headers, column order, and configuration values are unchanged; the legacy `"distance"` / `"Adjust viewing distance"` translation entries remain for older logs.

## [0.1.0] - 2026-10-21

### Added

- Project initialization (M0): directory structure, documentation, configuration
- Visual foundation (M1): unified file/camera capture, Haar Cascade face detection, HUD (FPS, face count, boxes)
- Distance calibration & estimation (M2): three-point least-squares calibration, JSON save/load, HUD distance
- Behavior metrics (M3): posture score, brightness level, anomaly state machine (duration + cooldown)
- Reminders & logging (M4): 20-20-20, sedentary, face-lost and anomaly reminders, CSV session logging, JSON config, explicit posture baseline (`b`)
- Session reports (M5): JSON summary + optional matplotlib PNG charts
- Stability (M6): eight edge-case tests (zero-length/corrupted video, no-face, flicker, SIGINT, config deletion, unwritable log dir, 4K frames), `--headless` and `--config` options
- GitHub Actions CI workflow

### Notes

- No real-face screenshots or videos are included in the repository (privacy).
- Distance estimation is a relative estimate, not precision ranging.
