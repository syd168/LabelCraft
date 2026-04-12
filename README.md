# LabelCraft - Intelligent Image Annotation Tool

> **A modern image annotation tool developed based on [labelImg](https://github.com/tzutalin/labelImg)**

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/)
[![PySide6](https://img.shields.io/badge/PySide6-6.5+-green.svg)](https://www.qt.io/)

**[中文文档](README-CN.md)** | **[English](README.md)**

LabelCraft is a modern graphical image annotation tool that supports annotating object bounding boxes in images. It's an essential tool for data preparation in deep learning tasks such as image classification and object detection.

**This project is a secondary development and improvement based on the open-source project [labelImg](https://github.com/tzutalin/labelImg). Special thanks to the original author TzuTa Lin for his outstanding contribution.**

## ✨ Features

- 🎯 Rectangle box annotation support
- 📁 Multiple annotation format support:
  - **PASCAL VOC** (XML format)
  - **YOLO** (TXT format)
  - **CreateML** (JSON format)
  - **COCO** (JSON format)
  - **CSV** (CSV format)
- 🔄 Unified annotation converter - Convert between 5 formats
- 🌍 Multi-language support (Simplified Chinese, Traditional Chinese, English, Japanese, German, French)
- 💡 Brightness adjustment
- 🔍 Zoom and pan
- ⚡ Keyboard shortcuts
- 📋 Predefined class management
- ✅ Annotation verification
- 🚀 GitHub Actions automated build

## 📸 Screenshot

![LabelCraft Screenshot](resources/icons/app_screen.png)

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- pip package manager

### One-Click Launch (Recommended)

We provide cross-platform automatic installation and launch scripts:

#### Linux/macOS
```bash
chmod +x start.sh
./start.sh
```

#### Windows
```bash
start.bat
```

The script will automatically:
1. Check Python environment
2. Create virtual environment (venv)
3. Install all dependencies
4. Compile resource files
5. Launch LabelCraft

### Manual Installation

If you prefer manual installation, follow these steps:

#### 1. Clone Repository
```bash
git clone https://github.com/syd168/LabelCraft.git
cd LabelCraft
```

> **Note**: LabelCraft is developed based on labelImg, so it retains the same directory structure and startup method.

#### 2. Create and Activate Virtual Environment

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

#### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

#### 4. Compile Resource Files
```bash
# Linux/macOS
make pyside6

# Windows
pyside6-rcc -o libs/resources.py resources.qrc
```

#### 5. Run
```bash
python main.py  # or labelcraft (if installed via pip)
```

## 📖 Usage Guide

### Basic Operations

1. **Open Image**: Click "Open" button on the left or press `Ctrl+O`
2. **Select Save Directory**: Click "Change Save Dir" to set annotation file save location
3. **Create Bounding Box**: Click "Create RectBox" or press `W`, then drag on the image
4. **Enter Label**: Type object category in the dialog box
5. **Save Annotation**: Click "Save" or press `Ctrl+S`
6. **Switch Images**: Use "Next Image" (`D`) or "Prev Image" (`A`)

### Common Shortcuts

| Shortcut | Function |
|----------|----------|
| `Ctrl + O` | Open image file |
| `Ctrl + S` | Save annotation |
| `Ctrl + R` | Change default save directory |
| `W` | Create rectangle box |
| `D` | Next image |
| `A` | Previous image |
| `Del` | Delete selected bounding box |
| `Ctrl++` | Zoom in |
| `Ctrl--` | Zoom out |
| `Ctrl + F` | Fit window |
| `Ctrl + Shift + F` | Fit width |
| `Z` | Undo last action |

### Annotation Format Switching

You can select different annotation formats in the right panel:
- **PascalVOC**: Generates XML files, suitable for most object detection frameworks
- **YOLO**: Generates TXT files, suitable for YOLO series models
- **CreateML**: Generates JSON files, suitable for Apple CreateML

### Predefined Classes

Edit the `data/predefined_classes.txt` file with one class name per line for quick selection during annotation:

```
cat
dog
person
car
```

## 🔧 Advanced Configuration

### Command Line Arguments

```bash
python main.py [IMAGE_PATH] [PRE-DEFINED CLASS FILE]
```

Examples:
```bash
# Specify default image to open
python main.py images/test.jpg

# Specify predefined classes file
python main.py data/predefined_classes.txt

# Specify default save directory
python main.py images/ data/predefined_classes.txt annotations/

# Or use command-line command (if installed via pip)
labelcraft images/test.jpg
```

### Custom Settings

LabelCraft automatically saves your settings to system configuration files, including:
- Recently opened directories
- Window size and position
- Brush color and thickness
- Default annotation format

## 🛠️ Development Guide

### Project Structure

```
LabelCraft/
├── main.py              # Main program entry
├── libs/                # Core libraries
│   ├── canvas.py        # Canvas component
│   ├── shape.py         # Shape class
│   ├── labelFile.py     # Annotation file handling
│   ├── annotation_converter.py  # Unified annotation converter
│   ├── pascal_voc_io.py # VOC format IO
│   ├── yolo_io.py       # YOLO format IO
│   └── ...
├── resources/           # Resource files
│   ├── icons/           # Icons
│   └── strings/         # Multi-language strings
├── data/                # Data files
│   └── predefined_classes.txt
├── build-tools/         # Build scripts
└── .github/workflows/   # GitHub Actions configuration
```

### Adding New Language

1. Create a new language file in `resources/strings/` directory
2. Copy `strings.properties` as template
3. Translate all strings
4. Recompile resource files

### Running Tests

```bash
python -m unittest discover tests
```

## ❓ FAQ

### Q: Missing modules when starting?
A: Ensure all dependencies are installed:
```bash
pip install -r requirements.txt
```

### Q: Chinese characters display incorrectly?
A: LabelCraft supports Unicode. Make sure your system fonts support Chinese character display.

### Q: How to batch convert annotation formats?
A: Use conversion scripts in the `tools/` directory, or write custom scripts to read one format and convert to another.

### Q: Where are annotation files saved?
A: By default, saved in the same directory as the image, with the same filename but different extension (.xml, .txt, .json).

## 🤝 Contributing

Issues and Pull Requests are welcome!

1. Fork this repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details

## 🙏 Acknowledgments

- **[labelImg](https://github.com/tzutalin/labelImg)** - Original project created by [TzuTa Lin](https://github.com/tzutalin)
- All developers who contributed to labelImg and LabelCraft

## 📮 Contact

- Project Homepage: https://github.com/syd168/LabelCraft
- Issue Tracker: https://github.com/syd168/LabelCraft/issues

---

**Happy Labeling! 🎉**
