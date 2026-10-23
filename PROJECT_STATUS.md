# StudyGuard 项目进度 / Project Status

## 当前阶段 / Current Phase

**O1-C: D1/D3 缺陷修复（v0.2.1 准备中）/ Post-release defect fixes**

## 当前状态 / Current Status

**O1-C IMPLEMENTED**（自动化测试 108/108，回归锁先红后绿；待负责人真机目验后打标签 `v0.2.1`）
M0–M7、O1-A、O1-B 均 **VERIFIED**；`v0.1.0` / `v0.2.0` 已发布（v0.1.0 的 GitHub Actions 首轮运行 success，2026-10-21 由项目负责人侧查询确认）。

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
- [x] `metrics.py` — 坐姿会话自基线（显式 `b` 键触发，默认 30 帧；未标定前用配置理想值）
- [x] `main.py` — 集成 config/reminder/logger；`Space` 暂停/恢复、`b` 坐姿基线、提醒横幅
- [x] `tests/test_config.py`（8）、`tests/test_reminder.py`（8）、`tests/test_logger.py`（3）、`tests/test_metrics.py` 基线用例（4）
- [x] `docs/ALGORITHM_NOTES.md` — 显式基线局限、face_lost、阈值更新

### M4 复验修复 / Re-verification Fixes

- [x] 缺陷 1（实现 bug）：`SessionLogger.log` 仅取当帧 reminders，非写行帧事件被丢弃。已改为内部缓冲自上次写行以来的事件，写行时并入 `reminder_triggered` 后清空；新增 `test_csv_log_buffers_events_from_non_write_frames`。
- [x] 缺陷 2（设计缺陷）：坐姿基线自动采集启动时俯身姿势。已改为显式 `b` 键触发（HUD 提示 `Sit upright, press b to set posture baseline`，完成后 `baseline ready`）；未按 `b` 时恒用配置理想值；`auto_baseline` 语义为 true=允许 b 键基线、false=禁用。新增 b 键基线与未标定回退用例；`INTERFACE_SPEC §5`、`ALGORITHM_NOTES §6` 已同步。

## 验收标准 / Acceptance Criteria (M4)

- [x] 自动化测试 57/57 通过（项目负责人独立复跑确认）
- [x] 代码审查通过：logger 先缓冲事件再判断写行间隔、写行后清空；`begin_baseline` 显式 `b` 键语义正确（重触发回退配置理想值、`auto_baseline=false` 忽略 `b`）
- [x] 复验实证：按 `b` 后 Posture 升至 0.9+，正常坐姿不再误报；距离警告触发并写入 CSV（`...,27.35,too_close,0.179,3,distance_warning`），缺陷 1 在真实数据下生效
- [x] 两项缺陷修复提交 `6dd50bc` 已审查

## M5 已完成 / M5 Completed

- [x] `report.py` — 会话摘要：JSON（`reports/session_summary_*.json`）+ 可选 PNG 图表（matplotlib，`report.generate_charts` 控制）
- [x] JSON 字段：会话时长、有效用眼时间、人脸出现率、距离统计（mean/min/max/median + 分类占比）、坐姿统计、亮度分布、按类型提醒次数、标定 k 值
- [x] 无有效数据 → `insufficient_data: true`、统计字段 null、图表跳过；损坏 CSV 跳过坏行并 warning，全部坏行按数据不足处理
- [x] `main.py` — 退出（q/Esc/EOF/KeyboardInterrupt）自动用本次 CSV 生成报告
- [x] `tests/test_report.py`（7 用例：正常/空日志/全人脸丢失/损坏日志/全坏行/图表开关/标定 k）

## 验收标准 / Acceptance Criteria (M5)

- [x] 自动化测试 64/64 通过（项目负责人独立复跑确认）
- [x] 代码审查通过：matplotlib Agg 后端、图表渲染失败不影响 JSON、坏行跳过不崩溃、insufficient_data 路径统计字段全 null
- [x] 目验会话 A（80 s 真实摄像头）：JSON 字段齐全（duration 80.62 s、effective_study_time 54.0 s、face_detection_rate 0.675、calibration_k 11488.34、距离统计+分类占比、坐姿统计、亮度分布、提醒计数），同名 PNG 已生成
- [x] 目验会话 B（无脸）：`insufficient_data: true`、统计全 null、不生成 PNG（实证 `reports/session_summary_20261021_205947.json`）

## M6 已完成 / M6 Completed

- [x] `tests/test_stability.py`（8 用例）：零长度视频、损坏视频、全程无人脸（子进程 headless）、人脸快速出现/消失、KeyboardInterrupt(SIGINT)、配置中途删除、日志目录不可写、4K 帧
- [x] `main.py` 新增 `--headless`（无窗口运行）与 `--config`（自定义配置）；日志目录不可写时启动报错并降级为无日志
- [x] 覆盖率报告已生成（72 用例；7 个核心模块均 ≥85%）

## 验收标准 / Acceptance Criteria (M6)

- [x] 自动化测试 72/72 通过（项目负责人独立复跑确认）
- [x] 覆盖率复现与汇报一致：capture 85 / detector 97 / calibrator 89 / metrics 98 / reminder 96 / logger 98 / report 88，TOTAL 83
- [x] TEST_PLAN M6 八个用例全部实现于 `tests/test_stability.py` 并通过
- [x] `--headless` 模式为 CI 与子进程测试提供基础

## M7 已完成 / M7 Completed

- [x] `.github/workflows/tests.yml` — push/PR 触发，ubuntu-latest + Python 3.12，安装 requirements-dev.txt 后运行 pytest
- [x] `README.md` / `README_zh.md` — Actions badge、实测精度（40 cm→+10–12%、60 cm→+2–3%，数据线真值 ±2–3 cm）、测试命令、算法局限与隐私声明；修正克隆 URL；补 `b` 快捷键
- [x] `docs/CHANGELOG.md` — v0.1.0 条目（M1–M6 全部功能）
- [x] 干净环境复现：全新 venv + `pip install -r requirements-dev.txt` → **72 passed**（默认 PyPI 大文件下载多次中断，改用清华镜像完成安装）
- [x] 仓库核查：`logs/`、`reports/`、`configs/calibration.json` 与任何真实人脸素材均未入库（`.gitignore` 生效；仅 `.gitkeep` 被跟踪）
- [x] 发布提交与标签 `v0.1.0` 已推送
- [x] GitHub Actions 首轮运行确认：success（run #2，head e4623be，https://github.com/kingdream-cn/study-guard/actions/runs/39612818997）

## O1-A **VERIFIED** / 检测参数接入配置（v0.1.0 之后优化项，2026-10-23）

- [x] `detector.py` — `FaceDetector.__init__` 新增 `scale_factor` / `min_neighbors` / `min_face_size`（默认 1.1 / 5 / 30，引用现有常量，无参构造行为与 v0.1.0 完全一致）；`detect()` 改用实例参数
- [x] `main.py` — 用 `config.get("detection.scale_factor"/"min_neighbors"/"min_face_size")` 构造 `FaceDetector`
- [x] `config.py` — `scale_factor` 校验 `[1.01, 2.0]`、`min_face_size >= 1`，保留 `min_neighbors >= 0`
- [x] `tests/test_detector.py`（+3：默认值 / 自定义参数 / 参数转发）、`tests/test_config.py`（+4：scale_factor 越界×2、min_face_size 越界×2）
- [x] `docs/INTERFACE_SPEC.md §1.3`、`docs/CHANGELOG.md` 同步

## 验收标准 / Acceptance Criteria (O1-A)

- [x] 自动化测试 79/79 通过，无回归
- [x] `FaceDetector()` 无参构造仍可用，参数 = 1.1 / 5 / 30
- [x] 配置 `min_neighbors=20` 时 main.py 实际构造使用 20，改回 5 后恢复（端到端 spy 验证）
- [x] `scale_factor` / `min_face_size` 越界启动即报 ConfigError（exit 1）
- [x] INTERFACE_SPEC §1.3 与代码签名一致

### Qoder 独立复核（不采信执行方汇报）/ Independent Audit

- `.venv` + `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest tests/ -q` → **79 passed in 2.48s**（本地独立执行）
- `FaceDetector()` 直读实例属性 → `1.1 5 30`；`inspect.signature` 确认 `cascade_path` 仍为首位参数，位置调用未破坏
- 实跑坏配置：`--config` 注入 `scale_factor=2.5` / `min_face_size=0` → `exit=1` 且错误文本逐字匹配
- 桩掉 `VideoCapture` 跑通 `main.main()`，抓到构造实参 `{'scale_factor': 1.3, 'min_neighbors': 20, 'min_face_size': 45}`，与临时配置一致 → **接线在真实运行路径生效**
- 越界检查：`configs/default.json`、`hud.py`、`logger.py`、`metrics.py`、`report.py`、`calibrator.py`、`reminder.py` 全部零改动
- 负责人真实摄像头目验：`min_neighbors=7` 时正脸丢框（`Faces: 0`）且 logo 仍偶尔误检 → **默认值保持 5，不调参**，实测记录见 `docs/ALGORITHM_NOTES.md` §8

## O1-B **VERIFIED** / HUD 中文本地化 + 警告横幅正文汉化（v0.1.0 之后优化项，2026-10-23）

- [x] `hud.py` — 新增 Pillow CJK 渲染路径 + 独立字体探测 `find_cjk_font()`；找不到 CJK 字体自动回退 `cv2.putText` 英文（不抛异常、不画豆腐块）；`draw` 签名与返回值类型不变
- [x] `HUDOverlay.__init__` 新增 `language`（默认 `"en"`）；`main.py` 用 `config.get("hud.language")` 传入
- [x] 渲染层中文映射表：标签（FPS/Faces/Distance/Posture/Light）、距离档位（unknown/too_close/too_far/normal）、warning 前缀 `WARNING: `→`警告：`、baseline_hint；CSV/JSON 与 `DistanceCategory` 枚举值保持英文
- [x] 横幅正文汉化（O1-B 追加，负责人 2026-10-23 批准）：固定提醒整句精确匹配 + `WARNING: <标签>` 动态标签逐个翻译（`、` 连接），未命中原样返回；`reminder.py`/`logger.py`/`metrics.py` 零改动
- [x] `config.py` + `configs/default.json` 新增 `hud.language="zh"`；校验 `language ∈ {zh, en}`，非法抛 `ConfigError`
- [x] `tests/test_hud.py`（新建，12 用例：zh 同形状 / 无字体回退英文 / 非法 language ConfigError / 默认 en / 4 整句映射 / 单·多标签动态组合 / 未知原样 / en 不翻译）
- [x] `docs/INTERFACE_SPEC.md §1.9 §2`、`docs/ALGORITHM_NOTES.md §9`、`docs/CHANGELOG.md` 同步

## 验收标准 / Acceptance Criteria (O1-B)

- [x] 自动化测试 **91/91** 通过（83 原有 + 8 新增横幅用例），无回归
- [x] `language="zh"` 摄像头画面 HUD 显示中文标签与中文横幅且无乱码方块 —— **负责人 2026-10-23 真机目验通过**：`帧率/人脸/距离/坐姿/亮度` 全中文、档位显示 `[过近]`、`坐直，按 b 设置坐姿基线` 与 `基线就绪` 中文、动态标签横幅显示 `警告：距离异常`，全程无 □ 豆腐块
- [x] 5 类真实横幅消息在 `language="zh"` 下全部译成中文（整句 4 条 + `WARNING: face_lost` 动态标签），未知字符串原样返回且不崩溃
- [x] `language="en"` 输出与 v0.1.0 逐行一致且不经过任何翻译（en 路径为原 `cv2.putText` 代码逐字保留；spy 测试证明 `_zh_warning` 未被调用）
- [x] CSV 表头与 reminder/枚举字符串未变（`logger.py`/`metrics.py`/`reminder.py` 零改动，git diff 确认）
- [x] 无 CJK 字体时回退英文（monkeypatch 测试 `np.testing.assert_array_equal(zh, en)` 证明）

## O1-C **IMPLEMENTED（待负责人真机验收）** / D1 跨方向告警静音 + D3 整句横幅死路径（v0.2.1，2026-10-23）

- [x] `reminder.py` — 距离异常拆为 `distance_close` / `distance_far` 两个 tracker 键，均沿用现有 `distance_anomaly_threshold_sec` 与 `cooldown_sec`；同一帧两键都调用 `update()`，非当前方向显式传 `is_anomalous=False` 复位；任一触发只发一条 `DISTANCE_WARNING`（`metrics.py` 零改动）
- [x] 方向化文案 — 距离告警 message 拆为 `"Too close — move back"` / `"Too far — move closer"`；`ReminderType` value 与 CSV 写入值不变
- [x] `reminder.py` — 新增纯函数 `select_banner(now, events, active_labels, hold_sec)`；`main.py` 改为调用，`BANNER_HOLD_SEC = 3.0` 不变
- [x] `reminder.py` — `active_warnings()` 返回 `distance_too_close` / `distance_too_far`（posture 保持 `posture`）
- [x] `hud.py` — `_WARNING_LABELS_ZH` 增加两条方向标签、`_WARNING_MESSAGES_ZH` 增加两条整句；保留旧 `distance` / `Adjust viewing distance` 映射以兼容旧日志与 O1-B 用例
- [x] 测试 — **91 → 108**（+17：跨方向回归锁、方向 message、同向 60 s 冷却、方向标签、枚举值逐字节锁、5 个 `select_banner` 单测、HUD 方向映射 5 个参数化用例 + 整句→标签端到端、CSV 表头/行字节锁）
- [x] 回归锁先红后绿：修改前 `test_distance_warning_cross_direction_not_silenced` 失败（`assert len(close_events) == 1` → `0 == 1`）；修改后通过
- [x] `docs/INTERFACE_SPEC.md §1.6 §1.9`、`docs/CHANGELOG.md [0.2.1]` 同步
- [x] 边界确认：`configs/default.json`、`logger.py`、`metrics.py`、`detector.py`、`calibrator.py`、`report.py`、`config.py`、`docs/ALGORITHM_NOTES.md` 零改动（`git diff` 确认）

## 验收标准 / Acceptance Criteria (O1-C)

- [x] 自动化测试 108/108 通过，无回归（91 原有 + 17 新增，无删除、无放宽断言）
- [x] 跨方向回归锁在修改前失败、修改后通过（两次运行输出已记录）
- [x] 同方向 60 s 冷却未变（触发后 60 s 内恢复再持续不重复；冷却结束后才再次触发）
- [x] 逻辑层验证：持续 too_close 时前 3 s 返回整句、3 s 后返回 `WARNING: distance_too_close`，中文分别为 `距离过近，请后退` / `警告：距离过近`
- [x] CSV 表头、列顺序、`ReminderType` value 逐字节锁死（新增字节级断言）
- [x] `configs/default.json` 零改动
- [ ] 负责人真机目验：摄像头下前 3 秒整句、3 秒后方向标签，中文无豆腐块（DSH 沙箱无 `/dev/video0`，**未验证**）
- [ ] 负责人确认后打标签 `v0.2.1` 并推送（执行方不自动打标签/上传）

## 发布记录 / Release

- Tag: `v0.1.0`
- 内容：M1–M6 全部 P0 功能（视觉基础、距离标定、行为指标、提醒与日志、报告生成、稳定性）
- 演示素材：未包含任何真实人脸截图/视频（v0.1.0 省略截图）
- Tag: `v0.2.0`（O1-A 检测参数接入配置 + O1-B HUD 中文本地化）
- Tag: `v0.2.1` — 待负责人验收后创建（O1-C：D1 + D3）

## 当前任务 / Current Task

M0–M7 全部 VERIFIED，v0.1.0 / v0.2.0 已发布，项目 MVP 闭环（2026-10-21）。
**O1-A（检测参数接入配置）VERIFIED**（2026-10-23，Qoder 独立复核 + 负责人真实摄像头目验），不改变任何默认行为。
**O1-B（HUD 中文本地化 + 警告横幅正文汉化）VERIFIED**（2026-10-23，自动化测试 91/91 通过 + 负责人真机目验 6 项全过）。
**O1-C（D1 跨方向告警静音 + D3 整句横幅死路径）IMPLEMENTED**（2026-10-23，自动化测试 108/108；回归锁先红后绿；待负责人真机目验后打标签 `v0.2.1`）。
目验过程中发现三项缺陷 **D1 / D2 / D3**（见「已知问题」），D1、D3 已在 O1-C 修复（待验收），D2 并入 O2-B 实测表定标。
O1-C 验收并发布 `v0.2.1` 后进 **O2 = YuNet 检测器替换**（负责人 2026-10-23 批准排期）：
用于根治 Haar 的姿态局限，需新增 ONNX 模型文件与下载，届时单独确认来源与许可。
遗留事项：找人辅助重标定补精确误差表（负责人推迟）；`min_neighbors` 调参已实测否决，见 `docs/ALGORITHM_NOTES.md` §8。

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
- M3 目验发现 3（已处理）：静态理想位置误报 → M4 改为会话自基线；复验后调整为显式 `b` 键触发，未按 `b` 时使用配置理想值。
- M4 复验缺陷 1（已修复）：CSV `reminder_triggered` 在非写行帧丢失 → 已缓冲并并入下一次写行。
- M4 复验缺陷 2（已修复）：自动基线捕获启动俯身姿势导致正常坐姿误报 → 已改为 `b` 键显式触发。
- **Haar 检测器姿态局限（未解决，排入 O2）**：轻微侧脸、小幅低头、刘海遮挡即丢框；背景对称图案（墙上立方体 logo）仍会误检。2026-10-23 实测 `min_neighbors=7` 使正脸也丢框且未消除误检，故不调参；根治需换 YuNet ONNX 检测器。详见 `docs/ALGORITHM_NOTES.md` §8。
- **D1 跨方向告警静音（已修复，O1-C，待真机确认）**：原 `reminder.py:160-166` 把 `too_close` 与 `too_far` 合并为同一 metric 键 `"distance"` 共用 60 s 冷却，而 `metrics.py:285-288` 的冷却判断读 `last_triggered_at`，异常恢复分支（277-280 行）不清零该字段。后果是一次"离太远"告警会把之后 60 s 内的"离太近"告警全部压掉。实证：`logs/session_20261023_205533.csv` 22.4 s 因 too_far(104 cm) 触发 `distance_warning`，随后 42.8–68.2 s 连续 26 s 的 too_close(26.7–30.2 cm) **零告警**；对照组 `/tmp/banner_check.json`（`cooldown_sec=0`）下 2 s 内即弹出横幅。**修复**：`reminder.py` 拆为 `distance_close` / `distance_far` 两键，逐帧两键都 `update()`、非当前方向传 `is_anomalous=False` 复位，同一帧至多一条 `DISTANCE_WARNING`，`metrics.py` 未改动。回归锁 `test_distance_warning_cross_direction_not_silenced`：修改前 `assert len(close_events) == 1` → `0 == 1` 失败，修改后通过；同向 60 s 冷却由 `test_distance_warning_same_direction_cooldown_still_holds` 锁住。
- **D2 `too_close_cm=30.0` 贴着测距噪声带（新发现，暂不改数值）**：同一坐姿下 Haar 脸宽实测在 143–430 px 摆动（对应 26.7–80.9 cm），阈值 30.0 正落在该噪声带中段，导致"真实 28 cm 是否告警"取决于当帧检测器框多宽。实证：`session_20261023_205533.csv` 42.8–68.2 s 脸宽 380–430 px ↔ 距离 26.7–30.2 cm；`session_20261023_210932.csv` 同姿势读数 29.92/32.00/39.34/62.44/73.64/80.90 乱跳。**决定：阈值重新定标并入 O2-B 实测表**——换检测器后脸宽定义改变，现在改 30 这个数字等于白改。
- **D3 整句横幅为事实死路径（已修复，O1-C，待真机确认）**：原 `main.py:212-217` 先取 `events[-1].message`（整句）作为 banner，但紧接着只要 `active_warnings()` 非空就用 `"WARNING: " + labels` 覆盖；而 `triggered` 在异常持续期间恒为 True（`metrics.py:282-283`），故持续异常期间用户只能看到标签式横幅。后果：O1-B 的 `_WARNING_MESSAGES_ZH` 在真实运行中基本不可达，且横幅不告诉用户该往前还是往后靠。**修复**：抽出纯函数 `select_banner(now, events, active_labels, hold_sec)`（`reminder.py`），按「hold 内整句 → 超时且 active 显示标签 → 空串」选择；`main.py` 改为调用，`BANNER_HOLD_SEC = 3.0` 不变。新增 `select_banner` 单测与 `test_distance_banner_message_then_chinese_label` 端到端逻辑用例（前 3 s `距离过近，请后退`，之后 `警告：距离过近`）；真机目验仍待负责人。
- `BRIGHTNESS_WARNING` 类型已定义，但本次未实现亮度异常提醒（未收到明确的亮度触发阈值要求）；亮度等级仅在 HUD 显示。
- 报告中的「有效用眼时间」「距离分类时长占比」基于 CSV 行数 × 记录间隔近似（CSV 非逐帧写入）。
- 沙箱环境 `~/.config/matplotlib` 无写权限时 matplotlib 使用临时缓存目录（仅提示，不影响图表生成）。
- 在 ROS 2 环境下运行 pytest 需加 `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1` 前缀，详见 `CONTRIBUTING.md`。
- M6 覆盖率：`main.py`/`hud.py` 覆盖 0%（仅经子进程集成运行，未单测导入）；`config.py` 74%（部分校验分支未覆盖）。核心 7 模块（capture/detector/calibrator/metrics/reminder/logger/report）均 ≥85%。
- `test_keyboard_interrupt` 依赖时序（日志文件出现后发 SIGINT）；若视频处理极快提前结束，仍断言「退出 0 + 报告存在」，不严格保证命中中断分支。
- `test_log_directory_not_writable` 在 root 下跳过（目录权限不生效）。
- GitHub Actions 首轮运行状态**未验证**（本地无法查询）；如失败，优先检查 ubuntu-latest 的 `libgl1` 依赖与 4K 测试耗时阈值。
- 干净环境安装因默认 PyPI 大文件下载多次中断，改用清华镜像完成；依赖版本与 `requirements*.txt` 一致。

## 最近一次测试 / Latest Test

O1-C（2026-10-23）：`.venv` + `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest tests/ -q` → **108 passed in 3.28s**（91 原有 + 17 新增，零回归、零删除）。
回归锁证据：修改前 `tests/test_reminder.py::test_distance_warning_cross_direction_not_silenced` → **FAILED**（`assert len(close_events) == 1`，`0 == 1`）；修改后 → **1 passed**。

## 下一项任务 / Next Task

**O1-C 待负责人验收**：真机摄像头下凑近 3 秒，确认前 3 秒整句（`距离过近，请后退`）、3 秒后 `警告：距离过近`，无豆腐块；确认后由负责人打标签 `v0.2.1` 并推送。
随后才是 **O2 = YuNet 检测器替换**（先 O2-A 接线，默认仍 Haar）。**本次不自动进入 O2、不自动打标签/推送。**
负责人侧的书面作业：把 D1/D2/D3 的结论手写进 `docs/ALGORITHM_NOTES.md` 新 §10（执行方未改动该节）。

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
| 2026-10-20 | M4 复验缺陷修复：CSV 事件缓冲、坐姿 b 键显式基线；57 用例通过 / M4 fixes |
| 2026-10-21 | M4 验收通过 VERIFIED；缺陷 1/2 修复在真实数据下生效 / M4 verified |
| 2026-10-21 | M5 报告生成实现：report.py JSON+PNG + 退出自动生成，64 用例通过 / M5 implemented |
| 2026-10-21 | M5 验收通过 VERIFIED（真实会话 A/B 目验）/ M5 verified |
| 2026-10-21 | M6 测试与稳定性：stability 8 用例 + --headless/--config + 覆盖率，72 用例通过 / M6 implemented |
| 2026-10-21 | M6 验收通过 VERIFIED / M6 verified |
| 2026-10-21 | M7 v0.1.0 发布：CI workflow、README/CHANGELOG、干净环境复现 72 passed、tag v0.1.0 / M7 released |
| 2026-10-23 | O1-A 检测参数接入配置：detector/main/config + 测试，79 用例通过 / O1-A implemented |
| 2026-10-23 | O1-A 验收通过 VERIFIED；Qoder 独立复核 + 负责人目验；实测否决 min_neighbors=7（默认保持 5）/ O1-A verified |
| 2026-10-23 | 批准 O2 = YuNet 检测器替换（根治 Haar 姿态局限），排在 O1-B 与 v0.2.0 之后 / O2 YuNet approved in principle |
| 2026-10-23 | O1-B HUD 中文本地化：hud/config/main + test_hud，83 用例通过 / O1-B implemented |
| 2026-10-23 | O1-B 追加：警告横幅正文汉化（整句 + 动态标签三层映射），91 用例通过 / O1-B banner localization |
| 2026-10-23 | O1-B 负责人真机目验 6 项全过，状态升级为 VERIFIED / O1-B verified |
| 2026-10-23 | 目验中发现并登记 D1（跨方向告警静音）/D2（阈值贴噪声带）/D3（整句横幅死路径）；D1+D3 排入 O1-C，D2 并入 O2-B 定标 / defects logged |
| 2026-10-23 | O1-C 修复 D1（距离拆 `distance_close`/`distance_far` 双键）与 D3（`select_banner` 纯函数 + main 接线），方向化标签/整句 + zh 映射；108 用例通过，回归锁先红后绿 / O1-C implemented |
