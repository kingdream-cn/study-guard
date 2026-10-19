# Security & Privacy Policy

## Data Processing

StudyGuard processes video frames locally on your machine. **No data is ever uploaded, transmitted, or shared externally.**

### What StudyGuard Accesses

- **Video frames** from your webcam or local video files — processed in memory, never saved as images
- **Configuration files** — local JSON files only
- **Session logs** — written to local `logs/` directory as CSV

### What StudyGuard Does NOT Do

- Does not upload video frames or face images
- Does not connect to any external server
- Does not collect personal information
- Does not store identifiable face data
- Does not require an account or authentication

## Session Data

Session logs (CSV files) and reports are stored locally in:

- `logs/` — Raw session metrics
- `reports/` — Generated session summaries

These files contain only numerical measurements (distances, scores, timestamps). No face images or video frames are saved.

## Reporting Vulnerabilities

If you discover a security vulnerability in StudyGuard, please:

1. **Do not** open a public issue.
2. Contact the maintainers privately through GitHub's [private vulnerability reporting](https://docs.github.com/en/code-security/security-advisories/guidance-on-reporting-and-writing/privately-reporting-a-security-vulnerability).
3. Include a description of the vulnerability and steps to reproduce.

We will acknowledge receipt within 48 hours and provide a timeline for the fix.

## Dependencies

StudyGuard depends on the following third-party packages:

- `opencv-python` — Video processing and face detection
- `numpy` — Numerical computation
- `matplotlib` — Report charts
- `Pillow` — Image rendering

If you discover a vulnerability in any of these dependencies, please report it to the respective project maintainers. We will update our dependencies promptly when security patches are available.

## Best Practices for Users

1. Run StudyGuard in a virtual environment to isolate dependencies.
2. Keep your system and Python packages up to date.
3. Review `configs/default.json` before running — ensure paths and settings are as expected.
4. Do not commit `configs/calibration.json` if it contains environment-specific data you wish to keep private (it is already in `.gitignore`).
