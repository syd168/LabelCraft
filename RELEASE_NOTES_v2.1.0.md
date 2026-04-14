# Release Notes - v2.1.0

## 🎉 What's New

### ✨ Major Features

#### 1. Smart Annotation Import (New!)
- **Import external annotations** from existing datasets (YOLO, VOC, COCO, CreateML, CSV)
- **Auto-detect format** - Automatically identifies annotation format from directory structure
- **Smart label mapping** - Maps imported annotations to project-defined labels by class ID
- **YOLO data.yaml support** - Automatically reads and displays class names from YOLO datasets
- **Flexible import options**:
  - Copy images to project (optional)
  - Skip existing annotations (optional)
  - Batch import with progress tracking

#### 2. Enhanced YOLO Support
- **Intelligent directory detection** - Recognizes standard YOLO structures:
  - `dataset/data.yaml` + `images/` + `labels/`
  - Parent/grandparent directory scanning
  - Sibling directory detection (images/ ↔ labels/)
- **Automatic class name extraction** from data.yaml
- **Warning system** for label order mismatches between source and project

#### 3. Improved Internationalization
- **Fixed import menu translation** - Import/Export actions now properly update on language switch
- All UI elements fully translated across 6 languages:
  - English
  - 简体中文 (Simplified Chinese)
  - 繁體中文 (Traditional Chinese)
  - 日本語 (Japanese)
  - Deutsch (German)
  - Français (French)

### 🔧 Improvements

- **Better error handling** for PyYAML dependency
- **Enhanced format detection** with 6-layer YOLO structure analysis
- **Clearer user feedback** with detailed console logging during import
- **Improved confirmation dialogs** showing detected classes and mapping warnings

### 🐛 Bug Fixes

- Fixed import action not updating text when switching languages
- Fixed YOLO class ID to label name conversion
- Fixed auto-detection failure for YOLO datasets in nested directories
- Fixed label mapping priority (project labels now take precedence over source labels)

## 📦 Installation

### Via pip (Recommended)
```bash
pip install --upgrade labelcraft
```

### From Source
```bash
git clone https://github.com/syd168/LabelCraft.git
cd LabelCraft
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
pip install -r requirements.txt
python main.py
```

## 🔄 Migration Guide

### Upgrading from v2.0.x

No breaking changes! Your existing projects and annotations are fully compatible.

**New workflow tip:** Use the Import feature (`Ctrl+I`) to quickly bring in annotations from other datasets instead of manually converting formats.

## ⚠️ Important Notes

### Label Mapping Behavior

When importing annotations, the system maps by **class ID**, not by label name:

**Example:**
```
Source YOLO dataset:
  data.yaml names: [person, car, dog]
  
Your project labels:
  ['cat', 'bird', 'fish']

Result:
  class_id=0 → 'cat'    (NOT 'person')
  class_id=1 → 'bird'   (NOT 'car')
  class_id=2 → 'fish'   (NOT 'dog')
```

**Best Practice:** Ensure your project labels match the source dataset's label order before importing, or review imported annotations carefully.

## 📊 Statistics

- **Files changed:** 5
- **Lines added:** ~400
- **Languages supported:** 6
- **Formats supported:** 5 (VOC, YOLO, COCO, CreateML, CSV)

## 🙏 Acknowledgments

Special thanks to all users who provided feedback on the import functionality and helped identify edge cases in YOLO dataset structures.

---

**Full Changelog:** https://github.com/syd168/LabelCraft/compare/v2.0.4...v2.1.0
