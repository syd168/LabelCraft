# LabelCraft - 智能图像标注工具

> **版本 2.0.0** - 具备项目管理功能的现代化图像标注工具，基于 [labelImg](https://github.com/tzutalin/labelImg) 开发

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/)
[![PySide6](https://img.shields.io/badge/PySide6-6.5+-green.svg)](https://www.qt.io/)
[![Version](https://img.shields.io/badge/version-2.0.0-orange.svg)](https://github.com/syd168/LabelCraft/releases)
[![Downloads](https://pepy.tech/badge/labelcraft)](https://pepy.tech/project/labelcraft)

**[中文文档](README-CN.md)** | **[English](README.md)**

LabelCraft 是一款专业的图形化图像标注工具，具备先进的项目管理能力。专为深度学习任务（如目标检测、图像分类）的数据准备而设计。

**本项目是开源项目 [labelImg](https://github.com/tzutalin/labelImg) 的重大演进版本，新增了基于项目的工作流、多格式支持和智能标注功能。特别感谢原作者 TzuTa Lin 的开创性工作。**

## ✨ 核心特性

### 🎯 基础标注
- 矩形边界框标注
- 多边形标注（即将推出）
- 实时预览和编辑
- 撤销/重做支持

### 📁 项目管理 (v2.0 新增!)
- 创建和管理标注项目
- 项目配置持久化 (.labelcraft 文件)
- 最近项目快速访问
- 自动标注目录管理
- 项目元数据跟踪

### 🔄 多格式支持
支持5种主流标注格式，无缝转换：
- **PASCAL VOC** (XML) - 传统格式，适用于 Faster R-CNN、SSD 等
- **YOLO** (TXT) - 适用于 YOLO 系列模型 (v5, v8, v10)
- **CreateML** (JSON) - 适用于 Apple CreateML 框架
- **COCO** (JSON) - Microsoft COCO 数据集标准
- **CSV** (CSV) - 通用数据分析格式

### 🌐 高级国际化
无需重启即可动态切换语言：
- English (英语)
- 简体中文
- 繁體中文
- 日本語 (日语)
- Deutsch (德语)
- Français (法语)

### ⚡ 智能工作流
- 待标注队列管理
- 已标注列表
- 自动保存模式
- 批量标注默认标签
- 验证模式进行质量控制
- 复制前一帧标注

### 🛠️ 开发者工具
- 内置格式转换器（支持全部5种格式）
- 命令行界面
- Python API 集成
- 可自定义快捷键
- 亮度调节

## 📸 界面截图

![LabelCraft 界面](resources/icons/app_screen.png)

## 🚀 快速开始

### 通过 pip 安装（推荐）

```bash
pip install labelcraft
```

从命令行启动：
```bash
labelcraft
```

或指定图像目录：
```bash
labelcraft /path/to/images
```

### 一键启动（从源码）

**Linux/macOS:**
```bash
chmod +x start.sh
./start.sh
```

**Windows:**
```bash
start.bat
```

脚本将自动：
1. 检查 Python 环境
2. 创建虚拟环境
3. 安装依赖
4. 编译资源
5. 启动应用

### 手动安装

```bash
# 克隆仓库
git clone https://github.com/syd168/LabelCraft.git
cd LabelCraft

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# 或
venv\Scripts\activate     # Windows

# 安装依赖
pip install -r requirements.txt

# 编译资源 (Linux/macOS)
make pyside6
# 或 Windows
pyside6-rcc -o libs/resources.py resources.qrc

# 运行
python main.py
```

## 📖 使用指南

### 标准工作流程（基于项目）

#### 步骤 1: 创建新项目

1. 菜单：`文件 → 新建项目` 或按 `Ctrl+N`
2. 填写项目信息：
   - **项目名称**: 你的项目名称
   - **项目位置**: 存储项目文件的目录
   - **输出格式**: 选择标注格式 (VOC/YOLO/CreateML/COCO/CSV)
   - **标签**: 添加你的对象类别
3. 点击"创建项目"

系统将自动创建：
- 项目文件：`{project_name}.labelcraft`
- 标注目录：`{project_dir}/annotations/`

#### 步骤 2: 添加图像到项目

1. 菜单：`文件 → 打开目录` 或按 `Ctrl+U`
2. 选择包含图像的目录
3. 图像将加载到待标注队列

你也可以：
- 直接拖放图像
- 使用 `文件 → 添加图像` 添加特定文件

#### 步骤 3: 标注图像

1. 点击"创建矩形框"按钮或按 `W`
2. 在对象上绘制边界框
3. 输入标签名称（或使用默认标签）
4. 按 Enter 确认
5. 使用 `Ctrl+S` 保存或启用自动保存

**技巧：**
- 使用方向键微调框位置
- 绘制时按住 `Ctrl` 获得完美正方形
- 右键点击框编辑属性
- 使用验证模式（空格键）标记已完成图像

#### 步骤 4: 管理标注

**查看状态：**
- 左侧面板：待标注图像队列
- 右侧面板：当前图像标注
- 窗口标题显示进度：`(5/100)`

**导航：**
- 下一张图像：`D` 或 `→`
- 上一张图像：`A` 或 `←`
- 从文件列表跳转到特定图像

#### 步骤 5: 导出与转换

**导出标注：**
- 菜单：`文件 → 导出标注`
- 选择导出位置和格式

**转换格式：**
以编程方式使用内置转换器：

```python
from libs.annotation_converter import AnnotationConverter

converter = AnnotationConverter()

# 将整个项目从 VOC 转换为 YOLO
converter.convert(
    input_dir='path/to/voc_annotations',
    input_format='voc',
    output_format='yolo',
    output_dir='path/to/yolo_output'
)
```

或通过命令行：
```bash
python -m libs.annotation_converter \
    --input /path/to/input \
    --input_format voc \
    --output_format yolo \
    --output /path/to/output
```

### 传统模式（快速标注）

对于不需要项目管理的简单任务：

```bash
# 打开单个图像
python main.py image.jpg

# 直接打开目录
python main.py /path/to/images

# 使用预定义标签
python main.py /path/to/images data/predefined_classes.txt
```

## ⌨️ 快捷键

### 文件操作
| 快捷键 | 操作 |
|--------|------|
| `Ctrl+N` | 新建项目 |
| `Ctrl+O` | 打开项目 |
| `Ctrl+U` | 打开目录 |
| `Ctrl+S` | 保存标注 |
| `Ctrl+E` | 编辑项目 |
| `Ctrl+Shift+C` | 关闭项目 |

### 标注操作
| 快捷键 | 操作 |
|--------|------|
| `W` | 创建矩形框 |
| `Ctrl+J` | 编辑模式 |
| `Delete` | 删除选中框 |
| `Ctrl+D` | 复制框 |
| `Ctrl+V` | 复制前一帧 |
| `Space` | 验证图像 |

### 导航
| 快捷键 | 操作 |
|--------|------|
| `D` / `→` | 下一张图像 |
| `A` / `←` | 上一张图像 |
| `Ctrl++` | 放大 |
| `Ctrl+-` | 缩小 |
| `Ctrl+F` | 适应窗口 |
| `Ctrl+Shift+F` | 适应宽度 |

### 视图
| 快捷键 | 操作 |
|--------|------|
| `Ctrl+T` | 切换工具栏 |
| `Ctrl+H` | 隐藏所有框 |
| `Ctrl+A` | 显示所有框 |
| `Ctrl+Shift++` | 增加亮度 |
| `Ctrl+Shift+-` | 降低亮度 |
| `Ctrl+Shift+=` | 重置亮度 |

## 🔧 高级配置

### 预定义标签

创建一个文本文件，每行一个标签：

```txt
person
car
dog
cat
bicycle
```

启动时加载：
```bash
python main.py data/predefined_classes.txt
```

或在运行时：`文件 → 加载预定义类别` (`Ctrl+Shift+L`)

### 自定义设置

设置会自动保存到系统配置：
- 最近使用的目录
- 窗口大小和位置
- 默认标注格式
- 画笔颜色
- 语言偏好

### 命令行参数

```bash
python main.py [IMAGE_PATH] [PREDEFINED_CLASSES] [SAVE_DIR]
```

示例：
```bash
# 打开特定图像
python main.py images/test.jpg

# 使用预定义类别
python main.py images/ data/classes.txt

# 指定保存目录
python main.py images/ classes.txt annotations/
```

## 🏗️ 项目结构

```
LabelCraft/
├── main.py                 # 应用程序入口
├── labelcraft_ui.py        # 主 UI 实现
├── libs/                   # 核心库
│   ├── project.py          # 项目管理
│   ├── canvas.py           # 绘图画布
│   ├── shape.py            # 形状类
│   ├── annotation_converter.py  # 格式转换器
│   ├── i18n_engine.py      # 国际化引擎
│   ├── pascal_voc_io.py    # VOC 格式 I/O
│   ├── yolo_io.py          # YOLO 格式 I/O
│   ├── create_ml_io.py     # CreateML I/O
│   ├── coco_io.py          # COCO I/O
│   └── csv_io.py           # CSV I/O
├── locales/                # 翻译文件
│   ├── en.json
│   ├── zh-CN.json
│   ├── zh-TW.json
│   ├── ja-JP.json
│   ├── de-DE.json
│   └── fr-FR.json
├── resources/              # 图标和资源
├── doc/                    # 文档
│   ├── tutorial.md
│   ├── tutorial_zh-CN.md
│   └── TRANSLATION_GUIDE.md
└── build-tools/            # 构建脚本
```

## 🌍 添加新语言

1. 在 `locales/` 中创建新文件（例如 `es-ES.json`）
2. 复制现有 JSON 作为模板
3. 翻译所有值（保持键不变）
4. 重启应用 - 新语言会被自动检测

详见 [TRANSLATION_GUIDE.md](doc/TRANSLATION_GUIDE.md)。

## ❓ 常见问题

### Q: v1.x 和 v2.0 有什么区别？

**A:** 2.0 版本引入了：
- ✅ 基于项目的工作流（vs v1.x 的基于文件）
- ✅ 支持 COCO 和 CSV 格式
- ✅ 内置格式转换器
- ✅ 动态语言切换
- ✅ 增强的 UI 和更好的组织
- ✅ 改进的标注管理

### Q: 我可以不创建项目直接使用吗？

**A:** 可以！你可以通过直接打开目录使用传统模式。但是，项目提供更好的组织和持久化。

### Q: 如何转换现有的标注？

**A:** 使用内置转换器：

```python
from libs.annotation_converter import AnnotationConverter

converter = AnnotationConverter()
converter.convert('old_annotations/', 'voc', 'yolo', 'new_annotations/')
```

### Q: 我的标注保存在哪里？

**A:** 
- **使用项目时**: 在 `{project_dir}/annotations/`
- **不使用项目**: 与图像相同目录
- 文件名与图像匹配，扩展名适当 (.xml, .txt, .json, .csv)

### Q: 我可以在项目进行中更改输出格式吗？

**A:** 可以！编辑项目 (`Ctrl+E`) 并更改格式。如果需要，现有标注将被迁移。

### Q: 如何备份我的项目？

**A:** 只需复制整个项目目录，包括：
- `.labelcraft` 项目文件
- `annotations/` 目录
- 你的图像（如果存储在项目内）

### Q: 有用于编程使用的 API 吗？

**A:** 有！你可以将 LabelCraft 集成到你的 Python 代码中：

```python
from libs.project import Project
from libs.annotation_converter import AnnotationConverter

# 创建项目
project = Project(name="MyProject", project_dir="/path/to/project")
project.save("/path/to/project/myproject.labelcraft")

# 转换格式
converter = AnnotationConverter()
converter.convert("input/", "voc", "yolo", "output/")
```

## 🤝 贡献指南

欢迎贡献！请遵循以下步骤：

1. Fork 本仓库
2. 创建特性分支：`git checkout -b feature/amazing-feature`
3. 提交更改：`git commit -m 'Add amazing feature'`
4. 推送到分支：`git push origin feature/amazing-feature`
5. 开启 Pull Request

### 开发环境设置

```bash
# 克隆和设置
git clone https://github.com/syd168/LabelCraft.git
cd LabelCraft
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 运行测试
python -m pytest tests/

# UI 更改后编译资源
pyside6-rcc -o libs/resources.py resources.qrc
```

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件。

## 🙏 致谢

- **[labelImg](https://github.com/tzutalin/labelImg)** - 由 [TzuTa Lin](https://github.com/tzutalin) 创建的原始项目
- 所有改进 LabelCraft 的贡献者
- 提供灵感和支持的开源社区

## 📮 联系与支持

- **项目主页**: https://github.com/syd168/LabelCraft
- **问题追踪**: https://github.com/syd168/LabelCraft/issues
- **文档**: 查看 `doc/` 目录
- **邮箱**: syd168@users.noreply.github.com

---

**祝您标注愉快！🎉**

*为计算机视觉社区用心制作 ❤️*
