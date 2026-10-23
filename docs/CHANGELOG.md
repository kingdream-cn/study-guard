# Changelog

All notable changes to StudyGuard will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed

- Detection parameters wired to configuration (O1-A): `FaceDetector` now accepts `scale_factor`, `min_neighbors`, and `min_face_size` (defaults 1.1 / 5 / 30 unchanged, no-arg construction behavior identical to v0.1.0); `main.py` constructs the detector from the `detection.*` config; `config.py` validates `scale_factor` within [1.01, 2.0] and `min_face_size >= 1` (existing `min_neighbors >= 0` retained).

### Added

- HUD Chinese localization (O1-B): `HUDOverlay` gains a `language` parameter (default `"en"`); `hud.language` config (`"zh"` default) drives Chinese labels via Pillow + a system CJK font, with automatic fallback to the English `cv2.putText` path when no CJK font is found. CSV/JSON logs and `DistanceCategory` enum values remain English (Chinese is rendering-layer only).
- HUD warning-banner Chinese translation (O1-B follow-up): the reminder banner body is now localized in the rendering layer — fixed reminder messages map to Chinese, dynamic `"WARNING: <label>"` banners translate each label (e.g. `face_lost`/`distance`/`posture`), and unmatched text is shown verbatim; `reminder.py`/`logger.py` remain unchanged.

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
