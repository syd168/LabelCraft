# LabelCraft - Intelligent Image Annotation Tool

> **Version 3.1.0** — Project-first annotation for detection, pose, OBB & segmentation, based on [labelImg](https://github.com/tzutalin/labelImg)

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/)
[![PySide6](https://img.shields.io/badge/PySide6-6.5+-green.svg)](https://www.qt.io/)
[![Version](https://img.shields.io/badge/version-3.1.0-orange.svg)](https://github.com/syd168/LabelCraft/releases)
[![Downloads](https://pepy.tech/badge/labelcraft)](https://pepy.tech/project/labelcraft)
[![PyPI](https://img.shields.io/pypi/v/labelcraft.svg)](https://pypi.org/project/LabelCraft/)

**[中文文档](README-CN.md)** | **[English](README.md)**

LabelCraft is a graphical image annotation tool with project management, multi-shape drawing, and YOLO-Pose support. It is a major evolution of [labelImg](https://github.com/tzutalin/labelImg) — thanks to TzuTa Lin for the original work.

## Highlights (v3.0)

- **Shapes**: rectangle, pose (bbox + keypoints), polygon, ellipse, circle
- **Projects**: `.lbc` project files (legacy `.labelcraft` still opens), detect / pose tasks
- **Import / Export**: LabelCraft JSON, YOLO Detect, YOLO Pose, PASCAL VOC, CreateML, COCO, CSV
- **Workflow**: pending queue, completed list, verify status, auto-save, default label
- **UI**: compact project info panel, cleaned menus & shortcuts, taskbar app icon
- **i18n**: English, 简体中文, 繁體中文, 日本語, Deutsch, Français (live switch)

## Screenshot

![LabelCraft Interface](https://raw.githubusercontent.com/syd168/LabelCraft/main/resources/icons/app_screen.png)

## Install

### pip (recommended)

```bash
pip install -U labelcraft
labelcraft
```

### From source

```bash
git clone https://github.com/syd168/LabelCraft.git
cd LabelCraft
python3 -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
pyside6-rcc -o libs/resources.py resources.qrc   # if you change icons
python main.py
```

Or use `./start.sh` (Linux/macOS) / `start.bat` (Windows).

## Quick workflow

1. **File → New Project** (`Ctrl+N`) — name, location, labels, detect or pose
2. Add images / folders into the **pending** queue
3. Draw with **W** (rect), **P** (pose), **G** (polygon), **E** (ellipse), **C** (circle)
4. **Ctrl+S** save annotation · **Ctrl+Alt+S** save project
5. **Data → Export…** (`Ctrl+Shift+E`) when ready

Project files use **`{name}.lbc`**. Annotations live under `{project_dir}/annotations/`.

## Keyboard shortcuts (common)

| Shortcut | Action |
|----------|--------|
| `Ctrl+N` / `Ctrl+O` | New / Open project |
| `Ctrl+Alt+E` / `Ctrl+Alt+S` | Edit / Save project |
| `Ctrl+S` | Save annotation |
| `Ctrl+I` / `Ctrl+Shift+E` | Import / Export |
| `W` `P` `G` `E` `C` | Rect / Pose / Poly / Ellipse / Circle |
| `Ctrl+E` | Edit label |
| `Delete` / `Ctrl+D` / `Ctrl+Z` | Delete / Duplicate / Undo |
| `Ctrl+V` | Copy previous image boxes |
| `V` | Verify current image |
| `A` / `D` | Prev / Next image |
| `Ctrl+F` / `Ctrl+Shift+F` | Fit window / Fit width |

See **Help → Shortcuts** in the app for the full list.

## Project layout

```
LabelCraft/
├── main.py              # Entry
├── labelcraft_ui.py     # Main window
├── libs/                # Core (project, canvas, I/O, i18n, …)
├── resources/           # Icons & assets
├── requirements.txt
└── setup.py             # PyPI packaging
```

## Development notes

- Python **3.8+**, dependency: **PySide6 ≥ 6.5**, **lxml**
- Locales: `libs/locales/*.json`
- After editing `resources.qrc`, recompile:  
  `pyside6-rcc -o libs/resources.py resources.qrc`

## Changelog

Latest highlights (**3.1.0**): Rotated rectangles (OBB), YOLO OBB / YOLO Seg / COCO Seg export, redesigned export dialog.

Full history: [CHANGELOG.md](CHANGELOG.md).

## License

MIT — see [LICENSE](LICENSE).

## Acknowledgments

- [labelImg](https://github.com/tzutalin/labelImg) by TzuTa Lin
- Contributors and users of LabelCraft
