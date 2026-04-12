LabelCraft - Modern Image Annotation Tool
==========================================

.. image:: https://img.shields.io/pypi/v/labelcraft.svg
   :target: https://pypi.org/project/LabelCraft/
   :alt: PyPI Version

.. image:: https://img.shields.io/pypi/pyversions/labelcraft.svg
   :target: https://pypi.org/project/LabelCraft/
   :alt: Python Versions

.. image:: https://img.shields.io/github/license/syd168/LabelCraft.svg
   :target: https://github.com/syd168/LabelCraft/blob/master/LICENSE
   :alt: License

**LabelCraft** is a powerful and user-friendly graphical image annotation tool, enhanced from the popular labelImg project. It provides an intuitive interface for creating bounding box annotations for object detection and machine learning tasks.

✨ Key Features
--------------

- **Multiple Format Support**: Export annotations in PASCAL VOC (XML), YOLO (TXT), CreateML (JSON), COCO (JSON), and CSV formats
- **Project Management**: Create and manage annotation projects with organized directory structures
- **Smart Workflow**: Pending queue system for efficient batch annotation
- **Multi-language Support**: English, Simplified Chinese, Traditional Chinese, Japanese, German, French
- **Image Enhancement**: Real-time brightness adjustment for better visibility
- **Flexible Navigation**: Zoom, pan, and keyboard shortcuts for fast annotation
- **Predefined Classes**: Load and manage custom class labels
- **Annotation Verification**: Mark verified annotations for quality control
- **Dark/Light Mode**: Automatic theme adaptation for comfortable viewing
- **Auto-save**: Optional automatic saving when switching images
- **Cross-platform**: Works on Windows, macOS, and Linux

🚀 Quick Start
-------------

Installation
~~~~~~~~~~~~

Install via pip::

    pip install labelcraft

Or run from source::

    git clone https://github.com/syd168/LabelCraft.git
    cd LabelCraft
    pip install -r requirements.txt
    python main.py

Usage
~~~~~

Basic usage::

    labelcraft                              # Start without parameters
    labelcraft /path/to/images              # Open images from directory
    labelcraft --classes classes.txt        # Use custom class file
    labelcraft --save-dir ./output          # Set default save directory
    labelcraft --version                    # Show version

Command-line Options
~~~~~~~~~~~~~~~~~~~~

- ``image_dir``: Directory containing images to annotate (optional)
- ``--classes, -c``: Path to predefined classes file
- ``--save-dir, -s``: Default directory to save annotations
- ``--version, -v``: Display program version

📖 Documentation
---------------

For detailed tutorials and documentation, visit:

- `GitHub Repository <https://github.com/syd168/LabelCraft>`_
- `Installation Guide <https://github.com/syd168/LabelCraft/blob/master/doc/安装标注工具.md>`_
- `Tutorial (English) <https://github.com/syd168/LabelCraft/blob/master/doc/tutorial.md>`_
- `Tutorial (中文) <https://github.com/syd168/LabelCraft/blob/master/doc/tutorial_zh-CN.md>`_

🛠️ Development
-------------

Requirements
~~~~~~~~~~~~

- Python 3.8 or higher
- PySide6 >= 6.5.0
- lxml >= 4.9.0

Install dependencies::

    pip install pyside6>=6.5.0 lxml>=4.9.0

💡 Tips
------

- Press ``W`` to start drawing bounding boxes
- Use ``D`` and ``A`` to navigate between images
- Press ``Space`` to verify current annotation
- Use mouse wheel to zoom, drag to pan
- Adjust brightness with Ctrl+Shift+[/]

📄 License
---------

MIT License - See LICENSE file for details

🙏 Acknowledgments
-----------------

This project is based on the original `labelImg <https://github.com/tzutalin/labelImg>`_ by TzuTa Lin.

Note: This project is actively maintained and enhanced with modern features.
