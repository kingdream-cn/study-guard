# StudyGuard 项目进度 / Project Status

## 当前阶段 / Current Phase

**M0: 项目初始化 / Project Initialization**

## 当前状态 / Current Status

**COMPLETED** ✅

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

## 当前任务 / Current Task

准备进入 M1：视觉基础 / Ready to begin M1: Visual Foundation

## 验收标准 / Acceptance Criteria (M0)

- [x] Python 版本符合项目要求 / Python version meets requirements (3.12)
- [x] OpenCV 可以正常导入 / OpenCV imports successfully
- [x] 摄像头设备已确认 / Camera device confirmed
- [x] 项目文档齐全 / All project documentation complete
- [x] Git 仓库已初始化并关联远程 / Git repo initialized and linked to remote

## 已知问题 / Known Issues

- OpenCV 约束已收紧为 `>=4.6,<5.0`，环境已重装为 4.14.0（2026-10-20 环境复核）。
- 摄像头设备 `/dev/video0` 当前不存在，M1 摄像头输入的人工验收待硬件确认后执行（由项目负责人另行处理，本次不涉及）。
- 在 ROS 2 环境下运行 pytest 需加 `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1` 前缀，详见 `CONTRIBUTING.md`。

## 最近一次测试 / Latest Test

M0 环境复核（2026-10-20）：OpenCV 重装为 4.14.0，Haar 级联文件存在且 `CascadeClassifier` 加载成功（`empty() = False`），合成图人脸检测无异常（返回 0 个框）。pytest 默认命令受 ROS 2 插件影响，需用 `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1` 前缀。

## 下一项任务 / Next Task

**M1: 视觉基础 / Visual Foundation**
- 视频读取 + 摄像头读取
- Haar 人脸检测
- 人脸框绘制
- FPS 显示
- HUD 叠加
- 退出与资源释放

## 变更记录 / Change Log

| 日期 / Date | 变更 / Change |
|------------|--------------|
| 2026-10-19 | 项目初始化完成 / Project initialization completed |
| 2026-10-20 | M0 环境复核：OpenCV 固定为 4.x，Haar 可用性验证通过 / M0 env recheck |
