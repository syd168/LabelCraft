# LabelCraft User Tutorial (v2.0.0)

> **Project-Based Image Annotation Tool** - Developed based on [labelImg](https://github.com/tzutalin/labelImg)

## 📖 Table of Contents

1. [Introduction](#introduction)
2. [Quick Start](#quick-start)
3. [Understanding Projects](#understanding-projects)
4. [Creating Your First Project](#creating-your-first-project)
5. [Annotation Workflow](#annotation-workflow)
6. [Advanced Features](#advanced-features)
7. [Format Conversion](#format-conversion)
8. [Keyboard Shortcuts](#keyboard-shortcuts)
9. [Best Practices](#best-practices)
10. [FAQ](#faq)

---

## Introduction

LabelCraft v2.0.0 is a professional image annotation tool designed for object detection and computer vision tasks. Unlike traditional tools, LabelCraft uses a **project-based workflow** that helps you organize annotations efficiently.

### What's New in v2.0?

- ✅ **Project Management**: Organize annotations into projects with metadata
- ✅ **Multi-Format Support**: 5 formats (VOC, YOLO, CreateML, COCO, CSV)
- ✅ **Built-in Converter**: Convert between all formats seamlessly
- ✅ **Dynamic Language Switching**: 6 languages without restart
- ✅ **Enhanced UI**: Better organization and usability
- ✅ **Smart Workflow**: Pending queue, verification mode, auto-save

---

## Quick Start

### Installation

```bash
pip install labelcraft
```

### Launch

```bash
labelcraft
```

Or from source:
```bash
./start.sh  # Linux/macOS
start.bat   # Windows
```

---

## Understanding Projects

### What is a Project?

A **Project** in LabelCraft is a container that organizes your annotation work. It includes:

- **Project File** (`.labelcraft`): Stores configuration (name, labels, format, etc.)
- **Annotations Directory**: Contains all annotation files
- **Images**: Your image files (can be anywhere)
- **Metadata**: Creation date, last modified, statistics

### Why Use Projects?

✅ **Organization**: Keep related annotations together  
✅ **Persistence**: Settings saved automatically  
✅ **Portability**: Easy to share and backup  
✅ **Tracking**: Monitor progress and statistics  
✅ **Flexibility**: Change formats mid-project  

### Project Structure

```
MyProject/
├── MyProject.labelcraft      # Project configuration file
├── annotations/               # All annotation files
│   ├── image1.xml
│   ├── image2.xml
│   └── ...
└── images/                    # Your images (optional location)
    ├── image1.jpg
    ├── image2.jpg
    └── ...
```

---

## Creating Your First Project

### Step 1: Open New Project Dialog

**Method 1:** Menu → `File` → `New Project`  
**Method 2:** Keyboard shortcut `Ctrl+N`  
**Method 3:** Click "New Project" button on toolbar

### Step 2: Fill Project Information

The New Project dialog will appear:

#### Project Name
- Enter a descriptive name for your project
- Example: "Cat_Dog_Detection", "Vehicle_Annotation"

#### Project Location
- Choose where to store the project
- Click "Browse" to select a directory
- The system will create:
  - Project file: `{name}.labelcraft`
  - Annotations folder: `annotations/`

#### Output Format
Choose your annotation format:

| Format | Extension | Use Case |
|--------|-----------|----------|
| **PASCAL VOC** | `.xml` | Faster R-CNN, SSD, most frameworks |
| **YOLO** | `.txt` | YOLOv5, YOLOv8, YOLOv10 |
| **CreateML** | `.json` | Apple CreateML framework |
| **COCO** | `.json` | Microsoft COCO standard |
| **CSV** | `.csv` | Data analysis, spreadsheets |

> 💡 **Tip**: You can change this later! Annotations will be converted automatically.

#### Labels (Categories)
Add your object categories:

1. Type a label name in the input box
2. Click "Add" or press Enter
3. Repeat for all categories

Example labels for pet detection:
```
cat
dog
bird
rabbit
```

**Optional:**
- **Load from file**: Click "Load Labels" to import from a text file
- **Clear all**: Remove all labels and start over

### Step 3: Create Project

Click the **"Create Project"** button.

You'll see a success message with project details:
```
Project "MyProject" created successfully!

Project Name: MyProject
Location: /path/to/MyProject
Annotation Directory: /path/to/MyProject/annotations
Labels: 4 (cat, dog, bird, rabbit)
Output Format: PASCAL_VOC
```

The main window title updates to show: `LabelCraft - MyProject`

---

## Annotation Workflow

### Step 1: Add Images to Project

After creating a project, you need to add images:

**Method 1: Open Directory**
1. Menu → `File` → `Open Dir` or `Ctrl+U`
2. Select the folder containing your images
3. All supported images (JPG, PNG, BMP, etc.) load automatically

**Method 2: Drag & Drop**
- Simply drag image files from your file manager
- Drop them onto the LabelCraft window

**Method 3: Add Individual Files**
- Menu → `File` → `Add Images`
- Select specific image files

The left panel shows the **Pending Queue** - images waiting to be annotated.

### Step 2: Start Annotating

#### Create Bounding Box

1. Ensure you're in **Create Mode** (first toolbar button highlighted)
2. Press `W` or click "Create RectBox"
3. Click and drag on the image to draw a box around the object
4. Release the mouse button

#### Enter Label

A dialog appears asking for the label:

**Option A: Type Manually**
- Type the object category
- Press Enter or click OK

**Option B: Use Default Label**
1. Check "Use Default Label" checkbox (right panel)
2. Select a label from the dropdown
3. No dialog appears - uses selected label automatically
4. Great for batch annotating same-category objects

#### Adjust the Box

**Move:**
- Switch to Edit Mode (`Ctrl+J`)
- Drag the box to new position

**Resize:**
- In Edit Mode, drag edges or corners

**Fine-tune:**
- Use arrow keys for pixel-perfect positioning

### Step 3: Save Annotation

**Manual Save:**
- Press `Ctrl+S`
- Or menu → `File` → `Save`

**Auto-Save (Recommended):**
- Menu → `View` → `Auto Save Mode`
- Automatically saves when switching images

Saved annotations appear in the right panel list.

### Step 4: Verify Completion

Once an image is fully annotated:

1. Review all bounding boxes
2. Press `Space` to mark as verified
3. A ✓ appears before the filename
4. Image moves to "Completed" list

### Step 5: Navigate Between Images

**Next Image:**
- Press `D` or `→` arrow key
- Or click "Next Image" button

**Previous Image:**
- Press `A` or `←` arrow key
- Or click "Prev Image" button

**Jump to Specific Image:**
- Double-click any image in the file list (left panel)

### Step 6: Monitor Progress

Check your progress in multiple places:

- **Window Title**: `LabelCraft - MyProject (5/100)`
  - Shows current image number and total
- **Left Panel**: Pending vs completed counts
- **Right Panel**: Number of annotations on current image

---

## Advanced Features

### Editing Projects

Need to modify project settings?

1. Menu → `File` → `Edit Project` or `Ctrl+E`
2. The dialog opens with current settings pre-filled
3. Modify as needed:
   - Add/remove labels
   - Change output format
   - Update project name

**Important:** Changing output format will prompt you to migrate existing annotations.

### Managing Labels

#### Add Labels During Annotation

Labels are automatically added to the project when you:
- Create a new bounding box with a new label
- Edit an existing box and change its label

#### Load Labels from File

1. Prepare a text file with one label per line:
   ```txt
   person
   car
   bicycle
   motorcycle
   ```

2. In New/Edit Project dialog, click "Load Labels"
3. Select your text file
4. Labels populate automatically

#### Remove Unused Labels

1. Menu → `File` → `Edit Project`
2. Select label in the list
3. Click "Remove" or press Delete key

> ⚠️ **Warning**: Removing labels won't delete existing annotations, but may cause inconsistencies.

### Copy Previous Frame

For video frames or similar consecutive images:

1. Annotate first frame completely
2. Move to next frame
3. Menu → `File` → `Copy Previous Bounding Boxes` or `Ctrl+V`
4. All boxes from previous frame are copied
5. Adjust positions as needed

This saves enormous time for sequential annotation!

### Brightness Adjustment

Having trouble seeing objects in dark/bright images?

**Toolbar Slider:**
- Drag the brightness slider on the toolbar

**Keyboard Shortcuts:**
- `Ctrl+Shift++` : Increase brightness
- `Ctrl+Shift+-` : Decrease brightness
- `Ctrl+Shift+=` : Reset to normal

> 💡 This only affects display, not the original image!

### Verification Mode

Quality control is crucial:

1. After annotating an image, review carefully
2. Press `Space` to toggle verification status
3. Verified images show ✓ in the file list
4. Use this to track which images need review

### Export Annotations

Export your annotations in different formats:

1. Menu → `File` → `Export Annotations` or `Ctrl+E`
2. Choose export format
3. Select destination directory
4. Click "Export"

All annotations will be converted and saved.

---

## Format Conversion

### Built-in Converter

LabelCraft v2.0 includes a powerful converter supporting all 5 formats.

### Programmatic Usage

```python
from libs.annotation_converter import AnnotationConverter

# Initialize converter
converter = AnnotationConverter()

# Convert entire directory
converter.convert(
    input_dir='path/to/voc_annotations',
    input_format='voc',        # Source format
    output_format='yolo',      # Target format
    output_dir='path/to/yolo_output'
)
```

**Supported Formats:**
- `'voc'` - PASCAL VOC (XML)
- `'yolo'` - YOLO (TXT)
- `'createml'` - CreateML (JSON)
- `'coco'` - COCO (JSON)
- `'csv'` - CSV

### Command-Line Usage

```bash
# Basic conversion
python -m libs.annotation_converter \
    --input /path/to/input \
    --input_format voc \
    --output_format yolo \
    --output /path/to/output

# With options
python -m libs.annotation_converter \
    --input ./voc_annotations \
    --input_format voc \
    --output_format coco \
    --output ./coco_annotations \
    --verbose
```

### Common Conversion Scenarios

#### VOC to YOLO
Train YOLO models with VOC-annotated data:
```python
converter.convert('voc_data/', 'voc', 'yolo', 'yolo_data/')
```

#### YOLO to COCO
Convert YOLO datasets to COCO format:
```python
converter.convert('yolo_dataset/', 'yolo', 'coco', 'coco_dataset/')
```

#### Any to CSV
Export for analysis in Excel/spreadsheets:
```python
converter.convert('annotations/', 'voc', 'csv', 'analysis.csv')
```

### Format Details

#### PASCAL VOC (XML)
```xml
<annotation>
    <folder>images</folder>
    <filename>image1.jpg</filename>
    <size>
        <width>1920</width>
        <height>1080</height>
    </size>
    <object>
        <name>cat</name>
        <bndbox>
            <xmin>100</xmin>
            <ymin>150</ymin>
            <xmax>300</xmax>
            <ymax>350</ymax>
        </bndbox>
    </object>
</annotation>
```

#### YOLO (TXT)
```
0 0.5 0.5 0.4 0.4
1 0.7 0.3 0.2 0.3
```
Format: `<class_id> <x_center> <y_center> <width> <height>`
- Values normalized to 0-1
- One line per object
- Class IDs start from 0

#### COCO (JSON)
```json
{
  "images": [
    {"id": 1, "file_name": "image1.jpg", "width": 1920, "height": 1080}
  ],
  "annotations": [
    {"id": 1, "image_id": 1, "category_id": 1, 
     "bbox": [100, 150, 200, 200]}
  ],
  "categories": [
    {"id": 1, "name": "cat"},
    {"id": 2, "name": "dog"}
  ]
}
```

#### CSV
```csv
filename,width,height,class,xmin,ymin,xmax,ymax
image1.jpg,1920,1080,cat,100,150,300,350
image1.jpg,1920,1080,dog,500,400,700,600
```

---

## Keyboard Shortcuts

### Project Management
| Shortcut | Action |
|----------|--------|
| `Ctrl+N` | New Project |
| `Ctrl+O` | Open Project |
| `Ctrl+E` | Edit Project |
| `Ctrl+S` | Save Annotation |
| `Ctrl+Shift+C` | Close Project |

### File Operations
| Shortcut | Action |
|----------|--------|
| `Ctrl+U` | Open Directory |
| `Ctrl+Shift+O` | Open Annotation File |
| `Ctrl+W` | Close Current Image |
| `Ctrl+Q` | Quit Application |

### Annotation
| Shortcut | Action |
|----------|--------|
| `W` | Create RectBox |
| `Ctrl+J` | Toggle Edit/Create Mode |
| `Delete` | Delete Selected Box |
| `Ctrl+D` | Duplicate Selected Box |
| `Ctrl+E` | Edit Label |
| `Ctrl+V` | Copy Previous Frame |

### Navigation
| Shortcut | Action |
|----------|--------|
| `D` or `→` | Next Image |
| `A` or `←` | Previous Image |
| `Space` | Verify/Unverify Image |
| `Home` | First Image |
| `End` | Last Image |

### View Control
| Shortcut | Action |
|----------|--------|
| `Ctrl++` | Zoom In |
| `Ctrl+-` | Zoom Out |
| `Ctrl+=` | Original Size |
| `Ctrl+F` | Fit Window |
| `Ctrl+Shift+F` | Fit Width |
| `Ctrl+H` | Hide All Boxes |
| `Ctrl+A` | Show All Boxes |

### Brightness
| Shortcut | Action |
|----------|--------|
| `Ctrl+Shift++` | Increase Brightness |
| `Ctrl+Shift+-` | Decrease Brightness |
| `Ctrl+Shift+=` | Reset Brightness |

### Others
| Shortcut | Action |
|----------|--------|
| `Ctrl+T` | Toggle Toolbar |
| `Ctrl+R` | Change Save Directory |
| `Ctrl+Shift+L` | Load Predefined Labels |
| `Ctrl+Shift+D` | Delete Image |

---

## Best Practices

### Before Starting

✅ **Plan your labels**: Define all categories beforehand  
✅ **Create a project**: Use projects for organization  
✅ **Set correct format**: Choose format matching your training framework  
✅ **Enable auto-save**: Prevent data loss  
✅ **Learn shortcuts**: Boost productivity significantly  

### During Annotation

✅ **Consistent labeling**: Use exact same spelling for categories  
✅ **Tight boxes**: Draw boxes tightly around objects  
✅ **Regular verification**: Use Space to verify completed images  
✅ **Frequent saving**: Save often, even with auto-save  
✅ **Default labels**: Use for batch annotation of same category  
✅ **Quality checks**: Periodically review previous annotations  

### After Annotation

✅ **Verify all images**: Ensure everything is marked verified  
✅ **Backup project**: Copy entire project directory  
✅ **Export if needed**: Convert to required formats  
✅ **Document statistics**: Record number of images, objects per class  
✅ **Version control**: Use Git for project tracking  

### Project Organization

```
Projects/
├── Project_1_Cats_Dogs/
│   ├── Project_1_Cats_Dogs.labelcraft
│   ├── annotations/
│   └── images/
├── Project_2_Vehicles/
│   ├── Project_2_Vehicles.labelcraft
│   ├── annotations/
│   └── images/
└── exports/
    ├── voc_export/
    ├── yolo_export/
    └── coco_export/
```

### Efficiency Tips

1. **Batch Similar Images**: Group similar images together
2. **Use Default Labels**: When annotating many objects of same type
3. **Copy Previous Frame**: For video or similar consecutive images
4. **Keyboard Over Mouse**: Learn and use shortcuts
5. **Regular Breaks**: Maintain annotation quality with breaks
6. **Progress Tracking**: Use verification mode to track completion

---

## FAQ

### Q1: Can I use LabelCraft without creating a project?

**A:** Yes! You can use legacy mode:
```bash
python main.py /path/to/images
```
However, projects provide better organization and are recommended.

### Q2: How do I open an existing project?

**A:** 
- Menu → `File` → `Open Project` or `Ctrl+O`
- Select the `.labelcraft` file
- Or use recent projects list in menu

### Q3: Where are my annotations saved?

**A:** In the project's `annotations/` directory by default. Each annotation file has the same name as the image with appropriate extension (.xml, .txt, .json, .csv).

### Q4: Can I change the output format after starting?

**A:** Yes! Edit project (`Ctrl+E`) and change format. Existing annotations will be offered for migration.

### Q5: How do I convert my old labelImg annotations?

**A:** Use the built-in converter:
```python
from libs.annotation_converter import AnnotationConverter
converter = AnnotationConverter()
converter.convert('old_annotations/', 'voc', 'yolo', 'new_annotations/')
```

### Q6: What image formats are supported?

**A:** JPG, JPEG, PNG, BMP, TIFF, WEBP, and most common image formats.

### Q7: How do I backup my project?

**A:** Copy the entire project directory including:
- `.labelcraft` file
- `annotations/` folder
- Your images (if stored in project)

### Q8: Can multiple people work on the same project?

**A:** Not simultaneously. However, you can:
1. Split images into sub-projects
2. Have each person annotate separately
3. Merge annotations using the converter

### Q9: How do I add more labels mid-project?

**A:** 
- Just type new label names when creating boxes
- Or edit project (`Ctrl+E`) to manage labels

### Q10: Is there an undo function?

**A:** Currently, deletion is immediate. Be careful when deleting. Future versions may add undo support.

### Q11: How do I report bugs or request features?

**A:** Visit our GitHub Issues page: https://github.com/syd168/LabelCraft/issues

### Q12: Can I contribute to LabelCraft?

**A:** Absolutely! We welcome contributions:
1. Fork the repository
2. Make your changes
3. Submit a Pull Request

See README.md for development setup instructions.

---

## Getting Help

- **Documentation**: Check `doc/` directory in repository
- **Issues**: https://github.com/syd168/LabelCraft/issues
- **Discussions**: GitHub Discussions tab
- **Email**: syd168@users.noreply.github.com

---

**Happy Annotating! 🎉**

*Version 2.0.0 - Made with ❤️ for the computer vision community*
