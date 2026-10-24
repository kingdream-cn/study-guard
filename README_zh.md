# 明眸 StudyGuard

**基于 OpenCV 的桌面学习行为与用眼习惯辅助工具**

[English](README.md)

[![tests](https://github.com/kingdream-cn/study-guard/actions/workflows/tests.yml/badge.svg)](https://github.com/kingdream-cn/study-guard/actions/workflows/tests.yml)

---

## 项目简介

StudyGuard 通过摄像头或本地视频文件检测人脸，估算相对距离，评估坐姿和画面亮度，提供 20-20-20 护眼提醒和久坐提醒，并生成包含统计数据和图表的会话报告。

所有处理 **100% 在本地完成**——不会上传任何视频、图像或个人数据。

## 功能列表

### P0（MVP 必须完成）

- **人脸检测** — 基于 OpenCV Haar Cascade，实时显示人脸框
- **距离估算** — 三点标定，反比例模型
- **坐姿评分** — 基于人脸位置和大小的启发式评分
- **亮度监测** — 相对亮度等级（1–5）
- **20-20-20 提醒** — 每 20 分钟提醒远眺 20 秒
- **久坐提醒** — 可配置的久坐提醒间隔
- **会话日志** — CSV 格式，可配置记录间隔
- **会话报告** — 距离分布、坐姿统计、亮度统计、图表
- **双输入** — 本地视频文件和摄像头均为正式支持

### MVP 之后交付的能力（v0.2.x – v0.3.0）

- **检测参数真正生效** — `scale_factor`、`min_neighbors`、`min_face_size` 现在会驱动检测行为，
  不再只是「有校验、无消费者」的配置键
- **HUD 中文本地化** — 叠加层显示中文；日志、报告与 CSV 字段保持英文
- **方向化距离提醒** — 「过近」与「过远」各自独立冷却，一个方向不再把另一个方向静音一分钟
- **可执行的横幅文案** — 横幅直接告诉你该后退还是该靠近
- **按后端存储标定** — `k` 按检测后端分开保存；未标定的后端显示 `--`，
  绝不借用别的后端的 `k`
- **可选 YuNet 后端** — 见下

### 可选：YuNet 检测器后端（v0.3.0）

Haar Cascade 在小幅姿态变化下就会丢框。真机实测（同一座位同一机器，4 段姿势各约 10 秒，
丢框数 / 采样数）：

| 姿势 | Haar | YuNet |
|---|---|---|
| 正脸坐直 | 1/10 | 0/10 |
| 侧脸约 45° | 2/10 | 0/10 |
| **小幅低头** | **10/10（整段零检出）** | 1/10 |
| 刘海遮挡额头 | 7/10 | 1/8 |

因此 YuNet 是**已接通但不作为默认后端**，原因两条：`.onnx` 模型不随仓库分发；
标定常数与后端绑定——YuNet 量脸宽的方式和 Haar 不同，`k = 11488.3` 不能沿用
（见[算法说明](#距离估算)）。

启用方法：

```bash
mkdir -p ~/study_models
curl -L -o ~/study_models/face_detection_yunet_2023mar.onnx \
  https://github.com/opencv/opencv_zoo/raw/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx
```

然后把配置里的 `detection.backend` 改成 `"yunet"`，并重跑一次三点标定（按 `c` 三次、再按 `s`）。
在此之前，yunet 后端下距离读数为 `--`，其余功能正常。默认保持 Haar，是为了让新克隆的仓库
不下载任何模型就能直接跑。

## 安装

### 环境要求

- Python 3.10–3.12
- Ubuntu 24.04（主要平台），其他 Linux 发行版应可运行
- OpenCV 兼容摄像头（可选——视频文件同样可用）

### 安装步骤

```bash
# 克隆仓库
git clone https://github.com/kingdream-cn/study-guard.git
cd study-guard

# 创建并激活虚拟环境
python3 -m venv .venv
source .venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# （可选）安装开发依赖用于测试
pip install -r requirements-dev.txt
```

## 使用方法

### 视频文件模式

```bash
python main.py --source file --path path/to/video.mp4
```

### 摄像头模式

```bash
python main.py --source camera --camera-index 0
```

### 快捷键

| 按键 | 功能 |
|------|------|
| `q` / `Esc` | 退出并生成报告 |
| `Space` | 暂停 / 恢复 |
| `c` | 进入标定模式 |
| `s` | 保存标定数据 |
| `b` | 标定坐姿基线 |
| `r` | 重置会话 |

## 配置

所有参数在 `configs/default.json` 中。主要设置：

- `input.source` — `"file"`（视频文件）或 `"camera"`（摄像头）
- `distance.too_close_cm` — "距离过近"警告阈值（默认 30 cm）
- `reminder.eye_care_interval_min` — 20-20-20 间隔分钟数（默认 20）
- `reminder.sedentary_interval_min` — 久坐提醒间隔（默认 45 分钟）
- `logging.interval_sec` — CSV 日志写入间隔（默认 1.0 秒）
- `detection.backend` — `"haar"`（默认）或 `"yunet"`；`"yunet"` 需要本地模型文件并完成自己的标定
- `detection.model_path` — YuNet 模型位置（默认 `~/study_models/face_detection_yunet_2023mar.onnx`，
  **不随仓库分发**）
- `hud.language` — `"en"`（默认）或 `"zh"`，仅影响 HUD 叠加层

## 测试

```bash
# 激活虚拟环境
source .venv/bin/activate

# 运行全部测试
pytest tests/ -v

# 运行测试并生成覆盖率报告
pytest tests/ --cov=. --cov-report=term-missing
```

所有测试均不需要真实摄像头——使用合成视频数据和 mock 输入。

> 若 shell 已 source ROS 2（会设置 `PYTHONPATH`），请在测试命令前加
> `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1`，例如 `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest tests/ -v`。

## 算法说明与局限性

### 距离估算

距离通过人脸框宽度与距离的反比关系估算（`d = k / w`）。三点标定可在特定条件下改善精度，但**这不是精密测距**。结果受头部角度、检测器精度、分辨率和个体差异影响。

#### 实测精度（v0.1.0）

基于一次参考标定（`k = 11488.3`），以数据线直线（屏幕顶边 → 鼻尖，±2–3 cm 不确定度）为真值，
独立样本实测：

| 真值 | HUD 读数 | 相对误差 |
|---|---|---|
| 40 cm | 44–45 cm | +10–12% |
| 60 cm | 61–62 cm | +2–3% |

系统误差随距离增加而收敛；近距离对头部角度与姿势最敏感。该结果为相对估算，并非精密测距。

#### 标定常数与后端绑定

`k` 是从**特定检测器画出的脸宽**拟合出来的，因此不能跨后端沿用。真机同一坐姿下
YuNet/Haar 脸宽比为 0.771，而离线测试图上为 0.864——**比值不是常数**，所以不存在换算系数，
每个后端都必须各自重跑三点标定。标定数据在 `configs/calibration.json`：顶层 `k`/`samples`
是 Haar 的数据，其他后端放在 `backends.<name>` 下。没有对应条目的后端会在启动时报
`该后端尚未标定` 并把距离显示为 `--`，**绝不回落成别的后端的 `k`**。

#### 已知局限

- `too_close_cm = 30.0` 正落在 Haar 脸宽噪声带中段（同一姿势实测 143–430 px，对应 26.7–80.9 cm），
  所以"过近"告警具体在多少厘米触发会在这个区间内浮动。把它当作提醒，而不是精确阈值。
- `min_face_size`、`scale_factor`、`min_neighbors` 都会改变检出框本身，即它们都是测距的输入，
  不是无害过滤器。标定完成后不要再调它们。
- 背景里的对称图案（例如墙上的立方体 logo）仍可能被 Haar 误检为人脸；代码取最大框并对
  30 帧取中位数，能压过大部分情况。

完整记录见 [ALGORITHM_NOTES.md](docs/ALGORITHM_NOTES.md)（§8 调参实测、§10 缺陷记录、§11 后端对比）。

### 坐姿评分

坐姿评分是**启发式指标**，基于人脸位置和大小。无法可靠识别所有趴桌动作——仅能判断有限的疑似不良姿势。

### 亮度等级

亮度是**相对等级**（1–5），不是照度（lux）测量。摄像头自动曝光会改变画面亮度，因此只能反映趋势，不能反映绝对光照水平。

## 隐私说明

- 所有处理在本地完成，不上传任何数据
- 会话日志和报告存储在本地 `logs/` 和 `reports/` 目录
- 核心功能不需要网络连接

## 许可证

MIT 许可证。详见 [LICENSE](LICENSE)。

## 贡献

开发流程和编码规范见 [CONTRIBUTING.md](CONTRIBUTING.md)。

## 项目文档

| 文档 | 说明 |
|------|------|
| [PROJECT_SPEC.md](docs/PROJECT_SPEC.md) | 项目规格与功能边界 |
| [PROJECT_RULES.md](docs/PROJECT_RULES.md) | 开发规则（AI 助手主控提示词） |
| [ARCHITECTURE.md](docs/ARCHITECTURE.md) | 模块职责与数据流 |
| [INTERFACE_SPEC.md](docs/INTERFACE_SPEC.md) | 接口定义与数据格式 |
| [CODING_STANDARDS.md](docs/CODING_STANDARDS.md) | 编码规范 |
| [TEST_PLAN.md](docs/TEST_PLAN.md) | 按里程碑的测试方案 |
| [DECISIONS.md](docs/DECISIONS.md) | 架构决策记录 |
| [ALGORITHM_NOTES.md](docs/ALGORITHM_NOTES.md) | 算法细节与局限性 |
| [ROADMAP.md](ROADMAP.md) | 开发里程碑与时间表 |
| [PROJECT_STATUS.md](PROJECT_STATUS.md) | 当前进度 |
