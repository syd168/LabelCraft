# Changelog

All notable changes to LabelCraft are documented in this file.  
Newest releases first.

---

## [3.1.0] — 2026-08-09

### Summary

Rotated rectangles (OBB), richer export formats for segmentation, and a redesigned export dialog.

### Features

- **Rotated rectangle (OBB)** drawing tool (`R`): two-step edge → width; edit with move / corner scale / rotate handle
- Explicit **Convert to Polygon** for OBB (after convert: free vertices only, no rotate/scale)
- **YOLO OBB** export (`cls x1 y1 … x4 y4` + `data.yaml`)
- **YOLO Seg** export (polygon TXT + `data.yaml`)
- **COCO Segmentation** dataset export (`images/` + `annotations/instances_default.json`)
- Export dialog: default/editable destination path, wider two-column layout

### Improvements

- OBB class labels anchor to the visual top-left corner (not AABB)
- LabelCraft JSON export preserves OBB vertices (no longer rewritten as AABB)
- Existing **COCO** per-file export includes `segmentation` when polygon geometry exists

### Installation

```bash
pip install -U labelcraft==3.1.0
```

- GitHub: https://github.com/syd168/LabelCraft/releases/tag/v3.1.0
- PyPI: https://pypi.org/project/LabelCraft/3.1.0/

---

## [3.0.3] — 2026-08-08

### Summary

Preferences dialog, theme/language persistence, and JSON settings storage.

### Features

- **Edit → Preferences…** (`Ctrl+,`): language, theme (system / light / dark), annotation toggles, default box style
- Persist language and theme across sessions
- Default line/fill/width and “use fixed colors for new boxes”
- Annotation prefs: auto-save, single-class, display labels, force square drawing

### Improvements

- Settings migrate from pickle (`~/.labelcraftSettings.pkl`) to portable **JSON**
  - Linux: `~/.config/labelcraft/settings.json`
  - macOS: `~/Library/Application Support/LabelCraft/settings.json`
  - Windows: `%APPDATA%/LabelCraft/settings.json`
  - Override: `LABELCRAFT_CONFIG_DIR` or portable mode (`LABELCRAFT_PORTABLE=1` / `portable` marker)
- Dark theme polish (placeholder text / Mid colors)
- Display Labels: draw label text after fill so selection fill does not cover it
- Show RectBox: checkable toolbutton on beginner toolbar
- Safer polygon toggle when list items are stale after project close
- Pose toolbar icon update

### Installation

```bash
pip install -U labelcraft==3.0.3
```

- GitHub: https://github.com/syd168/LabelCraft/releases/tag/v3.0.3
- PyPI: https://pypi.org/project/LabelCraft/3.0.3/

---

## [3.0.2] — 2026-08-07

### Summary

Bug fix for shape style fill opacity.

### Changes

- Fix fill opacity at 100%: painting no longer clamps alpha ≥ 250 down to a near-transparent value
- Clarify Chinese UI label: **填充不透明度** (100% = fully opaque)

### Installation

```bash
pip install -U labelcraft==3.0.2
```

---

## [3.0.1] — 2026-08-07

### Summary

Documentation fix so the project screenshot renders on PyPI.

### Changes

- README / README-CN: screenshot uses an absolute GitHub raw URL
- PyPI cannot rewrite an already published `3.0.0` description; this patch refreshes the package long description

### Installation

```bash
pip install -U labelcraft==3.0.1
```

---

## [3.0.0] — 2026-08-07

### Summary

Major release: pose / multi-shape annotation, project-first workflow, polished desktop UX.

### Annotation tools

- **Pose** — bounding box + keypoints (YOLO-Pose style)
- **Polygon** — click vertices; close with double-click / Enter / first point
- **Ellipse** and **Circle** (`E` / `C`)
- **Shape style** — per-shape line / fill / width
- Auto-return to edit mode after drawing

### Project workflow

- Project file **`.lbc`** (legacy `.labelcraft` still supported)
- Detect vs pose tasks with keypoint configuration
- Import / export with progress; export LabelCraft JSON, YOLO Detect, YOLO Pose (+ VOC / CreateML / COCO / CSV where applicable)

### UI & UX

- Cleaner menus; Project Information panel
- Verified / unverified via completed-list context menu
- App icon on Linux / Windows taskbars
- Help dialogs as Markdown

### Internationalization

- Updated strings for new tools; languages: English, 简体中文, 繁體中文, 日本語, Deutsch, Français

### Breaking / notable

- Prefer project workflow (`File → New/Open Project`)
- Save annotation: **`Ctrl+S`**; save project: **`Ctrl+Alt+S`**
- Open project: **`Ctrl+O`**; export: **`Ctrl+Shift+E`**
- Primary extension: **`.lbc`**

### Installation

```bash
pip install -U labelcraft==3.0.0
labelcraft
```

---

## [2.1.7] — 2026-06-09

### Summary

macOS UI: remove large blank area below the bottom panel.

### Bug Fixes

- macOS dock panel: remove bottom stretch spacer
- macOS dock title bar: zero-height title bar widget
- macOS toolbar: align buttons to top; prevent vertical stretch

---

## [2.1.2] — 2026-05-01

### Summary

Cross-platform build and theme detection improvements.

### Improvements

- Unified PyInstaller builds for Windows / macOS / Linux
- Better path handling and system theme detection
- GitHub Actions builds for three platforms (Python 3.9–3.12)

---

## [2.1.0] — (see git history)

### Summary

Smart annotation import and stronger YOLO / i18n support.

### Highlights

- Import external annotations (YOLO, VOC, COCO, CreateML, CSV) with auto-detect
- YOLO `data.yaml` class names; clearer label-mapping warnings
- Import/export menu strings update on language switch

### Notes

- Import maps by **class ID** (project label order), not by source class name

---

Built on [labelImg](https://github.com/tzutalin/labelImg) by TzuTa Lin.
