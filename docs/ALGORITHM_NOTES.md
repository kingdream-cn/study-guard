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

### 1.5 实测标定记录 / Real-world Calibration Record

**k = 11488.3**（2026-10-20 实测，两轮三点标定）：

| 距离 (cm) | 第 1 轮脸宽 (px) | 第 2 轮脸宽 (px) | 两轮差异 |
|-----------|------------------|------------------|----------|
| 30 | 318 | 347 | 约 9% |
| 50 | 234.5 | 231 | 约 1.5% |
| 70 | 168.5 | 169 | 约 0.3% |

**独立样本误差**（真值方法：数据线直线，屏幕顶边 → 鼻尖，不确定度 ±2-3 cm）：

| 真值 (cm) | HUD 显示 (cm) | 相对误差 |
|-----------|---------------|----------|
| 40 | 44–45 | +10-12% |
| 60 | 61–62 | +2-3% |

**观察**：

- 30 cm 两轮脸宽相差约 9%（318 vs 347 px），而 50/70 cm 稳定（约 1.5% / 约 0.3%），说明近距离样本对姿势/角度最敏感。
- 标定时应保持姿势一致；后续复测可增加近距离点的轮数。

**结论**：系统误差随距离收敛（近距约 +10%，远距约 +2-3%），与「距离估算不等于精密测距」的声明（PROJECT_SPEC §5.1）一致。

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
