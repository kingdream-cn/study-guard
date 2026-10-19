# StudyGuard Algorithm Notes

> 算法笔记 — 距离估算、坐姿评分、亮度等级的原理与局限

## Status: Placeholder

This document will be populated after M2 (Distance Calibration) implementation.

## Planned Content

### 1. Distance Estimation

- Model derivation: `d = k / w`
- Least squares fitting formula
- Multi-frame sample collection strategy
- Smoothing window for distance estimates
- Known error sources and expected accuracy range

### 2. Posture Scoring

- Heuristic rules based on face position and size
- Score formula and threshold rationale
- Limitations: what it can and cannot detect

### 3. Brightness Level

- Frame luminance calculation (mean of grayscale)
- Level boundaries and their meaning
- Why this is NOT lux measurement

### 4. Anomaly State Machine

- State transitions
- Duration tracking logic
- Cooldown mechanism
