# LabelCraft - 智能图像标注工具

> **基于 [labelImg](https://github.com/tzutalin/labelImg) 开发的现代化图像标注工具**

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/)
[![PySide6](https://img.shields.io/badge/PySide6-6.5+-green.svg)](https://www.qt.io/)

LabelCraft 是一个现代化的图形化图像标注工具，支持在图像中标注对象边界框。它是图像分类、目标检测等深度学习任务的数据准备利器。

**本项目基于开源项目 [labelImg](https://github.com/tzutalin/labelImg) 进行二次开发和改进，感谢原作者 TzuTa Lin 的杰出贡献。**

## ✨ 特性

- 🎯 支持矩形框标注
- 📁 支持多种标注格式：
  - **PASCAL VOC** (XML格式)
  - **YOLO** (TXT格式)
  - **CreateML** (JSON格式)
  - **COCO** (JSON格式)
  - **CSV** (CSV格式)
- 🔄 统一标注转换器 - 5种格式互相转换
- 🌍 多语言支持（中文简体/繁体、英文、日文、德语、法语）
- 💡 亮度调节功能
- 🔍 缩放和平移
- ⚡ 快捷键支持
- 📋 预定义类别管理
- ✅ 标注验证功能
- 🚀 GitHub Actions自动化构建

## 📸 截图

![LabelImg Screenshot](resources/icons/app_screen.png)

## 🚀 快速开始

### 前置要求

- Python 3.8 或更高版本
- pip 包管理器

### 一键启动（推荐）

我们提供了跨平台的自动安装和启动脚本：

#### Linux/macOS
```bash
chmod +x start.sh
./start.sh
```

#### Windows
```bash
start.bat
```

脚本会自动：
1. 检查 Python 环境
2. 创建虚拟环境（venv）
3. 安装所有依赖
4. 编译资源文件
5. 启动 LabelCraft

### 从 PyPI 安装（最简单）

如果你只想使用 LabelCraft，不需要修改源码，可以直接从 PyPI 安装：

```bash
# 安装到当前 Python 环境
pip install labelcraft

# 或者安装到虚拟环境（推荐）
python -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate   # Windows
pip install labelcraft
```

安装完成后，可以直接运行：
```bash
labelcraft  # 直接启动图形界面
```

或者指定图像路径：
```bash
labelcraft /path/to/image.jpg
labelcraft /path/to/images/ /path/to/classes.txt /path/to/annotations/
```

**更新到最新版本：**
```bash
pip install --upgrade labelcraft
```

**卸载：**
```bash
pip uninstall labelcraft
```

### 手动安装

如果你更喜欢手动安装，可以按照以下步骤：

#### 1. 克隆仓库
```bash
git clone https://github.com/syd168/LabelCraft.git
cd LabelCraft
```

> **注意**: LabelCraft 基于 labelImg 开发，因此保留了相同的目录结构和启动方式。

#### 2. 创建并激活虚拟环境

**Linux/macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

#### 3. 安装依赖
```bash
pip install -r requirements.txt
```

#### 4. 编译资源文件
```bash
# Linux/macOS
make pyside6

# Windows
pyside6-rcc -o libs/resources.py resources.qrc
```

#### 5. 运行
```bash
python main.py  # 或 labelcraft（如果通过pip安装）
```

## 📖 使用说明

### 基本操作

1. **打开图像**: 点击左侧 "Open" 按钮或按 `Ctrl+O`
2. **选择保存目录**: 点击 "Change Save Dir" 设置标注文件保存位置
3. **创建标注框**: 点击 "Create RectBox" 或按 `W` 键，然后在图像上拖动
4. **输入标签**: 在弹出的对话框中输入对象类别
5. **保存标注**: 点击 "Save" 或按 `Ctrl+S`
6. **切换图像**: 使用 "Next Image" (`D`) 或 "Prev Image" (`A`)

### 常用快捷键

| 快捷键 | 功能 |
|--------|------|
| `Ctrl + O` | 打开图像文件 |
| `Ctrl + S` | 保存标注 |
| `Ctrl + R` | 更改默认保存目录 |
| `W` | 创建矩形框 |
| `D` | 下一张图像 |
| `A` | 上一张图像 |
| `Del` | 删除选中的标注框 |
| `Ctrl++` | 放大 |
| `Ctrl--` | 缩小 |
| `Ctrl + F` | 适应窗口 |
| `Ctrl + Shift + F` | 适应宽度 |
| `Z` | 撤销上一个操作 |

### 标注格式切换

在右侧面板可以选择不同的标注格式：
- **PascalVOC**: 生成 XML 文件，适用于大多数目标检测框架
- **YOLO**: 生成 TXT 文件，适用于 YOLO 系列模型
- **CreateML**: 生成 JSON 文件，适用于 Apple CreateML

### 预定义类别

编辑 `data/predefined_classes.txt` 文件，每行一个类别名称，可以在标注时快速选择：

```
cat
dog
person
car
```

## 🔧 高级配置

### 命令行参数

```bash
python main.py [IMAGE_PATH] [PRE-DEFINED CLASS FILE]
```

示例：
```bash
# 指定默认打开的图像
python main.py images/test.jpg

# 指定预定义类别文件
python main.py data/predefined_classes.txt

# 指定默认保存目录
python main.py images/ data/predefined_classes.txt annotations/

# 或使用命令行命令（如果通过pip安装）
labelcraft images/test.jpg
```

### 自定义设置

LabelCraft 会自动保存你的设置到系统配置文件中，包括：
- 最近打开的目录
- 窗口大小和位置
- 画笔颜色和粗细
- 默认标注格式

## 🛠️ 开发指南

### 项目结构

```
LabelCraft/
├── main.py              # 主程序入口
├── libs/                # 核心库
│   ├── canvas.py        # 画布组件
│   ├── shape.py         # 形状类
│   ├── labelFile.py     # 标注文件处理
│   ├── annotation_converter.py  # 统一标注转换器
│   ├── pascal_voc_io.py # VOC格式IO
│   ├── yolo_io.py       # YOLO格式IO
│   └── ...
├── resources/           # 资源文件
│   ├── icons/           # 图标
│   └── strings/         # 多语言字符串
├── data/                # 数据文件
│   └── predefined_classes.txt
├── build-tools/         # 构建脚本
└── .github/workflows/   # GitHub Actions配置
```

### 添加新语言

1. 在 `resources/strings/` 目录下创建新的语言文件
2. 复制 `strings.properties` 作为模板
3. 翻译所有字符串
4. 重新编译资源文件

```bash
# 编译资源文件
make pyside6
# 或
pyside6-rcc -o libs/resources.py resources.qrc
```

### 运行测试

```bash
python -m unittest discover tests
```

## 📦 编译与打包

### 本地打包

项目提供了跨平台的自动化构建脚本，位于 `build-tools/` 目录：

#### Linux 打包
```bash
cd build-tools
chmod +x build-linux.sh
./build-linux.sh
```
输出: `dist/linux_labelCraft_<version>.tar.gz`

#### Windows 打包（使用Wine交叉编译）
```bash
cd build-tools
chmod +x build-windows.sh
./build-windows.sh
```
输出: `dist/windows_labelCraft_<version>.zip`

**首次使用需要安装Wine和Windows Python:**
```bash
# 安装Wine
sudo apt install wine64

# 下载并安装Python for Windows
wget https://www.python.org/ftp/python/3.11.0/python-3.11.0-amd64.exe
wine python-3.11.0-amd64.exe
```

#### macOS 打包
```bash
cd build-tools
chmod +x build-macos.sh
./build-macos.sh
```
输出: `dist/macOS_labelCraft_<version>.zip` 和 `.dmg`

#### PyPI 包打包
```bash
cd build-tools
chmod +x build-pypi.sh
./build-pypi.sh
```
生成wheel和source distribution包。

详细构建说明请查看 [build-tools/README.md](build-tools/README.md)

## 🚀 发布与部署

### GitHub Actions 自动化发布（推荐）

本项目配置了完整的CI/CD流程，可以自动构建和发布：

#### 自动触发条件

- **每次Push**: 自动运行多平台测试（Ubuntu/Windows/macOS × Python 3.9-3.12）
- **创建Tag**: 自动构建所有平台可执行文件并发布到GitHub Releases

#### 发布新版本步骤

**Step 1: 更新版本号**

编辑 `libs/__init__.py`:
```python
__version__ = '1.0.0'  # 修改版本号
```

**Step 2: 提交并打标签**
```bash
git add libs/__init__.py
git commit -m "Bump version to 1.0.0"
git tag v1.0.0
git push origin main --tags
```

**Step 3: 等待自动构建**

访问 `https://github.com/syd168/LabelCraft/actions` 查看构建进度。

**Step 4: 下载发布版本**

构建完成后，访问:
- **GitHub Releases**: `https://github.com/syd168/LabelCraft/releases/tag/v1.0.0`
- 包含Linux、Windows、macOS三个平台的可执行文件

#### 配置PyPI自动发布（可选）

如需自动发布到PyPI:

1. 从 [pypi.org](https://pypi.org/manage/account/token/) 获取API Token
2. 在GitHub仓库设置中添加Secret:
   - Settings → Secrets and variables → Actions
   - 新建Repository secret
   - Name: `PYPI_API_TOKEN`
   - Value: 你的PyPI token

下次创建tag时会自动发布到PyPI。

### 手动触发构建

1. 访问GitHub仓库的 **Actions** 标签
2. 选择 **Build Releases** 工作流
3. 点击 **Run workflow**
4. 选择分支并运行

详细CI/CD说明请查看 [doc/打包说明.md](doc/打包说明.md)

## ❓ 常见问题

### Q: 启动时提示缺少模块？
A: 确保已安装所有依赖：
```bash
pip install -r requirements.txt
```

### Q: 中文显示乱码？
A: LabelCraft 支持 Unicode，确保系统字体支持中文显示。

### Q: 如何批量转换标注格式？
A: 使用 `tools/` 目录下的转换脚本，或编写自定义脚本读取一种格式并转换为另一种。

### Q: 标注文件保存在哪里？
A: 默认保存在与图像相同的目录，文件名与图像相同但扩展名不同（.xml, .txt, .json）。

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 🙏 致谢

- **[labelImg](https://github.com/tzutalin/labelImg)** - 原始项目，由 [TzuTa Lin](https://github.com/tzutalin) 创建
- 所有为 labelImg 和 LabelCraft 做出贡献的开发者

## 📮 联系方式

- 项目主页: https://github.com/syd168/LabelCraft
- 问题反馈: https://github.com/syd168/LabelCraft/issues

---

**Happy Labeling! 🎉**

---

**Happy Labeling! 🎉**
