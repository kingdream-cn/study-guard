# StudyGuard 项目进度 / Project Status

## 当前阶段 / Current Phase

**M1: 视觉基础 / Visual Foundation**

## 当前状态 / Current Status

**VERIFIED** ✅（自动化测试 10/10、代码审查、无窗验证与人工验收均通过）

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

## 当前任务 / Current Task

M2: 距离标定与估算（进行中）。

## 验收标准 / Acceptance Criteria (M0)

- [x] Python 版本符合项目要求 / Python version meets requirements (3.12)
- [x] OpenCV 可以正常导入 / OpenCV imports successfully
- [x] 摄像头设备已确认 / Camera device confirmed
- [x] 项目文档齐全 / All project documentation complete
- [x] Git 仓库已初始化并关联远程 / Git repo initialized and linked to remote

## 已知问题 / Known Issues

- DSH 执行沙箱无法访问项目负责人桌面上的 `/tmp/test_face.mp4` 与 `/dev/video0`（沙箱内两者均不存在），因此 M1 的「视频真实人脸」与「摄像头」两项人工验收需由项目负责人在桌面环境执行。
- 摄像头模式与视频文件缺失模式的错误处理已实测：退出码 1，并输出明确错误信息（`Failed to open camera device at index 0` / `Video file not found: ...`）。
- 在 ROS 2 环境下运行 pytest 需加 `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1` 前缀，详见 `CONTRIBUTING.md`。

## 最近一次测试 / Latest Test

M1（2026-10-20）：`PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest tests/ -v` → **10 passed**。端到端冒烟测试用合成视频（`/tmp/sg_synthetic.avi`）运行 `main.py --source file`，窗口正常打开、处理到 EOF 后干净退出（exit 0）。摄像头模式与缺失文件模式退出码均为 1 且错误信息清晰。

## 下一项任务 / Next Task

**M2: 距离标定与估算** —— calibrator.py（三点标定/最小二乘拟合 k/保存加载）、metrics.py 距离估算、hud 距离显示、main 标定流程、tests/test_calibrator.py。

## 变更记录 / Change Log

| 日期 / Date | 变更 / Change |
|------------|--------------|
| 2026-10-19 | 项目初始化完成 / Project initialization completed |
| 2026-10-20 | M0 环境复核：OpenCV 固定为 4.x，Haar 可用性验证通过 / M0 env recheck |
| 2026-10-20 | M1 视觉基础实现：capture/detector/hud/main + 测试，10 用例通过 / M1 implemented |
| 2026-10-20 | M1 验收通过，状态升级为 VERIFIED / M1 verified |
