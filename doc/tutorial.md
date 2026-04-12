# LabelCraft User Tutorial

> **An image annotation tool developed based on [labelImg](https://github.com/tzutalin/labelImg)**

## 📖 Table of Contents

1. [Quick Start](#quick-start)
2. [Interface Overview](#interface-overview)
3. [Basic Operations](#basic-operations)
4. [Advanced Features](#advanced-features)
5. [Keyboard Shortcuts](#keyboard-shortcuts)
6. [FAQ](#faq)

---

## Quick Start

### Launch Application

**Linux/macOS:**
```bash
./start.sh
```

**Windows:**
```bash
start.bat
```

**Or run directly:**
```bash
python main.py
```

> **Tip**: LabelCraft is developed based on labelImg and retains the original command-line startup method.

### First Time Use

1. **Open Image**: Click `File → Open` or press `Ctrl+O`
2. **Create Bounding Box**: Click the "Create RectBox" button on the toolbar or press `W`
3. **Enter Label**: Type the object category name in the dialog box
4. **Save Annotation**: Click `File → Save` or press `Ctrl+S`

---

## Interface Overview

### Main Interface Layout

```
┌─────────────────────────────────────────────┐
│  Menu Bar (File/Edit/View/Language/Help)     │
├──────────┬──────────────────────┬───────────┤
│          │                      │           │
│ Toolbar  │                      │ Bounding  │
│          │   Image Display      │ Box List  │
│          │       Area           │           │
│          │                      │ □ Use     │
│          │                      │   Default │
│          │                      │   Label   │
│          │                      │           │
│          │                      │ □ Mark as │
│          │                      │  Difficult│
│          │                      │           │
├──────────┴──────────────────────┴───────────┤
│  Status Bar (Shows current status and tips)  │
└─────────────────────────────────────────────┘
```

### Right Panel Description

#### Bounding Box List
- Displays all created bounding boxes in the current image
- Each box has a checkbox to control visibility
- Double-click to edit label name
- Right-click to delete or edit

#### Use Default Label
- When checked, no label input dialog appears when creating new boxes
- Automatically uses the label selected in the dropdown
- Ideal for batch annotating objects of the same category

#### Mark as Difficult
- Marks objects that are hard to identify or uncertain
- Adds `<difficult>1</difficult>` to the XML file after saving
- Can choose to exclude these samples during training

---

## Basic Operations

### 1. Open Images

**Single Image:**
- Menu: `File → Open`
- Shortcut: `Ctrl+O`
- Supported formats: JPG, PNG, BMP, TIFF, etc.

**Entire Folder:**
- Menu: `File → Open Dir`
- Shortcut: `Ctrl+U`
- Automatically loads all images in the directory

### 2. Create Bounding Boxes

**Steps:**
1. Ensure you're in "Create Mode" (first toolbar button is highlighted)
2. Click and drag on the image with left mouse button
3. Release mouse and enter label name
4. Press Enter to confirm

**Tips:**
- Hold `Ctrl` key to draw perfect squares
- Use arrow keys to fine-tune box position
- Use mouse wheel to zoom in/out

### 3. Edit Bounding Boxes

**Move Box:**
- Switch to "Edit Mode" (shortcut `Ctrl+J`)
- Drag the box to a new position

**Resize:**
- In edit mode, drag edges or corners of the box

**Modify Label:**
- Double-click the label name in the box list
- Or double-click the box on the canvas

**Delete Box:**
- Select and press `Delete` key
- Or right-click in the list and select delete

### 4. Save Annotations

**Save Formats:**
- PASCAL VOC (XML) - Default format
- YOLO (TXT) - For YOLO model training
- CreateML (JSON) - For Apple CreateML

**Switch Format:**
- Menu: `File → Change Save Format`
- Shortcut: `Ctrl+Y`

**Auto Save:**
- Menu: `View → Auto Save Mode`
- When enabled, automatically saves when switching to next image

---

## Advanced Features

### 1. Load Predefined Labels

**Why Use It:**
- Avoid manual label entry each time
- Ensure label name consistency
- Improve annotation efficiency

**How to Use:**

**Method 1: Specify at Startup**
```bash
python main.py data/predefined_classes.txt
```

**Method 2: Load at Runtime**
- Menu: `File → Load Predefined Classes`
- Shortcut: `Ctrl+Shift+L`
- Select a text file containing label list

**File Format:**
```txt
person
car
dog
cat
```
One label per line, supports both Chinese and English.

### 2. Copy Previous Frame Annotations

**Use Cases:**
- Video frame annotation
- Consecutive images where object positions don't change much

**Operation:**
- Menu: `File → Copy Previous Bounding Boxes`
- Shortcut: `Ctrl+V`

### 3. Verification Mode

**Purpose:**
- Review completed annotations
- Mark verified images

**Operation:**
- Press Space bar to toggle verification status
- Verified images show ✓ before the filename

### 4. Brightness Adjustment

**Features:**
- Adjust image display brightness
- Does not affect original image

**Operation:**
- Brightness slider on toolbar
- Shortcuts: `Ctrl+Shift++` (brighten), `Ctrl+Shift+-` (darken)
- `Ctrl+Shift+=` reset brightness

### 5. Color Settings

**Change Line Color:**
- Menu: `Edit → Change Line Color`
- Shortcut: `Ctrl+L`

**Change Fill Color:**
- Right-click on bounding box
- Select "Choose Line Color" or "Choose Fill Color"

---

## Keyboard Shortcuts

### Common Shortcuts

| Shortcut | Function |
|----------|----------|
| `Ctrl+O` | Open image |
| `Ctrl+U` | Open directory |
| `Ctrl+S` | Save annotation |
| `Ctrl+Shift+S` | Save as |
| `Ctrl+W` | Close current image |
| `Ctrl+Q` | Quit application |

### Annotation Operations

| Shortcut | Function |
|----------|----------|
| `W` | Create bounding box |
| `Ctrl+J` | Edit mode |
| `Delete` | Delete selected box |
| `Ctrl+D` | Duplicate selected box |
| `Ctrl+E` | Edit label |
| `Ctrl+V` | Copy previous frame annotations |

### Navigation

| Shortcut | Function |
|----------|----------|
| `D` or `→` | Next image |
| `A` or `←` | Previous image |
| `Space` | Verify/Unverify |

### View Control

| Shortcut | Function |
|----------|----------|
| `Ctrl++` | Zoom in |
| `Ctrl+-` | Zoom out |
| `Ctrl+=` | Original size |
| `Ctrl+F` | Fit window |
| `Ctrl+Shift+F` | Fit width |
| `Ctrl+H` | Hide all boxes |
| `Ctrl+A` | Show all boxes |

### Brightness Control

| Shortcut | Function |
|----------|----------|
| `Ctrl+Shift++` | Brighten |
| `Ctrl+Shift+-` | Darken |
| `Ctrl+Shift+=` | Reset brightness |

### Others

| Shortcut | Function |
|----------|----------|
| `Ctrl+Shift+A` | Advanced mode |
| `Ctrl+R` | Change save directory |
| `Ctrl+Shift+O` | Open annotation file |
| `Ctrl+Shift+L` | Load label file |
| `Ctrl+Shift+D` | Delete image |

---

## FAQ

### Q1: How to switch language?

**A:** Menu `Language → Choose Language`, supports:
- English
- 简体中文 (Simplified Chinese)
- 繁體中文 (Traditional Chinese)
- 日本語 (Japanese)

### Q2: Where are annotation files saved?

**A:** 
- Saved in the same directory as the image by default
- Filename matches the image with extension `.xml` (VOC) or `.txt` (YOLO)
- Can be changed via `File → Change Save Dir`

### Q3: How to batch annotate the same category?

**A:**
1. Check "Use Default Label"
2. Select the category from the dropdown
3. Draw boxes directly without entering labels each time

### Q4: What if I drew a bounding box incorrectly?

**A:**
- Press `Ctrl+Z` to undo (if enabled)
- Or select and press `Delete`
- Or right-click in the list to delete

### Q5: How to check the number of annotated images?

**A:**
- Window title shows: `LabelCraft image.jpg (1/100)`
- Numbers in parentheses are current index and total count
- Right panel list shows all bounding boxes

### Q6: What annotation formats are supported?

**A:**
- **PASCAL VOC** (XML): Universal format, supported by most frameworks
- **YOLO** (TXT): For YOLO series models
- **CreateML** (JSON): For Apple CreateML framework

### Q7: How to handle difficult samples?

**A:**
1. Create or select a bounding box
2. Check "Mark as Difficult" on the right panel
3. XML will contain `<difficult>1</difficult>` after saving
4. Can choose to ignore these samples during training

### Q8: What if the image is too large/small?

**A:**
- Use `Ctrl++` / `Ctrl+-` to zoom
- Or `Ctrl+F` to fit window
- Or use mouse wheel to zoom
- Hold `Ctrl` + scroll for faster zooming

### Q9: How to backup annotation data?

**A:**
- Regularly copy the entire project folder
- Or use version control system (Git)
- Annotation files are text format, easy to manage

### Q10: Will annotations be lost if the program crashes?

**A:**
- If "Auto Save Mode" is enabled, they won't be lost
- Recommended to enable auto-save: `View → Auto Save Mode`
- Develop the habit of frequently pressing `Ctrl+S` to save

---

## Best Practices

### 1. Before Annotation

✅ Create predefined label file  
✅ Set appropriate save directory  
✅ Enable auto-save mode  
✅ Familiarize yourself with shortcuts  

### 2. During Annotation

✅ Keep label naming consistent  
✅ Regularly check annotation quality  
✅ Use verification mode to mark completion  
✅ Save progress periodically  

### 3. After Annotation

✅ Spot-check annotation quality  
✅ Backup annotation files  
✅ Export to required format  
✅ Record annotation statistics  

---

## Technical Support

- **Project Homepage**: https://github.com/syd168/LabelCraft
- **Original Project (labelImg)**: https://github.com/tzutalin/labelImg (Credits)
- **Issue Reporting**: Submit via GitHub Issues
- **Documentation**: Check project README.md

---

**Happy Annotating!** 🎉
