# StudyGuard DSH 操作指南

> 本文档是用户使用 DeepSeek (DSH) 进行 StudyGuard 开发的完整操作手册。
> 所有提示词均可直接复制粘贴给 DSH。

---

## 1. 环境准备

### 1.1 激活虚拟环境

每次开发前，在终端执行：

```bash
cd ~/projects/study_guard
source .venv/bin/activate
```

### 1.2 确认依赖

```bash
python -c "import cv2; print('OpenCV:', cv2.__version__)"
python -c "import numpy; print('NumPy:', numpy.__version__)"
python -c "import matplotlib; print('matplotlib:', matplotlib.__version__)"
python -c "from PIL import Image; import PIL; print('Pillow:', PIL.__version__)"
python -m pytest --version
```

### 1.3 项目关键文件

| 文件 | 作用 |
|------|------|
| `docs/PROJECT_RULES.md` | 主控提示词——每次新对话开头必须发送 |
| `docs/PROJECT_SPEC.md` | 项目规格和功能边界 |
| `docs/INTERFACE_SPEC.md` | 模块接口定义和数据格式 |
| `docs/CODING_STANDARDS.md` | 编码规范 |
| `docs/TEST_PLAN.md` | 测试方案 |
| `docs/ARCHITECTURE.md` | 架构设计和数据流 |
| `docs/DSH_GUIDE.md` | 本文档——里程碑任务提示词库 |
| `docs/OWNER_GUIDE.md` | 负责人手册：范围硬边界、现状快照、学习与收口路线 |
| `PROJECT_STATUS.md` | 当前进度 |
| `ROADMAP.md` | 里程碑和时间表 |

---

## 2. 主控提示词使用方法

**每次与 DSH 开始新对话时**，第一步发送以下消息：

```
请阅读以下项目主控提示词，并确认你理解所有规则。不要立即编写代码，先回复「已理解，等待任务指令」。

[粘贴 docs/PROJECT_RULES.md 的全部内容]
```

DSH 确认后，再发送具体的里程碑任务提示词（见下方第 3 节）。

---

## 3. 里程碑任务提示词

### 3.1 M1: 视觉基础

```
请严格遵守 StudyGuard 项目主控提示词，并首先检查项目中的 PROJECT_STATUS.md、ROADMAP.md、docs/ARCHITECTURE.md、docs/INTERFACE_SPEC.md 和 docs/CODING_STANDARDS.md。

当前任务：M1 视觉基础

本次需要完成：
1. 实现 capture.py — 统一视频输入模块，支持本地视频文件和摄像头两种输入方式。接口定义见 INTERFACE_SPEC.md §1.2。
2. 实现 detector.py — Haar Cascade 人脸检测模块。接口定义见 INTERFACE_SPEC.md §1.3。
3. 实现 hud.py — 基础 HUD 叠加显示（FPS、人脸数量、人脸框）。接口定义见 INTERFACE_SPEC.md §1.9。
4. 实现 main.py — 主循环：打开输入 → 检测人脸 → HUD 叠加 → 显示窗口 → 处理退出。
5. 编写测试：tests/test_capture.py 和 tests/test_detector.py。

本次验收标准：
- [ ] 本地视频文件能打开并实时显示人脸框
- [ ] 摄像头输入能打开并实时显示人脸框
- [ ] FPS 计数器在 HUD 上显示
- [ ] 按 q 或 Esc 能正常退出并释放资源
- [ ] 视频文件不存在时输出明确错误信息
- [ ] 所有 M1 测试通过（pytest tests/test_capture.py tests/test_detector.py -v）

限制：
1. 只完成 M1 任务，不实现距离标定、坐姿评分、提醒和报告。
2. 修改前检查现有实现。
3. 尽量进行最小范围修改，不随意重写已有文件。
4. 不引入未经批准的依赖。
5. 添加或更新相关测试。
6. 执行实际可运行的测试，不得伪造结果。
7. 更新 PROJECT_STATUS.md。
8. 如果遇到阻塞问题，先报告原因和最小解决方案。
9. 不自动进入 M2。

禁止：
- 实现距离标定、坐姿评分、计时提醒、报告生成
- 引入 YOLO、MediaPipe、ROS 2 或 GUI 框架
- 安装不必要的新依赖
- 自动上传 GitHub

请先简要说明实施计划，再执行。完成后按主控提示词规定格式汇报，等待我确认。
```

---

### 3.2 M2: 距离标定与估算

```
请严格遵守 StudyGuard 项目主控提示词，并首先检查项目中的 PROJECT_STATUS.md、ROADMAP.md、docs/INTERFACE_SPEC.md §1.4 和 docs/CODING_STANDARDS.md。

当前任务：M2 距离标定与估算

本次需要完成：
1. 实现 calibrator.py — 三点标定，最小二乘法拟合 k 参数，保存/加载 JSON。接口定义见 INTERFACE_SPEC.md §1.4。
2. 扩展 metrics.py — 距离估算部分。接口定义见 INTERFACE_SPEC.md §1.5（仅距离相关字段）。
3. 更新 hud.py — 在 HUD 上显示距离值和距离分类。
4. 更新 main.py — 集成标定和测距流程。
5. 编写测试：tests/test_calibrator.py。

本次验收标准：
- [ ] 能在已知距离处采集标定样本
- [ ] k 参数通过最小二乘法正确拟合
- [ ] 标定数据保存和加载正常（configs/calibration.json）
- [ ] HUD 实时显示距离值
- [ ] 距离分类（too_close / normal / too_far）正确
- [ ] 所有 M2 测试通过（pytest tests/test_calibrator.py -v）
- [ ] 用已知距离的独立测试样本记录误差

限制：
1. 只完成 M2 任务。
2. 标定模型为 d = k / w，使用最小二乘法拟合。
3. 每个距离点采集多帧取稳定值，不用单帧。
4. 不引入深度学习模型。
5. 执行实际测试，不伪造结果。
6. 更新 PROJECT_STATUS.md 和 docs/ALGORITHM_NOTES.md。
7. 不自动进入 M3。

请先简要说明实施计划，再执行。完成后按主控提示词规定格式汇报，等待我确认。
```

---

### 3.3 M3: 行为指标与异常状态机

```
请严格遵守 StudyGuard 项目主控提示词，并首先检查项目中的 PROJECT_STATUS.md、ROADMAP.md、docs/INTERFACE_SPEC.md §1.5 和 docs/CODING_STANDARDS.md。

当前任务：M3 行为指标与异常状态机

本次需要完成：
1. 完善 metrics.py — 坐姿评分和亮度等级。接口定义见 INTERFACE_SPEC.md §1.5。
2. 实现异常持续时间跟踪和冷却机制。
3. 更新 hud.py — 显示坐姿分数、亮度等级、异常状态。
4. 编写测试：tests/test_metrics.py。

本次验收标准：
- [ ] 坐姿评分基于人脸位置和大小计算（0.0–1.0）
- [ ] 亮度等级基于帧亮度计算（1–5）
- [ ] 异常在指标持续超出阈值指定时间后触发
- [ ] 冷却机制防止重复告警
- [ ] 每个指标有明确含义和触发原因输出
- [ ] 所有 M3 测试通过（pytest tests/test_metrics.py -v）

限制：
1. 坐姿和亮度采用透明规则算法，不用机器学习。
2. 每个分数和阈值都有明确含义。
3. 如果某指标无法可靠识别某种动作，记录为局限。
4. 不自动进入 M4。
5. 更新 PROJECT_STATUS.md 和 docs/ALGORITHM_NOTES.md。

请先简要说明实施计划，再执行。完成后按主控提示词规定格式汇报，等待我确认。
```

---

### 3.4 M4: 提醒与日志

```
请严格遵守 StudyGuard 项目主控提示词，并首先检查项目中的 PROJECT_STATUS.md、ROADMAP.md、docs/INTERFACE_SPEC.md §1.6 §1.7 和 docs/CODING_STANDARDS.md。

当前任务：M4 提醒与日志

本次需要完成：
1. 实现 reminder.py — 20-20-20 提醒、久坐提醒、异常提醒。接口定义见 INTERFACE_SPEC.md §1.6。必须使用可注入时钟（clock 参数），默认 time.monotonic()。
2. 实现 logger.py — CSV 会话日志，按配置间隔写入。接口定义见 INTERFACE_SPEC.md §1.7。CSV 格式见 INTERFACE_SPEC.md §3。
3. 完善 config.py — 完整 JSON 配置加载和校验。接口定义见 INTERFACE_SPEC.md §1.1。配置 schema 见 INTERFACE_SPEC.md §2。
4. 更新 main.py — 集成提醒和日志。
5. 编写测试：tests/test_reminder.py 和 tests/test_config.py。

本次验收标准：
- [ ] 20-20-20 提醒在 20 分钟有效用眼时间后触发
- [ ] 久坐提醒在配置时间后触发
- [ ] 人脸丢失时暂停计时器，恢复时继续
- [ ] effective_study_time 不包含人脸丢失时间
- [ ] CSV 按配置间隔写入（不是每帧）
- [ ] CSV 格式与 INTERFACE_SPEC.md §3 一致
- [ ] JSON 配置加载正常，缺失键回退默认值
- [ ] 无效配置在启动时抛出 ConfigError
- [ ] 所有 M4 测试通过（pytest tests/test_reminder.py tests/test_config.py -v）

限制：
1. 计时器必须可测试——使用注入时钟，不依赖真实时间。
2. 20-20-20 规则：每连续用眼 20 分钟提醒远眺 20 秒。
3. 久坐提醒独立计时。
4. 不自动进入 M5。
5. 更新 PROJECT_STATUS.md。

请先简要说明实施计划，再执行。完成后按主控提示词规定格式汇报，等待我确认。
```

---

### 3.5 M5: 报告生成

```
请严格遵守 StudyGuard 项目主控提示词，并首先检查项目中的 PROJECT_STATUS.md、ROADMAP.md、docs/INTERFACE_SPEC.md §1.8 和 docs/CODING_STANDARDS.md。

当前任务：M5 报告生成

本次需要完成：
1. 实现 report.py — 会话摘要报告。接口定义见 INTERFACE_SPEC.md §1.8。
2. 报告内容：会话时长、有效用眼时间、距离分布统计、坐姿统计、亮度统计、提醒次数。
3. 使用 matplotlib 生成趋势图（如果配置启用）。
4. 处理数据不足的情况——显示"数据不足"而非误导性统计。
5. 编写测试：tests/test_report.py。

本次验收标准：
- [ ] 会话结束时生成完整报告
- [ ] 报告包含所有统计项
- [ ] 图表正确渲染
- [ ] 空数据或全部人脸丢失时显示"数据不足"
- [ ] 损坏的 CSV 日志不导致崩溃
- [ ] 所有 M5 测试通过（pytest tests/test_report.py -v）

限制：
1. 没有检测到人脸的帧不能伪造距离数据。
2. 视频结束时不因最后一帧状态误报。
3. 不自动进入 M6。
4. 更新 PROJECT_STATUS.md。

请先简要说明实施计划，再执行。完成后按主控提示词规定格式汇报，等待我确认。
```

---

### 3.6 M6: 测试与稳定性

```
请严格遵守 StudyGuard 项目主控提示词，并首先检查项目中的 PROJECT_STATUS.md、ROADMAP.md、docs/TEST_PLAN.md 和 docs/CODING_STANDARDS.md。

当前任务：M6 测试与稳定性

本次需要完成：
1. 补全 docs/TEST_PLAN.md 中所有 M6 测试用例。
2. 异常输入测试：零长度视频、损坏视频文件、不存在的文件。
3. 边界条件测试：全部帧无人脸、人脸快速出现/消失。
4. 资源管理测试：KeyboardInterrupt 时资源释放。
5. 运行完整测试套件并生成覆盖率报告。

本次验收标准：
- [ ] TEST_PLAN.md 中所有 M6 测试用例已实现并通过
- [ ] 零长度视频正常处理
- [ ] 损坏视频不崩溃
- [ ] 全程无人脸时运行到结束
- [ ] Ctrl+C 后资源正确释放，部分报告保存
- [ ] 完整测试套件通过（pytest tests/ -v）
- [ ] 覆盖率报告已生成（pytest tests/ --cov=. --cov-report=term-missing）
- [ ] 未解决问题如实登记

限制：
1. 不为通过测试而删除测试或降低标准。
2. 不自动进入 M7。
3. 更新 PROJECT_STATUS.md 和 docs/TEST_PLAN.md。

请先简要说明实施计划，再执行。完成后按主控提示词规定格式汇报，等待我确认。
```

---

### 3.7 M7: 开源发布

```
请严格遵守 StudyGuard 项目主控提示词，并首先检查项目中的 PROJECT_STATUS.md、ROADMAP.md 和 docs/TEST_PLAN.md。

当前任务：M7 开源发布

本次需要完成：
1. 完善 README.md 和 README_zh.md — 添加截图说明、运行示例、测试结果。
2. 检查 LICENSE — 确认第三方资源许可。
3. 创建 GitHub Actions 工作流 — 推送时自动运行 pytest。
4. 检查 .gitignore — 确保无敏感文件。
5. 在干净虚拟环境中验证安装和测试流程。
6. 推送所有代码到 GitHub。
7. 打标签 v0.1.0。

本次验收标准：
- [ ] README 包含：简介、功能、安装、运行、测试、算法局限、许可证
- [ ] 干净 git clone + pip install + pytest 通过
- [ ] GitHub Actions 自动运行测试
- [ ] 仓库中无真实人脸视频、隐私数据或密钥
- [ ] 发布标签 v0.1.0

限制：
1. 不提交真实人脸视频或隐私数据。
2. 不提交 calibration.json（已在 .gitignore 中）。
3. 更新 PROJECT_STATUS.md 和 docs/CHANGELOG.md。

请先简要说明实施计划，再执行。完成后按主控提示词规定格式汇报，等待我确认。
```

---

### 3.8 O1-A: 检测参数接入配置（v0.2.0，行为不变）

> 背景：`configs/default.json` 已有 `detection.min_neighbors`，`config.py` 也校验它，
> 但 `main.py` 构造 `FaceDetector()` 时不传参，参数实际写死在 `detector.py` 常量里。
> 本任务只修这个失效的配置键，**不改任何数值**。

```
请严格遵守 StudyGuard 项目主控提示词，并首先检查项目中的 PROJECT_STATUS.md、docs/INTERFACE_SPEC.md §1.3、docs/CODING_STANDARDS.md，以及 detector.py、config.py、main.py 的现有实现。

当前任务：O1-A 检测参数接入配置（v0.1.0 之后的优化项，不改变任何默认行为）

本次需要完成：
1. detector.py：扩展 FaceDetector.__init__，新增可选参数 scale_factor、min_neighbors、min_face_size。默认值必须等于现有的 DEFAULT_SCALE_FACTOR / DEFAULT_MIN_NEIGHBORS / DEFAULT_MIN_FACE_SIZE（1.1 / 5 / 30），保证 FaceDetector() 无参构造的行为与 v0.1.0 完全一致。detect() 使用实例参数而不是模块常量。
2. main.py：用 config.get("detection.scale_factor") / config.get("detection.min_neighbors") / config.get("detection.min_face_size") 构造 FaceDetector，替换当前无参构造。
3. config.py：补齐 detection 段校验——scale_factor 必须在 1.01 到 2.0 之间，min_face_size 必须 >= 1；保留现有 min_neighbors >= 0 校验。非法值抛 ConfigError，错误信息风格与现有校验一致。
4. 测试：
   - tests/test_detector.py：新增参数生效测试，断言实例属性来自构造参数，并验证无参构造仍等于旧默认值。
   - tests/test_config.py：新增 scale_factor、min_face_size 越界的失败用例。
5. 文档：docs/INTERFACE_SPEC.md §1.3 更新 FaceDetector 签名；docs/CHANGELOG.md 增加 Unreleased 条目；更新 PROJECT_STATUS.md。

本次验收标准：
- [ ] 现有 72 个测试全部通过，无回归
- [ ] FaceDetector() 无参构造仍可用且参数等于 1.1 / 5 / 30
- [ ] 把配置里 min_neighbors 临时改成 20 后，程序实际使用 20（日志或 HUD 可观察），改回 5 后恢复
- [ ] scale_factor / min_face_size 越界时启动即报 ConfigError
- [ ] INTERFACE_SPEC §1.3 与代码签名一致

限制：
1. 不修改 configs/default.json 的任何数值（min_neighbors 保持 5，调参需要实测数据，由项目负责人另行批准）。
2. 不更换检测器算法（不引入 YuNet、DNN、MediaPipe），不改 cascade_path 逻辑。
3. 不做 HUD 汉化，不改 hud.py（那是 O1-B，本次不碰）。
4. 不引入新依赖。
5. 尽量最小范围修改，不重写已有文件。
6. 不自动进入 O1-B，不自动上传 GitHub。
7. 执行实际可运行的测试，不得伪造结果。

请先简要说明实施计划，再执行。完成后按主控提示词规定格式汇报，等待我确认。
```

---

### 3.9 O1-B: HUD 中文本地化（Pillow 叠加）

> 背景：`cv2.putText` 无法渲染 CJK。Pillow 已在 `requirements.txt`（`Pillow>=10.0.0`），系统字体为 `/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc`，**本任务不新增任何依赖**。

```
请严格遵守 StudyGuard 项目主控提示词，并首先检查项目中的 PROJECT_STATUS.md、docs/INTERFACE_SPEC.md §1.9 与 §3、hud.py、config.py、configs/default.json、tests/test_hud.py。

当前任务：O1-B HUD 中文本地化

本次需要完成：
1. hud.py：新增 Pillow 文字渲染路径，用于替换 cv2.putText 的文本绘制。要求：
   - HUDOverlay.draw 的函数签名保持不变（frame、metrics、fps、face_count、warning、baseline_hint），返回值仍是同形状同类型 BGR ndarray，main.py 无需改动调用方式。
   - 字体探测：按候选路径列表依次查找存在的 CJK 字体文件（首选 /usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc，再试 NotoSansCJK-Bold.ttc、WenQuanYi 等常见路径），把探测逻辑写成独立函数以便测试 monkeypatch。
   - 回退：找不到任何 CJK 字体时，自动退回现有 cv2.putText 英文渲染，不得抛异常、不得画出豆腐块（□）。
   - 文本绘制位置与现有行距保持一致（y = 25/50/75/100/125，底部提示 y = height-45，警告 y = height-20），颜色沿用现有 TEXT_COLOR / WARN_COLOR 常量（注意 cv2 是 BGR、PIL 是 RGB，需要正确换算，不要出现红绿互换）。
2. 语言开关：config.py 的 DEFAULT_CONFIG 与 configs/default.json 新增 "hud": { "language": "zh" }；config.py 校验 language 只能是 "zh" 或 "en"，非法值抛 ConfigError。HUDOverlay 构造参数新增 language（默认值必须是 "en"，保证现有测试与 main.py 旧调用行为不变），main.py 从配置传入。
3. 文案映射：仅在渲染层维护「内部值 → 显示文本」的映射表，覆盖 FPS、Faces、Distance、Posture、Light、unknown/too_close/too_far/normal 四类距离档位、warning 横幅前缀与 baseline_hint。
4. 测试：tests/test_hud.py 增加——language="zh" 时返回值仍为同形状 ndarray 且不抛异常；monkeypatch 字体探测返回 None 时走英文回退；configs 里 language 非法时 ConfigError；language 默认值为 "en"。
5. 文档：docs/INTERFACE_SPEC.md §1.9 与 §2 配置 schema 增加 hud.language；docs/ALGORITHM_NOTES.md 记一句「中文渲染依赖系统 CJK 字体，缺失时回退英文」；docs/CHANGELOG.md 更新 Unreleased；更新 PROJECT_STATUS.md。

本次验收标准：
- [ ] O1-A 之后的全部测试通过（含新增 HUD 测试），无回归
- [ ] language="zh" 时摄像头画面 HUD 显示中文标签，无乱码方块
- [ ] language="en" 时输出与 v0.1.0 逐行一致（文字内容与位置）
- [ ] CSV 表头与 reminder/枚举字符串未发生变化（对比 logs/ 新文件首行）
- [ ] 无 CJK 字体环境下程序仍能启动并显示英文 HUD（用 monkeypatch 测试证明）

限制（重要，越界即视为不合规）：
1. 禁止修改 logger.py 的 CSV 表头、列顺序与写入值；禁止修改 metrics.py 中 DistanceCategory 的枚举 value。CSV 与 JSON 报告必须继续存英文值，中文只存在于屏幕渲染层。
2. 不改动 reminder.py 产生的事件字符串本身；如需汉化横幅，只在 hud.py 的映射表里转换显示文本。
3. 不新增依赖（Pillow 已在 requirements.txt）。
4. 不改 report.py、metrics.py、detector.py、calibrator.py。
5. 不引入 GUI 框架、不改变窗口尺寸或行距布局。
6. 不自动进入下一项（YuNet 属于 O2），不自动上传 GitHub。
7. 执行实际可运行的测试，不得伪造结果。

请先简要说明实施计划，再执行。完成后按主控提示词规定格式汇报，等待我确认。
```

---

### 3.10 O2-A: YuNet 检测器后端接入（默认仍 Haar，v0.3.0）

> 背景：Haar 的姿态局限（侧脸/低头/刘海丢框）已实测确认无法靠阈值解决，见 `docs/ALGORITHM_NOTES.md` §8。
> O2-A **只加后端选项，不改默认行为**。
> **已核实（2026-10-23 负责人本地执行）**：`cv2 4.14.0` 自带 `cv2.FaceDetectorYN` 与 `cv2.FaceDetectorYN_create`，
> 推理走 OpenCV 内置 DNN，**因此本任务不新增任何 pip 依赖**，只需一个 `.onnx` 模型文件。
>
> 关键风险，必须先看懂再动手：YuNet 返回的人脸框**宽度定义与 Haar 不同**（紧致正脸框 vs 带余量检测框），
> 而 `configs/calibration.json` 的 `k=11488.3` 是拿 Haar 的脸宽拟出来的。换后端等于换尺子刻度。
> **所以默认后端必须是 `haar`，任何把默认切成 `yunet` 的改动都算越界。**

```
请严格遵守 StudyGuard 项目主控提示词，并首先检查项目中的 PROJECT_STATUS.md、docs/OWNER_GUIDE.md §0 与 §4、docs/INTERFACE_SPEC.md §1.3 与 §2、docs/ALGORITHM_NOTES.md §8，以及 detector.py、config.py、configs/default.json、main.py 的现有实现。

当前任务：O2-A YuNet 检测器后端接入（v0.2.0 之后的优化项，不改变任何默认行为）

第一步（不要跳过）：先只做调研并汇报，等我批准后再写代码。汇报内容：
- cv2.FaceDetectorYN_create 的完整签名与各参数含义（以本仓库 OpenCV 4.14.0 的实测签名为准，用 inspect 或 help 读取，不要凭记忆）
- detect() 返回的 ndarray 形状与各列含义
- 你打算让模型文件从哪里来（HTTPS 来源 URL），以及该模型的许可是否允许我们把它提交进公开仓库
- 输入尺寸（input_size）必须是 32 的倍数这一约束在你的方案里怎么满足

获得批准后本次需要完成：
1. detector.py：新增 YuNet 后端，与现有 Haar 后端并存。
   - FaceDetector 保持现有类名、无参构造行为、detect() 签名与 list[FaceBox] 返回类型完全不变（metrics.py、calibrator.py、main.py 不得因签名改动而修改）。
   - 新增后端选择参数（如 backend="haar"|"yunet"），默认必须是 "haar"。
   - YuNet 在固定 input_size 上推理，返回坐标必须换算回原始帧坐标系。这段换算逻辑写成独立的、可脱离摄像头单测的纯函数（输入检测框 + 缩放比，输出换算后坐标），不要用内联魔法数字。
   - 两后端的输出统一收敛为 FaceBox；YuNet 结果中的 landmark 与 score 列本阶段一律忽略（不做头部姿态）。
   - 模型文件缺失时构造即抛出明确异常（沿用现有 cascade 加载失败 RuntimeError 的错误风格），不得静默回退。
2. config.py 与 configs/default.json：detection 段新增 backend（默认 "haar"）、score_threshold、nms_threshold、top_k、model_path（默认指向本地路径字符串，不创建文件）。
   - 校验：backend 只能是 "haar" 或 "yunet"；score_threshold 与 nms_threshold 必须在 (0, 1] 内；top_k >= 1。非法值抛 ConfigError，错误信息风格与现有校验一致。
   - configs/default.json 现有数值一律不改（detection.scale_factor=1.1、min_neighbors=5、min_face_size=30 保持原样）。
   - backend="yunet" 且 model_path 不存在时，必须在启动阶段报清晰错误并退出，不得自动降级成 haar。
3. main.py：按配置构造 FaceDetector，其余流程不动。
4. 测试：
   - tests/test_detector.py 新增：backend 默认值为 haar；无参构造与 v0.2.0 行为一致；坐标换算纯函数的正确性（构造已知缩放比的假想框，断言换算结果，含 1:1 与非 1:1 两种情形）。
   - YuNet 真实推理用例：若模型文件不在本地则 pytest.skip 并在汇报里**如实统计 skip 数量**，禁止用 mock 让真实推理用例假装通过。
   - tests/test_config.py 新增 backend/score_threshold/nms_threshold/top_k 的非法值用例，以及 model_path 缺失时启动报错的用例。
5. 文档：docs/INTERFACE_SPEC.md §1.3 签名与 §2 配置 schema 同步；docs/CHANGELOG.md 增加 Unreleased 条目；docs/ALGORITHM_NOTES.md 增补一句「换检测后端会使基于 Haar 脸宽的标定 k 失效，切换前必须重新标定或给出脸宽换算系数」；更新 PROJECT_STATUS.md。

本次验收标准：
- [ ] O1-B 之后的全部测试通过，且无一条测试被删除或被降低断言
- [ ] FaceDetector() 无参构造仍走 Haar，参数仍等于 1.1 / 5 / 30
- [ ] 不传 model_path、不动配置时，程序行为与 v0.2.0 逐帧一致（默认路径不经过任何 YuNet 代码）
- [ ] backend="yunet" + 有效模型路径时能检出人脸（负责人真机目验判定，沙箱无 /dev/video0 不得代为声明通过）
- [ ] backend="yunet" + 模型文件缺失时启动即报错退出，不静默降级
- [ ] 坐标换算纯函数有独立单测，非 1:1 缩放比下断言通过
- [ ] INTERFACE_SPEC §1.3 与 §2 与代码签名、配置键一致

限制（重要，越界即视为不合规）：
1. 不改 configs/default.json 的任何现有数值，不把 backend 默认值设成 yunet。
2. 不重新标定、不改 calibrator.py、不改 metrics.py 的距离逻辑（脸宽换算系数与重标定属于 O2-B，由负责人亲自实测，不归你）。
3. 不新增 pip 依赖。模型文件是否入库需我单独批准，未批准前只允许用本地路径引用，且不得把大文件提交进仓库。
4. 不做头部姿态、不做眨眼检测、不做 PyInstaller 打包、不引入 GUI 框架——这些已从项目范围中砍掉。
5. 不改 report.py、reminder.py、logger.py、hud.py。
6. 尽量最小范围修改，不重写已有文件，不更换现有类名或文件名。
7. 不自动进入 O2-B，不自动打标签，不自动上传 GitHub。
8. 执行实际可运行的测试，不得伪造结果；未执行的测试必须标记为未验证。
9. 如果遇到阻塞，按 §8 格式报告原因和最小解决方案，不得擅自改变架构或换用 MediaPipe。

请先汇报调研结果，等我批准后再说明实施计划并执行。完成后按主控提示词规定格式汇报，等待我确认。
```

---

### 3.11 O1-C: 修复 D1 跨方向告警静音 + D3 整句横幅死路径（v0.2.1）

> 背景（负责人 2026-10-23 真机目验发现，证据已登记在 `PROJECT_STATUS.md`「已知问题」）：
> - **D1**：`reminder.py:160-166` 把 `too_close` 与 `too_far` 合并成同一个 tracker 键 `"distance"` 共用 60 s 冷却，
>   而 `metrics.py:285-288` 的冷却判断读 `state.last_triggered_at`，异常恢复分支（277-280 行）**不清零该字段**。
>   后果：一次"离太远"告警会压掉之后 60 s 内所有"离太近"告警。实证 `logs/session_20261023_205533.csv`：
>   22.4 s 因 too_far(104 cm) 触发，随后 42.8–68.2 s 连续 26 s 的 too_close 零告警；`cooldown_sec=0` 对照组 2 s 内即触发。
> - **D3**：`main.py:212-219` 先取 `events[-1].message` 作整句，但紧接着只要 `active_warnings()` 非空就用
>   `"WARNING: " + labels` 覆盖；而 `triggered` 在异常持续期间恒为 True（`metrics.py:282-283`），
>   所以 `BANNER_HOLD_SEC = 3.0` 的整句在持续异常期间**永远显示不出来**，`_WARNING_MESSAGES_ZH` 成为事实死路径。
> - 91 个测试全部通过却漏掉这两条，因为没有任何用例覆盖**跨方向状态序列**与**端到端横幅选择**。

```
请严格遵守 StudyGuard 项目主控提示词，并首先检查项目中的 PROJECT_STATUS.md（重点读「已知问题」中的 D1 与 D3 两条）、docs/OWNER_GUIDE.md §0、docs/INTERFACE_SPEC.md §1.6 §1.9、docs/CODING_STANDARDS.md，以及 reminder.py、metrics.py、main.py、hud.py 的现有实现。

当前任务：O1-C 修复 D1（跨方向告警静音）与 D3（整句横幅死路径），发布为 v0.2.1

本次需要完成：
1. D1 —— reminder.py：把距离异常拆成两个独立的 tracker 键 "distance_close" 与 "distance_far"，各自使用现有的 distance_anomaly_threshold_sec 与 cooldown_sec。要求：
   - 不修改 metrics.py 的 AnomalyTracker 实现与接口（保持 update/is_active/reset 三个方法的签名与语义不变），只在 reminder.py 侧用两个键分别调用。
   - 同一帧内两个键互斥（DistanceCategory 是单值），非异常的那一侧必须以 is_anomalous=False 调用 update，使其状态正常复位。
   - 任一侧触发即产生一条 ReminderType.DISTANCE_WARNING 事件，不得因为拆键而产生两条重复事件。
2. D3 —— 把横幅选择逻辑从 main.py 抽成可单测的纯函数（建议放在 reminder.py，例如 select_banner(now, events, active_labels, hold_sec) -> str），main.py 改为调用它，BANNER_HOLD_SEC 常量与现有取值 3.0 保持不变。优先级必须是：
   - 事件触发后的 hold_sec 之内：显示该事件的整句 message；
   - 超过 hold_sec 且仍有 active 异常：显示 "WARNING: " + 标签串；
   - 两者皆无：空字符串。
3. 方向化标签 —— reminder.py 的 active_warnings() 不再返回 "distance"，改为按当前异常方向返回 "distance_too_close" 或 "distance_too_far"；hud.py 的 _WARNING_LABELS_ZH 增加这两条映射（"距离过近" / "距离过远"）。posture 标签保持 "posture" 不变。这是有意的英文横幅文案变更，必须写进 docs/CHANGELOG.md 的 Fixed/Changed。
4. 测试（这是本任务的重点，缺任何一条视为未完成）：
   - 跨方向回归锁：用注入时钟构造序列——too_far 持续 3 s 触发一次 → 恢复正常 1 帧 → 立刻 too_close 持续 3 s → **断言必须再触发一次**（当前实现下该断言会失败，这是本缺陷的回归锁）。
   - 同方向冷却仍生效：too_close 触发后 60 s 内再次持续 too_close，断言不重复触发。
   - select_banner 纯函数单测：事件后 0~hold_sec 内返回整句；超过 hold_sec 且有 active 时返回标签串；都无时返回空串。
   - 断言 CSV 表头、列顺序与 reminder 字符串（ReminderType 的 value）在修改前后逐字节一致。
   - 现有 91 个测试零回归，禁止删除任何用例或放宽任何断言。
5. 文档：docs/INTERFACE_SPEC.md 同步 active_warnings() 返回值与 select_banner 签名；docs/CHANGELOG.md 增加 v0.2.1 的 Fixed 条目（D1、D3 各一条，注明用户可见的行为变化）；更新 PROJECT_STATUS.md。

本次验收标准：
- [ ] 全部测试通过，且新增用例数量在汇报中如实列出
- [ ] 跨方向回归锁用例在**修改前**会失败、**修改后**通过（请在汇报中贴出这两次运行结果，证明该用例真的能抓住这个 bug）
- [ ] 同方向 60 s 冷却行为未变（不得为了修 D1 而把冷却关掉）
- [ ] 持续 too_close 期间，横幅在前 3 秒显示整句、3 秒后显示"警告：距离过近"（英文模式为 WARNING: distance_too_close）
- [ ] CSV 表头与列值逐字节未变
- [ ] configs/default.json 数值零改动

限制（重要，越界即视为不合规）：
1. 禁止修改 configs/default.json 的任何数值，特别是 distance.too_close_cm=30.0——该阈值的重新定标属于 D2，排在 O2-B 实测之后，本次不动。
2. 禁止修改 logger.py 的 CSV 表头与写入值，禁止修改 metrics.py 中 DistanceCategory 的枚举 value。
3. 禁止修改 AnomalyTracker 的接口与内部实现（拆键方案只在 reminder.py 侧完成）。
4. 禁止改动 docs/ALGORITHM_NOTES.md 的 §10——该节由项目负责人本人撰写中，你只允许追加 §11 及之后的内容。
5. 不改 detector.py、calibrator.py、report.py、config.py；不新增依赖；不引入 GUI 框架。
6. 不自动进入 O2，不自动打标签，不自动上传 GitHub。
7. 执行实际可运行的测试，不得伪造结果；未执行的测试必须标记为未验证。
8. 如遇阻塞，按 §8 格式报告原因与最小方案，不得擅自改变架构。

请先简要说明实施计划（特别是跨方向回归锁那条用例怎么构造时序），再执行。完成后按主控提示词规定格式汇报，等待我确认。
```

---

### 3.12 O2-B 第一轮: 标定按后端分开存 k + D4 措辞 + D6 注释（v0.3.0）

> 背景（2026-10-24，O2-A 真机验收后决定，负责人选方案 A）：
> - O2-A 已让 `detection.backend` 可切换，且 `main.py:157` 构造的 detector 实例被 `main.py:269` 的
>   `collect_sample()` 复用，所以**零代码改动就能给 YuNet 重标定**。
> - 但 `configs/calibration.json` 只存**一个** `k`，且 `CALIBRATION_FILE` 不跟随 `--config`。
>   后果：给 YuNet 标定完之后，默认 Haar 路径会拿 YuNet 的 `k` 算距离——**静默错，且无报错**。
>   这是本轮唯一的真问题，其余两条是收尾。
> - 实测已证明"用一个脸宽换算系数跨后端换算"这条路走不通（真机同一坐姿 YuNet/Haar 脸宽比 0.771，
>   离线测试图上 0.864，**比值非常数**），所以只能分开存 k。
> - 默认后端**仍然保持 `haar`**：公开仓库必须 clone 即跑，不得把需下载的模型变成基础功能的必要条件
>   （`PROJECT_RULES.md` 规则 4）。
> - 顺带收掉 D4（同屏 `[太近]` 栏 vs `距离过近` 横幅两套措辞）与 D6（`detector.py` 里
>   "Matches Haar's min_face_size semantics" 措辞不准确）。
> - **D2（`too_close_cm` 阈值重定标）不在本轮**：它需要负责人先完成 YuNet 标定与噪声带实测。

```
请严格遵守 StudyGuard 项目主控提示词，并首先检查项目中的 PROJECT_STATUS.md、docs/INTERFACE_SPEC.md §1.3 与 §1.4 与 §2、docs/CHANGELOG.md，以及 calibrator.py、main.py、configs/calibration.json、hud.py、detector.py 的现有实现。

当前任务：O2-B 第一轮 = 标定数据按后端分开存 k（v0.3.0 收口轮的第一步）

第一步（不要跳过）：先说明实施计划，等我批准后再改代码。计划里必须专门回答：
- save() 的合并写入策略是什么（读-改-写？如何保证不丢另一个后端的条目？并发或异常中断时怎么办？）
- 旧格式文件（只有顶层 k/samples、没有 backends 键）如何被识别与读取
- 三种起始状态（文件不存在 / 旧格式 / 已含其他后端数据）的用例分别怎么构造

获得批准后本次需要完成：
1. calibrator.py：标定按后端分开存。
   - DistanceCalibrator 需要知道自己在为哪个后端工作（构造参数或 save/load 参数，二选一，说明理由）。
   - 文件 schema 保持向后兼容：现有 configs/calibration.json 的顶层 "k" 与 "samples" **原样视为 haar 的数据，不得改动其值或搬家**；新增可选的 "backends" 键存放其他后端，形如
     {"k": <haar k>, "samples": [haar 样本], "backends": {"yunet": {"k": ..., "samples": [...]}}}
   - save() 必须**合并写入**：先读现有文件，只替换本后端对应的条目，保留其他后端条目。禁止整文件覆盖导致另一后端的 k 被清空——这是本任务最容易做错、也最严重的一点。
   - load() 按后端取数：backend=="haar" 读顶层 k/samples（旧文件零改动即可读）；其他后端读 backends[<backend>]；该后端缺失时抛 CalibrationError，消息写明"该后端尚未标定"。**严禁在任何情况下回落到其他后端的 k。**
   - main.py 现有的 [WARN] 兜底分支保持不变：未标定的后端就是没有距离读数，这是正确行为，不要为了"看起来能用"而偷偷给一个 k。
   - 启动与保存的终端提示要打印当前后端，例如 `[INFO] Loaded calibration for backend 'haar': k=11488.3`。
2. hud.py（D4）：`_ZH_LABELS` 里 too_close/too_far 的中文值由「太近/太远」改为「过近/过远」，与 O1-C 的方向化横幅对齐。只改这两个字符串值；枚举 value、CSV 内容、英文标签一律不动。相关用例的期望值同步（改期望值不等于降低断言）。
3. detector.py（D6）：把 yunet_faces_to_boxes 里「Matches Haar's min_face_size semantics」改成准确表述——比较符与边界（含等号）一致，但作用机制不同：Haar 的 minSize 是检测阶段参数、会改变检出框本身；YuNet 侧是检出后的过滤。docs/INTERFACE_SPEC.md 若有同样措辞一并修正。此项只改注释/docstring 文字，不得改任何行为。
4. 测试（新增，不许删除或放宽任何现有用例）：
   - 给 yunet 标定并 save 之后，**haar 的顶层 k 与 samples 必须逐字节不变**；反向同理。
   - 旧格式文件（无 backends 键）能被 haar 正常读取。
   - load(backend="yunet") 在未标定时报 CalibrationError，而不是返回 haar 的 k。
   - save 的合并写入覆盖三种起始状态：文件不存在 / 旧格式 / 已含另一后端数据。
   - 汇报时给出与修改前的**用例名逐名比对**结果（新增多少、删除必须为 0）。
5. 文档：docs/INTERFACE_SPEC.md §1.4（calibrator 接口）与 §2 同步新 schema；docs/CHANGELOG.md 的 [Unreleased] 增加一条（按后端存 k 属行为变更，须写明旧文件仍可直接使用）；PROJECT_STATUS.md 更新状态与本任务记录。

限制（重要，越界即视为不合规）：
1. 禁止修改 configs/default.json 与 configs/calibration.json 的**任何数值**。`too_close_cm`/`too_far_cm` 的重新定标属于 O2-B 第二轮，需要负责人真机数据，本轮不碰。
2. 禁止修改 metrics.py、reminder.py、logger.py、report.py 与 detector.py 的行为（D6 仅允许改注释文字）。
3. 禁止修改 DistanceCategory 枚举 value、CSV 表头与字段值。
4. 禁止把默认后端改成 yunet；禁止新增 pip 依赖；禁止把 .onnx 提交进仓库；禁止在代码或测试里联网下载任何东西；禁止把人脸图片提交进仓库。
5. 禁止修改 docs/ALGORITHM_NOTES.md（§11 由负责人拿到真机数据后处理）。
6. 尽量最小范围修改，不重写已有文件，不更换现有类名或文件名。
7. 不自动进入 O2-B 第二轮，不自动打标签，不自动上传 GitHub。
8. 执行实际可运行的测试，不得伪造结果；未执行的测试必须标记为未验证。
9. 如果遇到阻塞，按 §8 格式报告原因和最小解决方案，不得擅自改变架构。

请先汇报实施计划（重点是 save 的合并写入与三种起始状态的用例设计），等我批准后再执行。完成后按主控提示词规定格式汇报，等待我确认。
```

---

## 4. 任务提示词模板

当需要在某个里程碑内分配子任务时，使用此模板：

```
请严格遵守 StudyGuard 项目主控提示词，并首先检查项目中的 PROJECT_STATUS.md、PROJECT_SPEC.md、ROADMAP.md 和相关源代码。

当前任务：[填写一个明确任务]
本次验收标准：[填写可以通过实际运行或测试验证的条件]

限制：
1. 只完成本次任务，不扩展需求。
2. 修改前检查现有实现。
3. 尽量进行最小范围修改，不随意重写已有文件。
4. 不引入未经批准的依赖。
5. 添加或更新相关测试。
6. 执行实际可运行的测试，不得伪造结果。
7. 更新 PROJECT_STATUS.md 和必要的测试记录。
8. 如果遇到阻塞问题，先报告原因和最小解决方案，不得擅自改变架构。
9. 不自动进入下一个任务。

请先简要说明实施计划，再执行本次任务。完成后按照项目主控提示词规定的格式汇报结果，并等待我确认。
```

---

## 5. 纠偏提示词

当 DSH 开始发散、扩展需求或偏离计划时，直接发送：

```
停止扩展需求。请重新读取 StudyGuard 的项目主控提示词、项目规格、路线图和当前进度。

你刚才提出的内容中，凡是没有纳入当前阶段、没有经过我批准的新功能或新技术，都不得实施。

现在请回答三个问题：
1. 当前里程碑是什么？
2. 当前唯一未完成且优先级最高的任务是什么？
3. 该任务的验收标准是什么？

然后只围绕这项任务继续。如果现有实现存在问题，请优先修复问题，而不是更换技术栈、重写项目或增加功能。没有实际执行的测试必须标记为未验证。

等待我确认后再进行范围变更。
```

---

## 6. 5 天推进时间表

| 天 | 时段 | 里程碑 | 内容 | 验收检查点 |
|----|------|--------|------|-----------|
| Day 1 | 上午 | M0 ✅ | 项目初始化（Qoder 已完成） | 目录完整、文档齐全 |
| Day 1 | 下午 | M1 | 视频/摄像头读取、Haar 检测、HUD | 视频+摄像头均可演示人脸检测 |
| Day 2 | 全天 | M2 | 距离标定与估算 | 三点标定完成、误差记录 |
| Day 3 | 全天 | M3 | 行为指标与异常状态机 | 坐姿/亮度/异常跟踪测试通过 |
| Day 4 | 上午 | M4 | 提醒与日志 | 20-20-20/久坐/CSV/JSON 测试通过 |
| Day 4 | 下午 | M5 | 报告生成 | 完整报告、异常数据处理 |
| Day 5 | 上午 | M6 | 测试与稳定性 | 全量测试+覆盖率 |
| Day 5 | 下午 | M7 | 开源发布 | GitHub 推送、Actions、v0.1.0 |

### 每日工作循环

```
1. 发送主控提示词（新对话必须）
2. 发送里程碑任务提示词
3. DSH 报告实施计划 → 你确认
4. DSH 执行 → 你检查输出
5. DSH 汇报结果 → 你验收
6. 验收通过 → 更新 PROJECT_STATUS.md → 进入下一个任务
7. 验收未通过 → 指出问题 → DSH 修复 → 重新验收
```

---

## 7. 验收审查清单

每个里程碑完成后，检查以下项目：

### 通用检查项（每个里程碑都检查）

- [ ] DSH 是否只做了指定任务，没有擅自扩展？
- [ ] 代码是否符合 docs/CODING_STANDARDS.md？
- [ ] 接口是否符合 docs/INTERFACE_SPEC.md？
- [ ] 测试是否实际执行？（检查命令输出，不是口头说通过）
- [ ] PROJECT_STATUS.md 是否已更新？
- [ ] 是否引入了未经批准的依赖？
- [ ] 是否有破坏性操作（覆盖文件、删除测试）？

### M1 专项检查

- [ ] 视频文件和摄像头都能正常打开
- [ ] 人脸框在画面上正确显示
- [ ] FPS 数值合理（>10 FPS）
- [ ] q/Esc 退出后无残留进程

### M2 专项检查

- [ ] 标定 k 值合理（用已知距离验证）
- [ ] 保存/加载 calibration.json 正常
- [ ] 距离显示在 HUD 上
- [ ] 独立测试样本误差已记录

### M3 专项检查

- [ ] 坐姿分数在正常姿势下接近 1.0
- [ ] 亮度等级与实际画面明暗一致
- [ ] 异常跟踪有明确的触发时间和原因

### M4 专项检查

- [ ] 20-20-20 计时器用注入时钟测试（不等 20 分钟）
- [ ] 人脸丢失时间不计入有效用眼时间
- [ ] CSV 格式与 INTERFACE_SPEC.md 一致
- [ ] 暂停/恢复后计时器从正确位置继续

### M5 专项检查

- [ ] 报告包含所有统计项
- [ ] 空数据显示"数据不足"
- [ ] 图表正确渲染

### M6 专项检查

- [ ] 所有边界条件测试通过
- [ ] 无内存泄漏（长时间运行观察）
- [ ] 覆盖率报告已生成

### M7 专项检查

- [ ] 干净环境 clone + install + test 通过
- [ ] GitHub Actions 绿色
- [ ] 无敏感文件在仓库中

---

## 8. 问题上报格式

当 DSH 遇到阻塞问题时，要求它按以下格式报告：

```
### 阻塞问题报告

**问题描述**：[一句话描述]
**影响范围**：[影响哪个模块/功能]
**根本原因**：[分析原因]
**最小解决方案**：[提出最小改动方案]
**替代方案**：[如果有其他方案]
**对进度的影响**：[是否影响当前里程碑]
**需要你的决定**：[需要用户确认什么]
```

---

## 9. 快速参考

### 项目路径

```
~/projects/study_guard/     # 项目根目录
~/projects/study_guard/.venv/  # 虚拟环境
```

### 常用命令

```bash
# 激活环境
source .venv/bin/activate

# 运行全部测试
pytest tests/ -v

# 运行指定模块测试
pytest tests/test_calibrator.py -v

# 带覆盖率测试
pytest tests/ --cov=. --cov-report=term-missing

# 运行主程序（视频模式）
python main.py --source file --path path/to/video.mp4

# 运行主程序（摄像头模式）
python main.py --source camera --camera-index 0
```

### 关键文档速查

| 需要了解什么 | 读哪个文件 |
|-------------|-----------|
| 项目能做什么、不能做什么 | docs/PROJECT_SPEC.md |
| 如何约束 DSH | docs/PROJECT_RULES.md |
| 模块怎么组织 | docs/ARCHITECTURE.md |
| 函数签名和数据格式 | docs/INTERFACE_SPEC.md |
| 代码怎么写 | docs/CODING_STANDARDS.md |
| 测试怎么跑 | docs/TEST_PLAN.md |
| 为什么这样设计 | docs/DECISIONS.md |
| 当前做到哪了 | PROJECT_STATUS.md |
| 范围边界与负责人路线 | docs/OWNER_GUIDE.md |
| 还剩什么 | ROADMAP.md |
