# StudyGuard Algorithm Notes

> 算法笔记 — 距离估算、坐姿评分、亮度等级的原理与局限

## 1. Distance Estimation (M2, implemented)

### 1.1 Model

Distance is estimated from the inverse relationship between the face bounding
box width and the camera-to-face distance:

    d = k / w

where `d` = distance (cm), `w` = face box width (px), and `k` = fitted constant.

### 1.2 Calibration

Three-point calibration collects `(distance, width)` samples at known distances.
`k` is fitted by least squares, minimizing `Σ(dᵢ − k/wᵢ)²`:

    k = Σ(dᵢ / wᵢ) / Σ(1 / wᵢ²)

Each sample is the **median** width over 30 frames, which suppresses detector
jitter and transient false positives.

### 1.3 Operation Flow

1. Run `python main.py --source camera`.
2. Stand at a known distance (30 / 50 / 70 cm recommended), press `c`, enter
   the distance in the terminal, and hold still while 30 frames are collected.
3. Repeat for the other two distances.
4. Press `s` to fit `k` and save to `configs/calibration.json`.
5. The HUD then shows `Distance: <cm> [too_close|normal|too_far]` each frame.

### 1.4 Accuracy and Limitations

- **Not precision ranging**: width depends on head angle, detector accuracy,
  resolution, and individual facial variation (see PROJECT_SPEC §5.1).
- Numerical simulation (true `K=7400`, 8% width noise): fitted `k=7358.3`;
  independent samples at 30/50/70 cm showed mean absolute error
  1.22 / 1.91 / 2.83 cm respectively.
- Real-world error must be measured with independent samples at the camera
  (M2 acceptance), not assumed from the simulation above.

## 2. Posture Scoring (M3, planned)

- Heuristic rules based on face position and size.
- Score formula and threshold rationale.
- Limitations: what it can and cannot detect.

## 3. Brightness Level (M3, planned)

- Frame luminance calculation (mean of grayscale).
- Level boundaries and their meaning.
- Why this is NOT a lux measurement.

## 4. Anomaly State Machine (M3, planned)

- State transitions.
- Duration tracking logic.
- Cooldown mechanism.
