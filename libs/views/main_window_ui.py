#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
UI Builder - Separates UI construction from business logic
This module handles all UI component creation and layout
"""
from PySide6.QtWidgets import (QMainWindow, QVBoxLayout, QHBoxLayout, 
                                QDockWidget, QWidget, QLabel, QGroupBox,
                                QListWidget, QCheckBox, QToolButton, QComboBox,
                                QScrollArea)
from PySide6.QtCore import Qt
from libs.toolBar import ToolBar
from libs.combobox import ComboBox
from libs.default_label_combobox import DefaultLabelComboBox
from libs.canvas import Canvas
from libs.zoomWidget import ZoomWidget
from libs.lightWidget import LightWidget
from libs.labelDialog import LabelDialog
from libs.colorDialog import ColorDialog


class MainWindowUIBuilder:
    """
    Builder class for constructing MainWindow UI components.
    
    This separates UI construction logic from business logic,
    making the code more maintainable and testable.
    """
    
    def __init__(self, main_window: QMainWindow):
        self.window = main_window
        self.widgets = {}  # Store references to created widgets
    
    def build_complete_ui(self, get_str_func, label_hist=None):
        """
        Build the complete UI for MainWindow.
        
        Args:
            get_str_func: Function to get translated strings
            label_hist: List of predefined labels
            
        Returns:
            Dictionary containing all created widgets
        """
        if label_hist is None:
            label_hist = []
        
        # Create central widget with canvas
        canvas = self._create_canvas()
        central_widget = self._create_central_widget(canvas)
        self.window.setCentralWidget(central_widget)
        
        # Create dock widget
        dock = self._create_right_dock(get_str_func, label_hist)
        self.window.addDockWidget(Qt.RightDockWidgetArea, dock)
        
        # Create toolbars
        file_toolbar = self._create_file_toolbar(get_str_func)
        edit_toolbar = self._create_edit_toolbar(get_str_func)
        view_toolbar = self._create_view_toolbar(get_str_func)
        
        # Create status bar
        self.window.statusBar().showMessage(get_str_func('ready'))
        
        return {
            'canvas': canvas,
            'dock': dock,
            'file_toolbar': file_toolbar,
            'edit_toolbar': edit_toolbar,
            'view_toolbar': view_toolbar,
            **self.widgets
        }
    
    def _create_canvas(self) -> Canvas:
        """Create the annotation canvas."""
        canvas = Canvas(parent=self.window)
        
        # Connect canvas signals to window methods
        # Use getattr to avoid errors if methods don't exist yet
        if hasattr(self.window, 'zoom_request'):
            canvas.zoomRequest.connect(self.window.zoom_request)
        if hasattr(self.window, 'scroll_request'):
            canvas.scrollRequest.connect(self.window.scroll_request)
        if hasattr(self.window, '_on_new_shape'):
            canvas.newShape.connect(self.window._on_new_shape)
        if hasattr(self.window, '_on_selection_changed'):
            canvas.selectionChanged.connect(self.window._on_selection_changed)
        if hasattr(self.window, '_on_shape_moved'):
            canvas.shapeMoved.connect(self.window._on_shape_moved)
        if hasattr(self.window, '_on_drawing_polygon'):
            canvas.drawingPolygon.connect(self.window._on_drawing_polygon)
        
        return canvas
    
    def _create_central_widget(self, canvas: Canvas) -> QWidget:
        """Create the central widget containing the canvas."""
        scroll_area = QScrollArea()
        scroll_area.setWidget(canvas)
        scroll_area.setWidgetResizable(True)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(scroll_area)
        
        central_widget = QWidget()
        central_widget.setLayout(layout)
        
        return central_widget
    
    def _create_right_dock(self, get_str_func, label_hist) -> QDockWidget:
        """
        Create the right dock widget with labels and file lists.
        
        Args:
            get_str_func: Function to get translated strings
            label_hist: List of predefined labels
            
        Returns:
            Configured QDockWidget
        """
        # Create dock widget
        dock = QDockWidget('', self.window)
        dock.setObjectName(get_str_func('labels'))
        dock.setTitleBarWidget(QWidget())  # Hide title bar
        
        # Create unified right panel
        right_panel = self._create_right_panel(get_str_func, label_hist)
        dock.setWidget(right_panel)
        
        self.widgets['dock'] = dock
        return dock
    
    def _create_right_panel(self, get_str_func, label_hist) -> QWidget:
        """Create the unified right panel with all sections."""
        panel = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(10)
        
        # Section 1: Output settings
        output_group = self._create_output_section(get_str_func)
        layout.addWidget(output_group)
        
        # Section 2: Label filter
        filter_group = self._create_filter_section(get_str_func)
        layout.addWidget(filter_group)
        
        # Section 3: Label list
        label_list_group = self._create_label_list_section(get_str_func)
        layout.addWidget(label_list_group)
        
        # Section 4: Completed annotations
        completed_group = self._create_completed_section(get_str_func)
        layout.addWidget(completed_group)
        
        layout.addStretch()
        
        panel.setLayout(layout)
        return panel
    
    def _create_output_section(self, get_str_func) -> QGroupBox:
        """Create output settings section."""
        group = QGroupBox(get_str_func('outputSettings'))
        layout = QVBoxLayout()
        layout.setSpacing(5)
        
        # Output path
        path_layout = QHBoxLayout()
        path_label = QLabel(get_str_func('outputPath'))
        output_dir_label = QLabel(get_str_func('notSet'))
        output_dir_label.setStyleSheet('padding: 2px;')
        path_layout.addWidget(path_label)
        path_layout.addWidget(output_dir_label)
        path_layout.addStretch()
        layout.addLayout(path_layout)
        
        # Output format
        format_layout = QHBoxLayout()
        format_label = QLabel(get_str_func('outputFormat'))
        output_format_label = QLabel('PASCAL VOC')
        output_format_label.setStyleSheet('padding: 2px;')
        format_layout.addWidget(format_label)
        format_layout.addWidget(output_format_label)
        format_layout.addStretch()
        layout.addLayout(format_layout)
        
        group.setLayout(layout)
        
        # Store references
        self.widgets['output_dir_label'] = output_dir_label
        self.widgets['output_format_label'] = output_format_label
        
        return group
    
    def _create_filter_section(self, get_str_func) -> QGroupBox:
        """Create label filter section."""
        group = QGroupBox(get_str_func('labelFilter'))
        layout = QVBoxLayout()
        layout.setSpacing(5)
        
        # Use simple combo box without callbacks
        from PySide6.QtWidgets import QComboBox as SimpleComboBox
        combo_box = SimpleComboBox()
        layout.addWidget(combo_box)
        
        group.setLayout(layout)
        self.widgets['combo_box'] = combo_box
        
        return group
    
    def _create_label_list_section(self, get_str_func) -> QGroupBox:
        """Create label list section."""
        group = QGroupBox(get_str_func('labelList'))
        layout = QVBoxLayout()
        layout.setSpacing(5)
        
        label_list = QListWidget()
        layout.addWidget(label_list)
        
        group.setLayout(layout)
        self.widgets['label_list'] = label_list
        
        return group
    
    def _create_completed_section(self, get_str_func) -> QGroupBox:
        """Create completed annotations section."""
        group = QGroupBox(get_str_func('completedAnnotations'))
        layout = QVBoxLayout()
        layout.setSpacing(5)
        
        file_list = QListWidget()
        layout.addWidget(file_list)
        
        group.setLayout(layout)
        self.widgets['file_list_widget'] = file_list
        
        return group
    
    def _create_file_toolbar(self, get_str_func) -> ToolBar:
        """Create file operations toolbar."""
        toolbar = self.window.toolbar(get_str_func('file'), [])
        return toolbar
    
    def _create_edit_toolbar(self, get_str_func) -> ToolBar:
        """Create edit operations toolbar."""
        toolbar = self.window.toolbar(get_str_func('edit'), [])
        return toolbar
    
    def _create_view_toolbar(self, get_str_func) -> ToolBar:
        """Create view operations toolbar."""
        toolbar = self.window.toolbar(get_str_func('view'), [])
        return toolbar
    
    def get_widget(self, name: str):
        """Get a reference to a created widget by name."""
        return self.widgets.get(name)
    
    def get_all_widgets(self) -> dict:
        """Get all created widgets."""
        return self.widgets.copy()
