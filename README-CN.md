# LabelCraft - 智能图像标注工具

> **版本 3.0.2** — 面向检测与姿态的项目化标注工具，基于 [labelImg](https://github.com/tzutalin/labelImg)

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/)
[![PySide6](https://img.shields.io/badge/PySide6-6.5+-green.svg)](https://www.qt.io/)
[![Version](https://img.shields.io/badge/version-3.0.2-orange.svg)](https://github.com/syd168/LabelCraft/releases)
[![Downloads](https://pepy.tech/badge/labelcraft)](https://pepy.tech/project/labelcraft)
[![PyPI](https://img.shields.io/pypi/v/labelcraft.svg)](https://pypi.org/project/LabelCraft/)

**[中文文档](README-CN.md)** | **[English](README.md)**

LabelCraft 是一款图形化图像标注工具，支持项目管理、多种几何形状，以及 YOLO-Pose 关键点标注。本项目是 [labelImg](https://github.com/tzutalin/labelImg) 的重大演进，感谢原作者 TzuTa Lin。

## 3.0 亮点

- **标注形状**：矩形、姿态（框 + 关键点）、多边形、椭圆、圆形
- **项目管理**：主扩展名 `.lbc`（兼容旧版 `.labelcraft`），检测 / 姿态任务
- **导入导出**：LabelCraft JSON、YOLO Detect、YOLO Pose、PASCAL VOC、CreateML、COCO、CSV
- **工作流**：待标注队列、已完成列表、验证状态、自动保存、默认标签
- **界面**：项目信息面板、精简菜单与快捷键、任务栏应用图标
- **多语言**：英文、简体中文、繁體中文、日语、德语、法语（运行时切换）

## 截图

![LabelCraft Interface](https://raw.githubusercontent.com/syd168/LabelCraft/main/resources/icons/app_screen.png)

## 安装

### pip（推荐）

```bash
pip install -U labelcraft
labelcraft
```

### 源码运行

```bash
git clone https://github.com/syd168/LabelCraft.git
cd LabelCraft
python3 -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
pyside6-rcc -o libs/resources.py resources.qrc   # 修改图标后需要
python main.py
```

也可使用 `./start.sh`（Linux/macOS）或 `start.bat`（Windows）。

## 推荐流程

1. **文件 → 新建项目**（`Ctrl+N`）— 名称、位置、标签，检测或姿态
2. 将图片 / 文件夹加入 **待标注** 队列
3. 使用 **W**（矩形）、**P**（姿态）、**G**（多边形）、**E**（椭圆）、**C**（圆）绘制
4. **Ctrl+S** 保存标注 · **Ctrl+Alt+S** 保存项目
5. **数据 → 导出…**（`Ctrl+Shift+E`）

项目文件为 **`{名称}.lbc`**，标注保存在 `{项目目录}/annotations/`。

## 常用快捷键

| 快捷键 | 功能 |
|--------|------|
| `Ctrl+N` / `Ctrl+O` | 新建 / 打开项目 |
| `Ctrl+Alt+E` / `Ctrl+Alt+S` | 编辑 / 保存项目 |
| `Ctrl+S` | 保存标注 |
| `Ctrl+I` / `Ctrl+Shift+E` | 导入 / 导出 |
| `W` `P` `G` `E` `C` | 矩形 / 姿态 / 多边形 / 椭圆 / 圆 |
| `Ctrl+E` | 编辑标签 |
| `Delete` / `Ctrl+D` / `Ctrl+Z` | 删除 / 复制 / 撤销 |
| `Ctrl+V` | 复制上一张图标注 |
| `V` | 验证当前图 |
| `A` / `D` | 上一张 / 下一张 |
| `Ctrl+F` / `Ctrl+Shift+F` | 适应窗口 / 适应宽度 |

完整列表见应用内 **帮助 → 快捷键**。

## 目录结构

```
LabelCraft/
├── main.py              # 入口
├── labelcraft_ui.py     # 主界面
├── libs/                # 核心库（项目、画布、读写、国际化等）
├── resources/           # 图标与资源
├── requirements.txt
└── setup.py             # PyPI 打包
```

## 开发说明

- Python **3.8+**，依赖 **PySide6 ≥ 6.5**、**lxml**
- 语言包：`libs/locales/*.json`
- 修改 `resources.qrc` 后重新编译：  
  `pyside6-rcc -o libs/resources.py resources.qrc`

## 更新说明（3.0.2）

- 修复选框样式：填充不透明度 100% 不再被压成近似透明

## 更新说明（3.0.1）

- PyPI 项目页截图改为 GitHub 绝对链接，可在 pypi.org 正常显示

## 更新说明（3.0.0）

详见 [RELEASE_NOTES_v3.0.0.md](RELEASE_NOTES_v3.0.0.md)。

## 许可证

MIT — 见 [LICENSE](LICENSE)。

## 致谢

- [labelImg](https://github.com/tzutalin/labelImg)（TzuTa Lin）
- LabelCraft 的贡献者与用户
