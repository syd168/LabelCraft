#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
LabelCraft - Main Entry Point
A modern graphical image annotation tool for object detection.
"""
import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import QApplication
from labelcraft_ui import get_main_app, __appname__, __version__


def main():
    """Main entry point for LabelCraft application"""
    app, _win = get_main_app(sys.argv)
    return app.exec()


if __name__ == '__main__':
    main()
