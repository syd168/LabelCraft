# Release v3.0.0

**Release Date**: 2026-08-07

## Summary

LabelCraft **3.0** is a major release focused on pose / multi-shape annotation, a cleaner project-first workflow, and a polished desktop experience on Linux and Windows.

## Highlights

### Annotation tools
- **Pose annotation** — bounding box + keypoints for YOLO-Pose style projects
- **Polygon** — click vertices; close with double-click / Enter / first point
- **Ellipse** and **Circle** — dedicated tools (`E` / `C`)
- **Shape style** — per-shape line / fill / width
- Auto-return to edit mode after drawing

### Project workflow
- Project file extension **`.lbc`** (legacy `.labelcraft` still supported)
- Detect vs pose project tasks with keypoint configuration
- Import / export dialogs with progress and clearer results
- Export: LabelCraft JSON, YOLO Detect, YOLO Pose (and existing VOC / CreateML / COCO / CSV paths where applicable)

### UI & UX
- Menus trimmed (legacy open/format clutter removed; shortcuts cleaned up)
- Right panel: **Project Information** (short project path + open-in-file-manager)
- Verified / unverified via completed-list context menu (status bar feedback)
- Application icon on Linux / Windows taskbars
- Help dialogs (tutorial / shortcuts / about) as Markdown

### Internationalization
- Updated strings for new tools, export, pose tips, and project UI
- Languages: English, 简体中文, 繁體中文, 日本語, Deutsch, Français

## Installation

### PyPI
```bash
pip install -U labelcraft==3.0.0
labelcraft
```

### From source
```bash
git clone https://github.com/syd168/LabelCraft.git
cd LabelCraft
git checkout v3.0.0
pip install -r requirements.txt
python main.py
```

### Quick start scripts
- Linux/macOS: `./start.sh`
- Windows: `start.bat`

## Breaking / notable changes

- Prefer **project-based** workflow (`File → New/Open Project`) over legacy open-directory menus
- Annotation save shortcut: **`Ctrl+S`**; save project: **`Ctrl+Alt+S`**
- Open project: **`Ctrl+O`**; export: **`Ctrl+Shift+E`**
- Primary project extension is **`.lbc`**

## Thanks

Built on the foundation of [labelImg](https://github.com/tzutalin/labelImg) by TzuTa Lin.
