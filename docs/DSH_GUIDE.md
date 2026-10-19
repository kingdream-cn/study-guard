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
python main.py --input file --video path/to/video.mp4

# 运行主程序（摄像头模式）
python main.py --input camera --camera-index 0
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
| 还剩什么 | ROADMAP.md |
