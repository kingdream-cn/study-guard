# StudyGuard 项目进度 / Project Status

## 当前阶段 / Current Phase

**M4: 提醒与日志 / Reminders & Logging**

## 当前状态 / Current Status

**IN_PROGRESS**（实现完成，自动化测试 54/54 通过；待项目负责人验收）

## 已完成 / Completed

- [x] 项目目录建立 / Project directory created
- [x] Python 环境确认 / Python environment verified (3.12.3)
- [x] 依赖检查 / Dependencies verified (OpenCV 4.14.0, NumPy 2.5.4, matplotlib 3.11.2, Pillow 13.0.0, pytest 9.1.1)
- [x] 摄像头确认可用 / Camera confirmed available (USB2.0 HD UVC WebCam, /dev/video0)
- [x] 虚拟环境创建 / Virtual environment created (.venv)
- [x] Git 仓库初始化 / Git repository initialized
- [x] 项目规格文档 / PROJECT_SPEC.md
- [x] 项目主控提示词 / PROJECT_RULES.md
- [x] 架构设计文档 / ARCHITECTURE.md
- [x] 接口规范文档 / INTERFACE_SPEC.md
- [x] 编码规范文档 / CODING_STANDARDS.md
- [x] 测试方案 / TEST_PLAN.md
- [x] 决策记录 / DECISIONS.md
- [x] 项目路线图 / ROADMAP.md
- [x] DSH 操作指南 / DSH_GUIDE.md
- [x] GitHub 远程仓库创建 / GitHub remote repository created

## M1 已完成 / M1 Completed

- [x] `capture.py` — 统一视频输入（文件 + 摄像头）
- [x] `detector.py` — Haar 人脸检测 + `FaceBox`
- [x] `hud.py` — 基础 HUD（FPS、人脸数量、人脸框）
- [x] `main.py` — 主循环（打开 → 检测 → HUD → 显示 → 退出）
- [x] `tests/test_capture.py`、`tests/test_detector.py`（10 用例全部通过）

## 验收标准 / Acceptance Criteria (M1)

- [x] 自动化测试 10/10 通过（项目负责人独立复跑确认）
- [x] 代码审查通过：capture/detector/hud/main 符合 INTERFACE_SPEC 与 CODING_STANDARDS
- [x] 无窗验证：`/tmp/test_face.mp4` 共 232 帧，198 帧（85%）检出人脸，人脸框宽度 46–280 px
- [x] 人工验收：视频模式与摄像头模式窗口实时显示绿色人脸框，HUD 显示 `FPS: 27.8` 与 `Faces: 1`，`q` 键正常退出

## M2 已完成 / M2 Completed

- [x] `calibrator.py` — 三点标定、最小二乘拟合 k、保存/加载 JSON
- [x] `metrics.py` — `DistanceCategory` + `DistanceEstimator`（距离估算与分类）
- [x] `hud.py` — 增加距离值与距离分类显示
- [x] `main.py` — 集成标定流程（`c` 采集、`s` 保存、启动加载）
- [x] `tests/test_calibrator.py`（11 用例，全部通过）

## 验收标准 / Acceptance Criteria (M2)

- [x] 自动化测试 21/21 通过（项目负责人独立复跑确认）
- [x] 代码审查通过：calibrator.py 实现批准的选项 A 公式，save/load 校验严密
- [x] 真实标定完成：`configs/calibration.json` k=11488.3，30/50/70 cm 两轮三点样本（脸宽 318/347、234.5/231、168.5/169 px）
- [x] 独立样本检查（数据线直线：屏幕顶边→鼻尖，±2-3 cm）：40 cm → HUD 44-45（+10-12%）；60 cm → HUD 61-62（+2-3%），在声明局限内
- [x] ADR-004 公式修正已记录在案

## M3 已完成 / M3 Completed

- [x] `metrics.py` — `MetricsCalculator` + `FrameMetrics` + `AnomalyTracker`（对齐 INTERFACE_SPEC §1.5，距离逻辑复用未重写）
- [x] 坐姿评分：人脸位置/大小启发式（0.0–1.0）
- [x] 亮度等级：帧灰度均值（1–5）
- [x] 异常持续时间跟踪 + 冷却机制（`AnomalyTracker`，M4 reminder.py 消费其输出）
- [x] `hud.py` — 显示坐姿分数、亮度等级、异常横幅
- [x] `main.py` — 集成 MetricsCalculator + AnomalyTracker
- [x] `docs/ARCHITECTURE.md` — 同步 metrics/reminder 模块职责
- [x] `tests/test_metrics.py`（13 用例，全部通过）

## 验收标准 / Acceptance Criteria (M3)

- [x] 自动化测试 34/34 通过（项目负责人独立复跑确认）
- [x] 代码审查通过：FrameMetrics 符合 §1.5；AnomalyTracker 持续+冷却语义正确
- [x] 人工目验：Posture/Light 响应正确；凑近触发距离警告；坐姿警告可触发

## M4 已完成 / M4 Completed

- [x] `config.py` + `configs/default.json` — 完整 JSON 配置、深合并默认值、范围校验、`ConfigError`
- [x] `reminder.py` — 20-20-20、久坐计时、距离/坐姿异常提醒、`FACE_LOST`、可注入时钟、暂停/恢复
- [x] `logger.py` — 会话 CSV 按配置间隔写入，列格式符合 INTERFACE_SPEC §3
- [x] `metrics.py` — 坐姿会话自基线（`posture.auto_baseline`，默认 30 帧）
- [x] `main.py` — 集成 config/reminder/logger；`Space` 暂停/恢复，提醒横幅
- [x] `tests/test_config.py`（7）、`tests/test_reminder.py`（8）、`tests/test_logger.py`（2）、`tests/test_metrics.py` 新增 3 个基线用例
- [x] `docs/ALGORITHM_NOTES.md` — 自动基线局限、face_lost、阈值更新

## 当前任务 / Current Task

M4 验收：等待项目负责人复跑测试与摄像头目验（提醒/横幅/CSV）。

## 验收标准 / Acceptance Criteria (M0)

- [x] Python 版本符合项目要求 / Python version meets requirements (3.12)
- [x] OpenCV 可以正常导入 / OpenCV imports successfully
- [x] 摄像头设备已确认 / Camera device confirmed
- [x] 项目文档齐全 / All project documentation complete
- [x] Git 仓库已初始化并关联远程 / Git repo initialized and linked to remote

## 已知问题 / Known Issues

- DSH 执行沙箱无法访问项目负责人的摄像头 `/dev/video0`；M4 的单元测试可完全离屏运行，真实摄像头目验（提醒/横幅/日志）需在桌面执行。
- ADR-004 原始拟合公式 `k = Σ(wᵢ×dᵢ)/Σ(wᵢ²)` 与模型 `d = k/w` 自相矛盾，已按批准修正为 `k = Σ(dᵢ/wᵢ)/Σ(1/wᵢ²)`（见 `docs/DECISIONS.md`、`docs/ALGORITHM_NOTES.md`）。
- 坐姿评分与亮度等级为启发式/相对指标，非精密测量（PROJECT_SPEC §5.2 / §5.3）。
- M3 目验发现 1（已处理）：警告体感慢/近距闪烁重置 → M4 阈值改为距离 3 s、坐姿 8 s，并迁入 config。
- M3 目验发现 2（已缓解）：极近（<约 20 cm）Haar 盲区 → M4 增加持续人脸丢失 >10 s 的 `face_lost` 提醒；检测器局限本身未改变。
- M3 目验发现 3（已处理）：静态理想位置误报 → M4 改为会话自基线；局限是「开局姿势即基线」，开局应保持正确坐姿。
- `BRIGHTNESS_WARNING` 类型已定义，但本次未实现亮度异常提醒（未收到明确的亮度触发阈值要求）；亮度等级仅在 HUD 显示。
- 在 ROS 2 环境下运行 pytest 需加 `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1` 前缀，详见 `CONTRIBUTING.md`。

## 最近一次测试 / Latest Test

M4（2026-10-20）：`PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest tests/ -v` → **54 passed**（calibrator 11 + capture 6 + config 7 + detector 4 + logger 2 + metrics 16 + reminder 8）。端到端冒烟：合成视频运行 `main.py --source file` exit 0，生成 `logs/session_*.csv`（表头符合 §3，按 1 s 间隔只写 1 行而非逐帧）。

## 下一项任务 / Next Task

M4 验收（复跑测试 + 摄像头目验：提醒/横幅/CSV）；通过后进入 **M5: 报告生成**。

## 变更记录 / Change Log

| 日期 / Date | 变更 / Change |
|------------|--------------|
| 2026-10-19 | 项目初始化完成 / Project initialization completed |
| 2026-10-20 | M0 环境复核：OpenCV 固定为 4.x，Haar 可用性验证通过 / M0 env recheck |
| 2026-10-20 | M1 视觉基础实现：capture/detector/hud/main + 测试，10 用例通过 / M1 implemented |
| 2026-10-20 | M1 验收通过，状态升级为 VERIFIED / M1 verified |
| 2026-10-20 | M2 距离标定与估算实现：calibrator/metrics/hud/main + 测试，21 用例通过 / M2 implemented |
| 2026-10-20 | M2 验收通过，状态升级为 VERIFIED（粗验收）/ M2 verified |
| 2026-10-20 | M3 行为指标与异常状态机实现：metrics/hud/main + 测试，34 用例通过 / M3 implemented |
| 2026-10-20 | M3 验收通过 VERIFIED；3 项目验缺陷经批准并入 M4（阈值 3s/8s、自动基线、face_lost）/ M3 verified + M4 adjustments approved |
| 2026-10-20 | M4 提醒与日志实现：config/reminder/logger + 自动基线/face_lost，54 用例通过 / M4 implemented |
