# Changelog

All notable changes to StudyGuard will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
