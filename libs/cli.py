#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
LabelCraft CLI Entry Point
This module serves as the proper entry point for the labelcraft command,
ensuring it works correctly regardless of the installation location.
"""
import sys
import os

def main():
    """
    Main entry point for LabelCraft command-line interface.
    This ensures proper module resolution and data file loading
    from any installation location.
    """
    # Handle --version flag
    if '--version' in sys.argv or '-v' in sys.argv:
        from libs import __version__
        print(f'LabelCraft {__version__}')
        sys.exit(0)
    
    # Get the directory where this module is located
    module_dir = os.path.dirname(os.path.abspath(__file__))
    # Get the parent directory (project root)
    project_root = os.path.dirname(module_dir)
    
    # Add project root and module directory to Python path for proper imports
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    if module_dir not in sys.path:
        sys.path.insert(0, module_dir)
    
    try:
        from PySide6.QtWidgets import QApplication
        from labelcraft_ui import get_main_app
        
        # Create and run the application
        app, _win = get_main_app(sys.argv)
        sys.exit(app.exec())
        
    except ImportError as e:
        print(f"Error: Failed to import required modules: {e}")
        print("Please ensure PySide6 and lxml are installed:")
        print("  pip install pyside6>=6.5.0 lxml>=4.9.0")
        sys.exit(1)
    except Exception as e:
        print(f"Error: Failed to start LabelCraft: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
