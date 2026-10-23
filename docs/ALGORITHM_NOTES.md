# StudyGuard Algorithm Notes

> 算法笔记 — 距离估算、坐姿评分、亮度等级的原理与局限
>
> **语言约定**：本文件按里程碑逐步追加，M2–M4 的正文以英文为主、真机实测之后补的章节以
> 中文为主，属历史成因，未做回溯翻译。**标题一律统一为「中文 / English」双语式**，与
> `PROJECT_STATUS.md` 的写法对齐。

## 1. 距离估算 / Distance Estimation (M2, implemented)

### 1.1 模型 / Model

Distance is estimated from the inverse relationship between the face bounding
box width and the camera-to-face distance:

    d = k / w

where `d` = distance (cm), `w` = face box width (px), and `k` = fitted constant.

### 1.2 标定 / Calibration

Three-point calibration collects `(distance, width)` samples at known distances.
`k` is fitted by least squares, minimizing `Σ(dᵢ − k/wᵢ)²`:

    k = Σ(dᵢ / wᵢ) / Σ(1 / wᵢ²)

Each sample is the **median** width over 30 frames, which suppresses detector
jitter and transient false positives.

### 1.3 操作流程 / Operation Flow

1. Run `python main.py --source camera`.
2. Stand at a known distance (30 / 50 / 70 cm recommended), press `c`, enter
   the distance in the terminal, and hold still while 30 frames are collected.
3. Repeat for the other two distances.
4. Press `s` to fit `k` and save to `configs/calibration.json`.
5. The HUD then shows `Distance: <cm> [too_close|normal|too_far]` each frame.

### 1.4 精度与局限 / Accuracy and Limitations

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

## 2. 坐姿评分 / Posture Scoring (M3, implemented)

Heuristic score (0.0–1.0) from face position and size relative to the frame:

- `y_ratio = face_center_y / frame_height`（ideal 0.4）
- `w_ratio = face_width / frame_width`（ideal 0.25）
- `score = mean( max(0, 1 - |y_ratio - ideal_y|/tol), max(0, 1 - |w_ratio - ideal_w|/tol) )`，`tol = 0.15`

1.0 = face at ideal position/size；0.0 = far off (edge or tiny)。无脸 → 0.0。
局限：仅靠人脸位置/大小无法可靠识别所有驼背/前倾（PROJECT_SPEC §5.2）。

## 3. 亮度等级 / Brightness Level (M3, implemented)

相对亮度等级 1–5，由帧灰度均值得到：

- 默认阈值 51 / 102 / 153 / 204 → `level = 1 + count(luminance >= threshold)`
- 1 = 最暗，5 = 最亮

非照度（lux）测量：摄像头自动曝光会改变帧亮度（PROJECT_SPEC §5.3）。

## 4. 异常状态机 / Anomaly State Machine (M3, implemented)

`AnomalyTracker` 按命名指标跟踪持续异常，含持续时间阈值与冷却：

- `update(metric, is_anomalous, threshold_sec, cooldown_sec) -> bool`：指标持续异常达到 `threshold_sec` 时恰好返回一次 True。
- 冷却期 `cooldown_sec` 内不重复触发。
- 恢复（指标回到正常范围）后，再次持续异常可重新触发。

M4 的 `reminder.py` 消费触发结果生成提醒事件。默认：坐姿异常阈值 8 s、距离 3 s、冷却 60 s（已迁入 `configs/default.json`）。

## 5. 人工目验发现的局限与 M4 处理 / Limits Found by Manual Inspection (M4)

1. **警告触发体感慢**：持续阈值 5 s / 10 s，且近距离检测闪烁会重置计时。
   M4 已改为距离 3 s、坐姿 8 s，并迁入 `configs/default.json`。
2. **极近距离检测盲区**：脸贴极近（<约 20 cm）时 Haar 检测不到人脸，原无任何提示。
   M4 已增加持续人脸丢失 >10 s 的 `face_lost` 提醒（检测器局限本身不改变）。
3. **静态理想位置误报**：固定 `ideal_y_ratio=0.4` / `ideal_w_ratio=0.25` 与真实摄像头
   仰角、坐位不符，正常坐姿也可能低分。M4 已改为会话自基线（见 §6）。

## 6. 会话坐姿基线 / Session Posture Baseline (M4, implemented)

基线为**显式触发**：HUD 提示 `Sit upright, press b to set posture baseline`，
按 `b` 后 `MetricsCalculator` 采集 `posture.baseline_frames`（默认 30）个有脸帧的
y/w 比率，取中位数作为理想值；完成后 HUD 显示 `baseline ready`。

- 未按 `b` 前：始终使用配置的 `ideal_y_ratio` / `ideal_w_ratio`（0.4 / 0.25）。
- 采集中：HUD 显示 `Baseline: n/30`，此期间仍使用配置理想值。
- `posture.auto_baseline=true`（默认）允许 `b` 键基线；`false` 禁用基线，恒用理想值。
- 优点：避免把启动时俯身操作姿势误当作基线（M4 复验发现的实际问题）。
- **局限**：按 `b` 时的姿势即基线——须在坐直后再按 `b`，否则该姿势会被当作正确姿势。

## 7. 人脸丢失检测 / Face-lost Detection (M4, implemented)

`ReminderManager` 在连续无脸超过 `reminder.face_lost_sec`（默认 10 s）时触发一次
`FACE_LOST` 事件，HUD 显示 `WARNING: face_lost`；人脸恢复后立即清除。
该提醒用于缓解极近距离 Haar 检测盲区（<约 20 cm）导致的「无任何警告」问题。

## 8. 检测参数调参实测 / Detector Parameter Tests (2026-10-23, post O1-A)

O1-A 把 `detection.*` 接入配置后，项目负责人用真实摄像头（教室环境）做了对比实测，
临时配置放在 `/tmp`，**未改动 `configs/default.json` 任何数值**：

| `min_neighbors` | 正脸检出 | 墙上立方体 logo 误检 | 结论 |
|---|---|---|---|
| 5（现行默认） | 稳定 | 偶尔仍被框 | 保留 |
| 7 | **正脸也丢框**（脸正对、占画面约 1/4 时 `Faces: 0`） | 仍偶尔被框 | 不采纳 |
| 20 | 频繁丢框 | — | 仅用于验证配置生效 |

**决定：默认值保持 5。** 5→7 两头都没收益——误检没压住，正脸先丢了。

**为什么调阈值治不了这三个现象**：`haarcascade_frontalface_default.xml` 的假设是
正脸、竖直、光照均匀。实测中「稍微侧脸就丢」「低头（幅度不大）就丢」「刘海遮挡加重丢失」
改的是脸的形状本身，不是候选的置信度；提高 `min_neighbors` 只会让正脸样本也被过滤。
唯一有效的手段是换检测器（P1 的 YuNet ONNX，对俯仰/侧转鲁棒性显著更好），已排入 O2。

## 9. HUD 中文本地化 / HUD Chinese Localization (2026-10-23, O1-B)

`hud.language="zh"` 时用 Pillow + 系统 CJK 字体（首选 Noto Sans CJK，探测见
`hud.find_cjk_font`）在渲染层绘制中文标签；中文仅存在于屏幕渲染层，CSV/JSON 报告与
`DistanceCategory` 枚举值保持英文不变。**中文渲染依赖系统 CJK 字体，缺失时自动回退英文
（cv2.putText），不抛异常、不画豆腐块。**

## 10. 跨方向告警静音与整句横幅死路径 / Cross-direction Silencing & Dead Banner Path (2026-10-23, O1-C)

三条缺陷 D1 / D2 / D3 都是 O1-B 真机目验时撞出来的，其中 D1、D3 已在 v0.2.1 修复，
D2 未修（并入 O2-B）。这一节记下现象、根因和证据分别是什么，以及为什么 91 条用例全绿却漏掉了它。

### 10.1 现象 / Symptom

负责人真实摄像头（教室环境）下：先弹一次「离太远」告警，随后把脸贴近并保持 20 秒以上，
**距离告警再也不出现**，同一区间反而弹了坐姿告警。CSV 里那 26 秒一行 `distance_warning` 都没有。

### 10.2 根因：两处叠加，缺一不可 / Root Cause

| 位置 | 问题 |
|---|---|
| `reminder.py`（修复前 160–166 行） | `too_close` 与 `too_far` 合成同一个 tracker 键 `"distance"`，共用 60 s 冷却 |
| `metrics.py`（277–280 行，至今未改） | 恢复分支只清 `started_at` / `triggered`，**不清 `last_triggered_at`**；而 285–288 行的冷却判断读的正是它 |

单看两处都自洽：`AnomalyTracker` 本来就是「按命名指标」跟踪，冷却跨恢复期保留也是有意的
（否则用户反复抖动可以无限刷告警）。**错的是键的粒度**——两个物理方向共用一份冷却，
于是一次「离太远」会吃掉之后 60 秒内所有「离太近」。修复因此落在 `reminder.py`（拆
`distance_close` / `distance_far` 两键，逐帧两键都 `update()`，非当前方向显式传
`is_anomalous=False` 复位），`metrics.py` 一行未动。

**为什么 91 条用例全绿没抓到**：没有任何用例覆盖「先 A 方向触发、再转 B 方向持续」的
**跨方向状态序列**；两个方向各自都有用例、各自都通过。`TOTAL 83%` 量的是行覆盖，
不是状态机转移——这是「测试通过 ≠ 行为正确」在本项目里最现成的一个例子。

### 10.3 证据链：逻辑层与真机层不可混为一谈 / Evidence Chain

时间均为**相对会话起点**的秒数（CSV `timestamp` 列是单调时钟原值，减起点即得）。

1. **原始故障实证** `logs/session_20261023_205533.csv`：
   `+22.42 s` too_far(104.44 cm) 触发 → `+42.8 ~ +68.2 s` 连续 26 秒 too_close
   （26.7–30.2 cm，脸宽 380–430 px，检测很稳）**零告警**；期间 `+60.03 s` 反倒触发了
   `posture_warning`。下一次 `distance_warning` 直到 `+262.32 s` 才出现。
2. **对照实验** `/tmp/banner_check.json`（只把 `cooldown_sec` 设为 0，另把
   `too_close_cm` 放宽到 200 以便正常坐姿就能触发）→ `logs/session_20261023_211430.csv`
   在 `+9.09 / +21.26 / +32.56 s` 连出三条 `distance_warning`。**冷却是唯一压制因素**，
   阈值与状态机都没问题。
   （注意：这份日志里「67.98 cm 却标 too_close」是**对照组故意放宽阈值**造成的，不是测距 bug。）
3. **逻辑层复现**（注入时钟、25 fps 时序回放，不依赖摄像头）：老代码在 too_far 触发后
   连续 26 秒 too_close → **0 条**；新代码同序列 → **1 条**；同方向 20 秒内恢复再持续 →
   **0 条**（冷却仍生效）；冷却到期 → **1 条**。
4. **修复后的真机证据** `logs/session_20261023_214550.csv`：`+14.25 s` too_close(34.92 cm)
   触发 → `+27.51 s` face_lost → `+37.65 s` too_far(94.17 cm) **又触发**。两次相隔
   **23.4 秒**、落在同一个 60 秒冷却窗内，中间还夹了一次丢脸。旧实现下第二条必被静音。
5. **未覆盖的缺口（如实记下）**：默认 `too_close_cm=30.0` 下的 far→close 路径
   **真机始终没能覆盖**——把脸贴到镜头前最低也只能读到 31 cm（见 10.4），分类器根本产不出
   too_close。第 4 条是把阈值临时抬到 35.0（一次性 `/tmp/d1_check.json`，`cooldown_sec`
   仍为 60，未改仓库任何数值）跑出来的，且方向是 close→far。far→close 的等价性由第 3 条
   的注入时钟回放承担，不由真机承担。
6. **方法论留档**：跨方向回归锁
   `tests/test_reminder.py::test_distance_warning_cross_direction_not_silenced` 的
   「改前失败」是真实的（`assert len(close_events) == 1` → `0 == 1`），但**无法从最终提交树
   复现**——测试文件模块级 `import select_banner`，在旧代码上会先 ImportError。
   红跑只存在于「先写测试、后加函数」的中间态。要复现得把 HEAD 源码与剥离新符号导入的用例
   单独组合运行。

### 10.4 D2：`too_close_cm=30.0` 贴着测距噪声带（未修）/ Threshold Inside the Noise Band

同一坐姿下 Haar 脸宽实测在 143–430 px 之间摆动，对应 26.7–80.9 cm；阈值 30.0 正落在噪声带
中段，于是「真实 28 cm 到底告不告警」取决于当帧检测器把框画多宽。
`logs/session_20261023_210932.csv` 里同一姿势读数 29.92 / 32.00 / 39.34 / 62.44 / 73.64 /
80.90 乱跳即为此证。负责人真机最低只能读到 31 cm，也是同一件事的另一面。

**决定：现在不改这个数字。** 换 YuNet 之后脸宽定义本身会变（见 §8 末与 O2），
阈值重新定标并入 O2-B 的对比实测表一起做。

### 10.5 D3：整句横幅是事实死路径（已修）/ Dead Whole-sentence Banner

修复前 `main.py:212-219` 先取 `events[-1].message`（整句）作 banner，紧接着只要
`active_warnings()` 非空就用 `"WARNING: " + labels` 覆盖；而 `triggered` 在异常持续期间
恒为 True（`metrics.py:282-283`），所以 `BANNER_HOLD_SEC = 3.0` 的整句**在持续异常期间
永远显示不出来**，O1-B 做的 `_WARNING_MESSAGES_ZH` 整句映射基本不可达，横幅也不告诉用户
该往前还是往后靠。

修复是把选择规则抽成纯函数 `reminder.select_banner(now, events, active_labels, hold_sec)`，
优先级「hold 内整句 → 超时且仍有活动告警用标签串 → 空串」，`main.py` 保留最近一次事件批并
调用它，`BANNER_HOLD_SEC` 仍为 3.0。抽成纯函数的唯一理由是这条路径没有显示器就测不了。

**两条已接受的设计后果**（按规则实现，不是缺陷）：① 整句优先，因此眼保健操（20 min）/
久坐（30 min）提醒会把活动中的告警横幅顶掉 3 秒；② `hud.language="en"` 时 `cv2.putText`
画不出 U+2014，`Too close — move back` 的破折号显示为小方框（不崩溃，仅外观）。

### 10.6 回指 §4 / Back-reference to §4

§4 写的「恢复（指标回到正常范围）后，再次持续异常可重新触发」，**按单个命名键看成立**，
但 D1 说明这句话有个隐含前提：**「恢复」的定义取决于键的粒度**。把两个物理方向塞进一个键，
「恢复」就只覆盖其中一侧，这句承诺在另一侧失效。今后新增指标时，键的粒度应当按
「用户会收到哪一条不同的提示」来划分，而不是按数据结构的枚举来划分。

顺带登记 **D4**（未修，并入 O2-B）：距离栏显示 `[太近] / [太远]`（`hud.py:40-41`，O1-B 定），
横幅显示 `距离过近 / 距离过远`（O1-C 新加），同一屏两套措辞。

---

> 本节文字由 Qoder 依据上述取证记录代笔（负责人 2026-10-23 授权），事实部分经独立复核；
> 结论与取舍仍由负责人判定。

