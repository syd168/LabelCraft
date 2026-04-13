#!/usr/bin/env python
# -*- coding: utf-8 -*-
import argparse
import codecs
import json
import os.path
import platform
import shutil
import sys
import webbrowser as wb
from functools import partial

from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *

from libs.combobox import ComboBox
from libs.default_label_combobox import DefaultLabelComboBox
from libs.resources import *
from libs.constants import *
from libs.utils import *
from libs.settings import Settings
from libs.shape import Shape, DEFAULT_LINE_COLOR, DEFAULT_FILL_COLOR
from libs.i18n import StringBundle
from libs.i18n_engine import I18nEngine
from libs.canvas import Canvas
from libs.zoomWidget import ZoomWidget
from libs.lightWidget import LightWidget
from libs.labelDialog import LabelDialog
from libs.colorDialog import ColorDialog
from libs.labelFile import LabelFile, LabelFileError, LabelFileFormat
from libs.toolBar import ToolBar
from libs.pascal_voc_io import PascalVocReader
from libs.pascal_voc_io import XML_EXT
from libs.yolo_io import YoloReader
from libs.yolo_io import TXT_EXT
from libs.create_ml_io import CreateMLReader
from libs.create_ml_io import JSON_EXT
from libs.ustr import ustr
from libs.hashableQListWidgetItem import HashableQListWidgetItem
from libs.project import Project, RecentProjectsManager
from libs.newProjectDialog import NewProjectDialog
from libs import __version__

__appname__ = 'LabelCraft'


class WindowMixin(object):

    def menu(self, title, actions=None):
        menu = self.menuBar().addMenu(title)
        if actions:
            add_actions(menu, actions)
        return menu

    def toolbar(self, title, actions=None):
        toolbar = ToolBar(title)
        toolbar.setObjectName(u'%sToolBar' % title)
        # Use icon and text style for better visibility
        toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        if actions:
            add_actions(toolbar, actions)
        
        # Enable toggle button for the toolbar
        toolbar.setMovable(False)  # Prevent moving
        # Note: The toggle text will be set later in __init__ using self.get_str()
        toolbar.toggleViewAction().setShortcut('Ctrl+T')
        
        self.addToolBar(Qt.ToolBarArea.LeftToolBarArea, toolbar)
        return toolbar


class MainWindow(QMainWindow, WindowMixin):
    FIT_WINDOW, FIT_WIDTH, MANUAL_ZOOM = list(range(3))

    def __init__(self, default_filename=None, default_prefdef_class_file=None, default_save_dir=None):
        super(MainWindow, self).__init__()
        self.setWindowTitle(__appname__)

        # Load setting in the main thread
        self.settings = Settings()
        self.settings.load()
        settings = self.settings

        self.os_name = platform.system()

        # Initialize modern I18n engine (with dynamic switching support)
        self.i18n = I18nEngine()
        
        # Keep old string bundle for backward compatibility
        self.string_bundle = StringBundle.get_bundle()
        
        # Connect language change signal for dynamic UI updates
        self.i18n.language_changed.connect(self.on_language_changed)

        # Save as Pascal voc xml
        self.default_save_dir = default_save_dir
        self.label_file_format = settings.get(SETTING_LABEL_FILE_FORMAT, LabelFileFormat.PASCAL_VOC)

        # For loading all image under a directory
        self.m_img_list = []
        self.dir_name = None
        self.label_hist = []
        self.last_open_dir = None
        self.cur_img_idx = 0
        self.img_count = len(self.m_img_list)
        
        # Project management
        self.current_project = None  # Current loaded project

        # Whether we need to save or not.
        self.dirty = False

        self._no_selection_slot = False
        self._beginner = True
        self.screencast = "https://youtu.be/p0nR2YsCY_U"

        # Load predefined classes to the list
        self.load_predefined_classes(default_prefdef_class_file)

        if self.label_hist:
            self.default_label = self.label_hist[0]
        else:
            print("Not find:/data/predefined_classes.txt (optional)")

        # Main widgets and related state.
        self.label_dialog = LabelDialog(parent=self, list_item=self.label_hist)

        self.items_to_shapes = {}
        self.shapes_to_items = {}
        self.prev_label_text = ''

        list_layout = QVBoxLayout()
        list_layout.setContentsMargins(0, 0, 0, 0)

        # Create a widget for using default label
        self.use_default_label_checkbox = QCheckBox(self.get_str('useDefaultLabel'))
        self.use_default_label_checkbox.setChecked(False)
        self.default_label_combo_box = DefaultLabelComboBox(self, items=self.label_hist)

        use_default_label_qhbox_layout = QHBoxLayout()
        use_default_label_qhbox_layout.addWidget(self.use_default_label_checkbox)
        use_default_label_qhbox_layout.addWidget(self.default_label_combo_box)
        use_default_label_container = QWidget()
        use_default_label_container.setLayout(use_default_label_qhbox_layout)

        # Create a widget for edit and diffc button
        self.diffc_button = QCheckBox(self.get_str('useDifficult'))
        self.diffc_button.setChecked(False)
        self.diffc_button.stateChanged.connect(self.button_state)
        self.edit_button = QToolButton()
        self.edit_button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)

        # Add some of widgets to list_layout
        list_layout.addWidget(self.edit_button)
        list_layout.addWidget(self.diffc_button)
        list_layout.addWidget(use_default_label_container)

        # Create and add combobox for showing unique labels in group
        self.combo_box = ComboBox(self)
        list_layout.addWidget(self.combo_box)

        # Create and add a widget for showing current label items
        self.label_list = QListWidget()
        
        # Create file list widget first (needed before building the panel)
        self.file_list_widget = QListWidget()
        
        # Create dock widget (remove title, will be hidden)
        self.dock = QDockWidget('', self)
        self.dock.setObjectName(self.get_str('labels'))
        self.dock.setTitleBarWidget(QWidget())  # Hide the title bar
        
        # Create unified right panel with all sections
        right_panel_layout = QVBoxLayout()
        right_panel_layout.setContentsMargins(5, 5, 5, 5)
        right_panel_layout.setSpacing(10)
        
        # Section 1: Output settings
        output_group = QGroupBox(self.get_str('outputSettings'))
        output_layout = QVBoxLayout()
        output_layout.setSpacing(5)
        
        # Output path (read-only label)
        output_path_layout = QHBoxLayout()
        output_path_label = QLabel(self.get_str('outputPath'))
        self.output_dir_label = QLabel(self.get_str('notSet'))
        self.output_dir_label.setStyleSheet('padding: 2px;')
        output_path_layout.addWidget(output_path_label)
        output_path_layout.addWidget(self.output_dir_label)
        output_path_layout.addStretch()
        output_layout.addLayout(output_path_layout)
        
        # Output format (read-only label)
        output_format_layout = QHBoxLayout()
        output_format_label = QLabel(self.get_str('outputFormat'))
        self.output_format_label = QLabel(self.get_str('exportFormatVOC').split('(')[0].strip())  # Extract 'PASCAL VOC' without extension
        self.output_format_label.setStyleSheet('padding: 2px;')
        output_format_layout.addWidget(output_format_label)
        output_format_layout.addWidget(self.output_format_label)
        output_format_layout.addStretch()
        output_layout.addLayout(output_format_layout)
        
        # Default label (checkbox + combo in same row)
        default_label_layout = QHBoxLayout()
        default_label_layout.setSpacing(5)
        
        self.use_default_label_checkbox = QCheckBox(self.get_str('defaultLabel'))
        self.use_default_label_checkbox.setChecked(False)
        # Initialize with empty list, will be populated when loading project or labels
        self.default_label_combo_box = DefaultLabelComboBox(self, items=[])
        
        # Hide default label section initially (no labels loaded yet)
        self.use_default_label_checkbox.setVisible(False)
        self.default_label_combo_box.setVisible(False)
        
        default_label_layout.addWidget(self.use_default_label_checkbox)
        default_label_layout.addWidget(self.default_label_combo_box)
        output_layout.addLayout(default_label_layout)
        
        output_group.setLayout(output_layout)
        right_panel_layout.addWidget(output_group)
        
        # Section 3: Label filter (combo box) - filter shapes by label
        filter_label_group = QGroupBox(self.get_str('labelFilter'))
        filter_label_layout = QVBoxLayout()
        filter_label_layout.setSpacing(5)
        # Initialize with empty list, will be updated when loading labels
        self.combo_box = ComboBox(self, items=[])
        filter_label_layout.addWidget(self.combo_box)
        filter_label_group.setLayout(filter_label_layout)
        right_panel_layout.addWidget(filter_label_group)
        
        # Section 4: Label list
        label_list_group = QGroupBox(self.get_str('labelList'))
        label_list_layout_inner = QVBoxLayout()
        label_list_layout_inner.setSpacing(5)
        
        self.label_list.itemActivated.connect(self.label_selection_changed)
        self.label_list.itemSelectionChanged.connect(self.label_selection_changed)
        self.label_list.itemDoubleClicked.connect(self.edit_label)
        self.label_list.itemChanged.connect(self.label_item_changed)
        label_list_layout_inner.addWidget(self.label_list)
        
        label_list_group.setLayout(label_list_layout_inner)
        right_panel_layout.addWidget(label_list_group)
        
        # Section 5: Completed annotations (scan from annotations directory)
        completed_group = QGroupBox(self.get_str('completedAnnotations'))
        completed_layout = QVBoxLayout()
        completed_layout.setSpacing(5)
        
        self.file_list_widget.itemDoubleClicked.connect(self.file_item_double_clicked)
        completed_layout.addWidget(self.file_list_widget)
        completed_group.setLayout(completed_layout)
        right_panel_layout.addWidget(completed_group)
        
        right_panel_layout.addStretch()
        
        label_list_container = QWidget()
        label_list_container.setLayout(right_panel_layout)
        self.dock.setWidget(label_list_container)

        # Create main widgets
        self.zoom_widget = ZoomWidget(title=self.get_str('zoomin'))
        self.light_widget = LightWidget(self.get_str('lightWidgetTitle'))
        self.color_dialog = ColorDialog(parent=self)

        self.canvas = Canvas(parent=self)
        self.canvas.zoomRequest.connect(self.zoom_request)
        self.canvas.lightRequest.connect(self.light_request)
        self.canvas.set_drawing_shape_to_square(settings.get(SETTING_DRAW_SQUARE, False))

        scroll = QScrollArea()
        scroll.setWidget(self.canvas)
        scroll.setWidgetResizable(True)
        # Use both enum and int keys for compatibility
        v_scroll = scroll.verticalScrollBar()
        h_scroll = scroll.horizontalScrollBar()
        self.scroll_bars = {
            Qt.Orientation.Vertical: v_scroll,
            Qt.Orientation.Horizontal: h_scroll,
            Qt.Orientation.Vertical.value: v_scroll,
            Qt.Orientation.Horizontal.value: h_scroll,
            0: v_scroll,  # Handle signal passing 0 for vertical
            1: h_scroll,  # Handle signal passing 1 for horizontal
        }
        self.scroll_area = scroll
        self.canvas.scrollRequest.connect(self.scroll_request)

        self.canvas.newShape.connect(self.new_shape)
        self.canvas.shapeMoved.connect(self.set_dirty)
        self.canvas.selectionChanged.connect(self.shape_selection_changed)
        self.canvas.drawingPolygon.connect(self.toggle_drawing_sensitive)
        self.canvas.shapeDoubleClicked.connect(self.edit_label)

        # Create central widget with splitter (canvas + pending queue)
        central_splitter = QSplitter(Qt.Orientation.Vertical)
        
        # Add canvas scroll area to splitter
        central_splitter.addWidget(scroll)
        
        # Create pending images queue section
        pending_widget = QWidget()
        pending_layout = QVBoxLayout()
        pending_layout.setContentsMargins(5, 5, 5, 5)
        pending_layout.setSpacing(5)
        
        # Buttons for pending queue - horizontal layout
        pending_btn_layout = QHBoxLayout()
        pending_btn_layout.setSpacing(5)
        add_images_btn = QPushButton(self.get_str('addImages'))
        add_images_btn.clicked.connect(self.add_images_to_pending)
        add_folder_btn = QPushButton(self.get_str('addFolder'))
        add_folder_btn.clicked.connect(self.add_folder_to_pending)
        clear_pending_btn = QPushButton(self.get_str('clearPending'))
        clear_pending_btn.clicked.connect(self.clear_pending_queue)
        pending_btn_layout.addWidget(add_images_btn)
        pending_btn_layout.addWidget(add_folder_btn)
        pending_btn_layout.addStretch()
        pending_btn_layout.addWidget(clear_pending_btn)
        pending_layout.addLayout(pending_btn_layout)
        
        # Pending images list (below buttons)
        self.pending_list_widget = QListWidget()
        self.pending_list_widget.itemDoubleClicked.connect(self.pending_item_double_clicked)
        pending_layout.addWidget(self.pending_list_widget)
        
        pending_widget.setLayout(pending_layout)
        central_splitter.addWidget(pending_widget)
        
        # Set initial sizes (canvas takes most space)
        central_splitter.setStretchFactor(0, 1)  # Canvas expands
        central_splitter.setStretchFactor(1, 0)  # Pending queue fixed
        central_splitter.setSizes([600, 150])  # Initial split
        
        self.setCentralWidget(central_splitter)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.dock)
        self.dock.setFeatures(QDockWidget.DockWidgetFeature.DockWidgetFloatable)
        # Set reasonable default width for right panel (250 pixels)
        self.dock.setMinimumWidth(200)
        self.dock.setMaximumWidth(350)

        self.dock_features = QDockWidget.DockWidgetFeature.DockWidgetClosable | QDockWidget.DockWidgetFeature.DockWidgetFloatable
        self.dock.setFeatures(self.dock.features() ^ self.dock_features)
        
        # Set stylesheet to add spacing between content areas and status bar
        # Use adaptive colors that work in both light and dark modes
        self.setStyleSheet("""
            QStatusBar {
                padding-top: 3px;
            }
            QToolBar {
                margin-bottom: 3px;
            }
            QDockWidget {
                margin-bottom: 3px;
            }
            /* Ensure ListWidget has proper background */
            QListWidget {
                background-color: palette(base);
            }
            QListWidget::item:selected {
                color: palette(highlighted-text);
            }
            /* Ensure GroupBox titles have consistent font size */
            QGroupBox {
                font-size: 13px;
                font-weight: bold;
            }
            /* QPushButton font size for consistency */
            QPushButton {
                font-size: 13px;
            }
        """)

        # Actions
        action = partial(new_action, self)
        quit = action(self.get_str('quit'), self.close,
                      'Ctrl+Q', 'quit', self.get_str('quitApp'))

        open = action(self.get_str('openFile'), self.open_file,
                      'Ctrl+O', 'open', self.get_str('openFileDetail'))

        open_dir = action(self.get_str('openDir'), self.open_dir_dialog,
                          'Ctrl+u', 'open', self.get_str('openDir'))

        change_save_dir = action(self.get_str('changeSaveDir'), self.change_save_dir_dialog,
                                 'Ctrl+r', 'open', self.get_str('changeSavedAnnotationDir'))

        open_annotation = action(self.get_str('openAnnotation'), self.open_annotation_dialog,
                                 'Ctrl+Shift+O', 'open', self.get_str('openAnnotationDetail'))
        copy_prev_bounding = action(self.get_str('copyPrevBounding'), self.copy_previous_bounding_boxes, 'Ctrl+v', 'copy',
                                    self.get_str('copyPrevBounding'))
        
        # Export annotations action
        export_annotations = action(self.get_str('exportAnnotations'), self.export_annotations_dialog,
                                    'Ctrl+E', 'save-as', self.get_str('exportAnnotationsDetail'))
        
        # Project management actions
        new_project = action(self.get_str('newProject'), self.new_project_dialog,
                            'Ctrl+N', 'new', self.get_str('newProjectDetail'))
        open_project = action(self.get_str('openProject'), self.open_project_dialog,
                             'Ctrl+O', 'open', self.get_str('openProjectDetail'))
        edit_project = action(self.get_str('editProject'), self.edit_project_dialog,
                             'Ctrl+E', 'edit', self.get_str('editProjectDetail'), enabled=False)
        save_project = action(self.get_str('saveProject'), self.save_project,
                             'Ctrl+S', 'save', self.get_str('saveProjectDetail'), enabled=False)
        close_project = action(self.get_str('closeProject'), self.close_project,
                              'Ctrl+Shift+C', 'close', self.get_str('closeProjectDetail'), enabled=False)

        open_next_image = action(self.get_str('nextImg'), self.open_next_image,
                                 'd', 'next', self.get_str('nextImgDetail'))

        open_prev_image = action(self.get_str('prevImg'), self.open_prev_image,
                                 'a', 'prev', self.get_str('prevImgDetail'))

        verify = action(self.get_str('verifyImg'), self.verify_image,
                        'space', 'verify', self.get_str('verifyImgDetail'))

        save = action(self.get_str('save'), self.save_file,
                      'Ctrl+S', 'save', self.get_str('saveDetail'), enabled=False)

        def get_format_meta(format):
            """
            returns a tuple containing (title, icon_name) of the selected format
            """
            if format == LabelFileFormat.PASCAL_VOC:
                return '&PascalVOC', 'format_voc'
            elif format == LabelFileFormat.YOLO:
                return '&YOLO', 'format_yolo'
            elif format == LabelFileFormat.CREATE_ML:
                return '&CreateML', 'format_createml'

        save_format = action(get_format_meta(self.label_file_format)[0],
                             self.change_format, 'Ctrl+Y',
                             get_format_meta(self.label_file_format)[1],
                             self.get_str('changeSaveFormat'), enabled=True)

        delete_image = action(self.get_str('deleteImg'), self.delete_image, 'Ctrl+Shift+D', 'close',
                              self.get_str('deleteImgDetail'))

        reset_all = action(self.get_str('resetAll'), self.reset_all, None, 'resetall', self.get_str('resetAllDetail'))

        color1 = action(self.get_str('boxLineColor'), self.choose_color1,
                        'Ctrl+L', 'color_line', self.get_str('boxLineColorDetail'))

        create_mode = action(self.get_str('crtBox'), self.set_create_mode,
                             'w', 'new', self.get_str('crtBoxDetail'), enabled=False)
        edit_mode = action(self.get_str('editBox'), self.set_edit_mode,
                           'Ctrl+J', 'edit', self.get_str('editBoxDetail'), enabled=False)

        create = action(self.get_str('crtBox'), self.create_shape,
                        'w', 'new', self.get_str('crtBoxDetail'), enabled=False)
        delete = action(self.get_str('delBox'), self.delete_selected_shape,
                        'Delete', 'delete', self.get_str('delBoxDetail'), enabled=False)
        copy = action(self.get_str('dupBox'), self.copy_selected_shape,
                      'Ctrl+D', 'copy', self.get_str('dupBoxDetail'),
                      enabled=False)

        advanced_mode = action(self.get_str('advancedMode'), self.toggle_advanced_mode,
                               'Ctrl+Shift+A', 'expert', self.get_str('advancedModeDetail'),
                               checkable=True)

        hide_all = action(self.get_str('hideAllBox'), partial(self.toggle_polygons, False),
                          'Ctrl+H', 'hide', self.get_str('hideAllBoxDetail'),
                          enabled=False)
        show_all = action(self.get_str('showAllBox'), partial(self.toggle_polygons, True),
                          'Ctrl+A', 'hide', self.get_str('showAllBoxDetail'),
                          enabled=False)

        help_default = action(self.get_str('tutorialDefault'), self.show_default_tutorial_dialog, None, 'help',
                              self.get_str('tutorialDetail'))
        show_info = action(self.get_str('info'), self.show_info_dialog, None, 'help', self.get_str('info'))
        self.show_shortcut = action(self.get_str('shortcut'), self.show_shortcuts_dialog, None, 'help', self.get_str('shortcut'))

        # Create zoom widget with slider and label
        zoom_widget_container = self.zoom_widget.create_widget_with_label()
        
        zoom = QWidgetAction(self)
        zoom.setDefaultWidget(zoom_widget_container)
        self.zoom_widget.setToolTip(
            u"Zoom in or out of the image. Also accessible with"
            " %s and %s from the canvas." % (format_shortcut("Ctrl+[-+]"),
                                             format_shortcut("Ctrl+Wheel")))
        self.zoom_widget.setEnabled(False)

        zoom_in = action(self.get_str('zoomin'), partial(self.add_zoom, 10),
                         'Ctrl++', 'zoom-in', self.get_str('zoominDetail'), enabled=False)
        zoom_out = action(self.get_str('zoomout'), partial(self.add_zoom, -10),
                          'Ctrl+-', 'zoom-out', self.get_str('zoomoutDetail'), enabled=False)
        zoom_org = action(self.get_str('originalsize'), partial(self.set_zoom, 100),
                          'Ctrl+=', 'zoom', self.get_str('originalsizeDetail'), enabled=False)
        fit_window = action(self.get_str('fitWin'), self.set_fit_window,
                            'Ctrl+F', 'fit-window', self.get_str('fitWinDetail'),
                            checkable=True, enabled=False)
        fit_width = action(self.get_str('fitWidth'), self.set_fit_width,
                           'Ctrl+Shift+F', 'fit-width', self.get_str('fitWidthDetail'),
                           checkable=True, enabled=False)
        # Group zoom controls into a list for easier toggling.
        zoom_actions = (self.zoom_widget, zoom_in, zoom_out,
                        zoom_org, fit_window, fit_width)
        self.zoom_mode = self.MANUAL_ZOOM
        self.scalers = {
            self.FIT_WINDOW: self.scale_fit_window,
            self.FIT_WIDTH: self.scale_fit_width,
            # Set to one to scale to 100% when loading files.
            self.MANUAL_ZOOM: lambda: 1,
        }

        # Create light widget with slider and label
        light_widget_container = self.light_widget.create_widget_with_label()
        
        light = QWidgetAction(self)
        light.setDefaultWidget(light_widget_container)
        self.light_widget.setToolTip(
            u"Brighten or darken current image. Also accessible with"
            " %s and %s from the canvas." % (format_shortcut("Ctrl+Shift+[-+]"),
                                             format_shortcut("Ctrl+Shift+Wheel")))
        self.light_widget.setEnabled(False)

        light_brighten = action(self.get_str('lightbrighten'), partial(self.add_light, 10),
                                'Ctrl+Shift++', 'light_lighten', self.get_str('lightbrightenDetail'), enabled=False)
        light_darken = action(self.get_str('lightdarken'), partial(self.add_light, -10),
                              'Ctrl+Shift+-', 'light_darken', self.get_str('lightdarkenDetail'), enabled=False)
        light_org = action(self.get_str('lightreset'), partial(self.set_light, 50),
                           'Ctrl+Shift+=', 'light_reset', self.get_str('lightresetDetail'), checkable=True, enabled=False)
        light_org.setChecked(True)

        # Group light controls into a list for easier toggling.
        light_actions = (self.light_widget, light_brighten,
                         light_darken, light_org)

        edit = action(self.get_str('editLabel'), self.edit_label,
                      'Ctrl+E', 'edit', self.get_str('editLabelDetail'),
                      enabled=False)
        self.edit_button.setDefaultAction(edit)

        shape_line_color = action(self.get_str('shapeLineColor'), self.choose_shape_line_color,
                                  icon='color_line', tip=self.get_str('shapeLineColorDetail'),
                                  enabled=False)
        shape_fill_color = action(self.get_str('shapeFillColor'), self.choose_shape_fill_color,
                                  icon='color', tip=self.get_str('shapeFillColorDetail'),
                                  enabled=False)

        labels = self.dock.toggleViewAction()
        labels.setText(self.get_str('showHide'))
        labels.setShortcut('Ctrl+Shift+L')

        # Label list context menu.
        label_menu = QMenu()
        add_actions(label_menu, (edit, delete))
        self.label_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.label_list.customContextMenuRequested.connect(
            self.pop_label_list_menu)

        # Draw squares/rectangles
        self.draw_squares_option = QAction(self.get_str('drawSquares'), self)
        self.draw_squares_option.setShortcut('Ctrl+Shift+R')
        self.draw_squares_option.setCheckable(True)
        self.draw_squares_option.setChecked(settings.get(SETTING_DRAW_SQUARE, False))
        self.draw_squares_option.triggered.connect(self.toggle_draw_square)

        # Store actions for further handling.
        self.actions = Struct(save=save, save_format=save_format, open=open,
                              resetAll=reset_all, deleteImg=delete_image, quit=quit,
                              lineColor=color1, create=create, delete=delete, edit=edit, copy=copy,
                              createMode=create_mode, editMode=edit_mode, advancedMode=advanced_mode,
                              shapeLineColor=shape_line_color, shapeFillColor=shape_fill_color,
                              zoom=zoom, zoomIn=zoom_in, zoomOut=zoom_out, zoomOrg=zoom_org,
                              fitWindow=fit_window, fitWidth=fit_width,
                              zoomActions=zoom_actions,
                              lightBrighten=light_brighten, lightDarken=light_darken, lightOrg=light_org,
                              lightActions=light_actions,
                              fileMenuActions=(
                                  open, open_dir, save, reset_all, quit),
                              beginner=(), advanced=(),
                              editMenu=(edit, copy, delete,
                                        None, color1, self.draw_squares_option),
                              beginnerContext=(create, edit, copy, delete),
                              advancedContext=(create_mode, edit_mode, edit, copy,
                                               delete, shape_line_color, shape_fill_color),
                              onLoadActive=(
                                  create, create_mode, edit_mode),
                              onShapesPresent=(hide_all, show_all),
                              # Add missing actions for language switching
                              openDir=open_dir, changeSaveDir=change_save_dir,
                              openAnnotation=open_annotation, copyPrevBounding=copy_prev_bounding,
                              exportAnnotations=export_annotations,
                              nextImg=open_next_image, prevImg=open_prev_image,
                              verify=verify, hideAll=hide_all, showAll=show_all,
                              labels=labels, drawSquares=self.draw_squares_option,
                              # Project management actions
                              newProject=new_project, openProject=open_project, editProject=edit_project, saveProject=save_project, closeProject=close_project)

        self.menus = Struct(
            file=self.menu(self.get_str('menu_file')),
            edit=self.menu(self.get_str('menu_edit')),
            view=self.menu(self.get_str('menu_view')),
            output=self.menu(self.get_str('menu_output')),
            language=self.menu(self.get_str('menu_lang')),
            help=self.menu(self.get_str('menu_help')),
            recentFiles=QMenu(self.get_str('menu_openRecent')),
            recentProjects=QMenu(self.get_str('menu_recentProjects')),  # Recent projects menu
            labelList=label_menu)

        # Auto saving : Enable auto saving if pressing next
        self.auto_saving = QAction(self.get_str('autoSaveMode'), self)
        self.auto_saving.setCheckable(True)
        self.auto_saving.setChecked(settings.get(SETTING_AUTO_SAVE, False))
        # Sync single class mode from PR#106
        self.single_class_mode = QAction(self.get_str('singleClsMode'), self)
        self.single_class_mode.setShortcut("Ctrl+Shift+S")
        self.single_class_mode.setCheckable(True)
        self.single_class_mode.setChecked(settings.get(SETTING_SINGLE_CLASS, False))
        self.lastLabel = None
        # Add option to enable/disable labels being displayed at the top of bounding boxes
        self.display_label_option = QAction(self.get_str('displayLabel'), self)
        self.display_label_option.setShortcut("Ctrl+Shift+P")
        self.display_label_option.setCheckable(True)
        self.display_label_option.setChecked(settings.get(SETTING_PAINT_LABEL, False))
        self.display_label_option.triggered.connect(self.toggle_paint_labels_option)

        # Language menu actions
        lang_action_group = QActionGroup(self)
        lang_action_group.setExclusive(True)

        self.lang_en = QAction(self.get_str('langEnglish'), self)
        self.lang_en.setCheckable(True)
        self.lang_en.setActionGroup(lang_action_group)
        self.lang_en.triggered.connect(lambda: self.change_language('en'))

        self.lang_zh_cn = QAction(self.get_str('langSimplifiedChinese'), self)
        self.lang_zh_cn.setCheckable(True)
        self.lang_zh_cn.setActionGroup(lang_action_group)
        self.lang_zh_cn.triggered.connect(lambda: self.change_language('zh-CN'))

        self.lang_zh_tw = QAction(self.get_str('langTraditionalChinese'), self)
        self.lang_zh_tw.setCheckable(True)
        self.lang_zh_tw.setActionGroup(lang_action_group)
        self.lang_zh_tw.triggered.connect(lambda: self.change_language('zh-TW'))

        self.lang_ja = QAction(self.get_str('langJapanese'), self)
        self.lang_ja.setCheckable(True)
        self.lang_ja.setActionGroup(lang_action_group)
        self.lang_ja.triggered.connect(lambda: self.change_language('ja-JP'))

        self.lang_de = QAction(self.get_str('langGerman'), self)
        self.lang_de.setCheckable(True)
        self.lang_de.setActionGroup(lang_action_group)
        self.lang_de.triggered.connect(lambda: self.change_language('de-DE'))

        self.lang_fr = QAction(self.get_str('langFrench'), self)
        self.lang_fr.setCheckable(True)
        self.lang_fr.setActionGroup(lang_action_group)
        self.lang_fr.triggered.connect(lambda: self.change_language('fr-FR'))

        # Set current language based on system locale
        current_locale = self.string_bundle.locale if hasattr(self.string_bundle, 'locale') else None
        if current_locale:
            if 'zh-CN' in current_locale or 'zh_CN' in current_locale:
                self.lang_zh_cn.setChecked(True)
            elif 'zh-TW' in current_locale or 'zh_TW' in current_locale:
                self.lang_zh_tw.setChecked(True)
            elif 'ja-JP' in current_locale or 'ja_JP' in current_locale:
                self.lang_ja.setChecked(True)
            elif 'de-DE' in current_locale or 'de_DE' in current_locale:
                self.lang_de.setChecked(True)
            elif 'fr-FR' in current_locale or 'fr_FR' in current_locale:
                self.lang_fr.setChecked(True)
            else:
                self.lang_en.setChecked(True)
        else:
            self.lang_en.setChecked(True)

        add_actions(self.menus.file,
                    (new_project, open_project, edit_project, save_project, close_project, None,
                     self.menus.recentProjects, None,  # Add recent projects menu
                     save, reset_all, delete_image, quit))
        
        # Output menu: export and save dir related functions
        add_actions(self.menus.output,
                    (export_annotations, None,
                     self.auto_saving, self.single_class_mode))
        
        # Custom context menu for the canvas widget:
        add_actions(self.canvas.menus[0], self.actions.beginnerContext)
        add_actions(self.canvas.menus[1], (
            action(self.get_str('copyHere'), self.copy_shape),
            action(self.get_str('moveHere'), self.move_shape)))

        # Create toolbar before building menus
        self.tools = self.toolbar('Tools')
        
        # Setup toolbar toggle action
        toolbar_toggle = self.tools.toggleViewAction()
        toolbar_toggle.setText(self.get_str('toolbarToggleText'))
        toolbar_toggle.setShortcut('Ctrl+T')
        
        add_actions(self.menus.language, (self.lang_en, self.lang_zh_cn, self.lang_zh_tw, self.lang_ja, self.lang_de, self.lang_fr))
        add_actions(self.menus.help, (help_default, show_info, self.show_shortcut))
        add_actions(self.menus.view, (
            toolbar_toggle, labels, None,  # Toolbar and dock toggle
            self.auto_saving,
            self.single_class_mode,
            self.display_label_option,
            advanced_mode, None,
            hide_all, show_all, None,
            zoom_in, zoom_out, zoom_org, None,
            fit_window, fit_width, None,
            light))
        

        self.menus.file.aboutToShow.connect(self.update_file_menu)
        self.menus.recentProjects.aboutToShow.connect(self.update_recent_projects_menu)
        
        self.actions.beginner = (
            verify, save, None, create,
            edit, copy, delete, None,
            fit_window, fit_width)

        self.actions.advanced = (
            save, None,
            create_mode, edit_mode, None,
            hide_all, show_all)

        self.statusBar().showMessage('%s started.' % __appname__)
        self.statusBar().show()

        # Application state.
        self.image = QImage()
        self.file_path = ustr(default_filename)
        self.last_open_dir = None
        self.recent_files = []
        self.max_recent = 7
        self.line_color = None
        self.fill_color = None
        self.zoom_level = 100
        self.fit_window = False
        # Add Chris
        self.difficult = False

        # Fix the compatible issue for qt4 and qt5. Convert the QStringList to python list
        if settings.get(SETTING_RECENT_FILES):
            if have_qstring():
                recent_file_qstring_list = settings.get(SETTING_RECENT_FILES)
                self.recent_files = [ustr(i) for i in recent_file_qstring_list]
            else:
                self.recent_files = recent_file_qstring_list = settings.get(SETTING_RECENT_FILES)

        size = settings.get(SETTING_WIN_SIZE, QSize(600, 500))
        position = QPoint(0, 0)
        saved_position = settings.get(SETTING_WIN_POSE, position)
        # Fix the multiple monitors issue
        # In Qt6/PySide6, QApplication.desktop() is removed, use QGuiApplication.screens()
        from PySide6.QtGui import QGuiApplication
        for screen in QGuiApplication.screens():
            if screen.availableGeometry().contains(saved_position):
                position = saved_position
                break
        self.resize(size)
        self.move(position)
        save_dir = ustr(settings.get(SETTING_SAVE_DIR, None))
        self.last_open_dir = ustr(settings.get(SETTING_LAST_OPEN_DIR, None))
        if self.default_save_dir is None and save_dir is not None and os.path.exists(save_dir):
            self.default_save_dir = save_dir
            self.statusBar().showMessage('%s started. Annotation will be saved to %s' %
                                         (__appname__, self.default_save_dir))
            self.statusBar().show()

        self.restoreState(settings.get(SETTING_WIN_STATE, QByteArray()))
        Shape.line_color = self.line_color = QColor(settings.get(SETTING_LINE_COLOR, DEFAULT_LINE_COLOR))
        Shape.fill_color = self.fill_color = QColor(settings.get(SETTING_FILL_COLOR, DEFAULT_FILL_COLOR))
        self.canvas.set_drawing_color(self.line_color)
        # Add chris
        Shape.difficult = self.difficult

        def xbool(x):
            return bool(x)

        if xbool(settings.get(SETTING_ADVANCE_MODE, False)):
            self.actions.advancedMode.setChecked(True)
            self.toggle_advanced_mode()

        # Populate the File menu dynamically.
        self.update_file_menu()

        # Since loading the file may take some time, make sure it runs in the background.
        if self.file_path and os.path.isdir(self.file_path):
            self.queue_event(partial(self.import_dir_images, self.file_path or ""))
        elif self.file_path:
            self.queue_event(partial(self.load_file, self.file_path or ""))

        # Callbacks:
        self.zoom_widget.valueChanged.connect(self.paint_canvas)
        self.light_widget.valueChanged.connect(self.paint_canvas)

        self.populate_mode_actions()

        # Display cursor coordinates at the right of status bar
        self.label_coordinates = QLabel('')
        self.statusBar().addPermanentWidget(self.label_coordinates)

        # Open Dir if default file
        if self.file_path and os.path.isdir(self.file_path):
            self.open_dir_dialog(dir_path=self.file_path, silent=True)

    def get_str(self, str_id):
        """Get translated string by ID (uses new i18n engine with fallback to old system)"""
        # Try new i18n engine first
        try:
            return self.i18n.tr(str_id)
        except:
            # Fallback to old string bundle
            return self.string_bundle.get_string(str_id)
    
    def on_language_changed(self, lang_code: str):
        """
        Called when language is switched dynamically.
        Retrarslates all UI elements.
        """
        print(f"🔄 Updating UI for language: {lang_code}")
        
        # Update window title
        self.setWindowTitle(__appname__)
        
        # Retranslate menus
        self.retranslate_menus()
        
        # Update dock widget
        if hasattr(self, 'dock'):
            self.dock.setObjectName(self.get_str('labels'))
        
        # Refresh UI
        self.update()
    
    def retranslate_menus(self):
        """Retranslate all menu titles and actions."""
        # This method will be called when language changes
        # It reuses the existing change_language logic
        pass

    def keyReleaseEvent(self, event):
        if event.key() == Qt.Key_Control:
            self.canvas.set_drawing_shape_to_square(False)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Control:
            # Draw rectangle if Ctrl is pressed
            self.canvas.set_drawing_shape_to_square(True)

    # Support Functions #
    def set_format(self, save_format):
        if save_format == FORMAT_PASCALVOC:
            self.actions.save_format.setText(FORMAT_PASCALVOC)
            self.actions.save_format.setIcon(new_icon("format_voc"))
            self.label_file_format = LabelFileFormat.PASCAL_VOC
            LabelFile.suffix = XML_EXT

        elif save_format == FORMAT_YOLO:
            self.actions.save_format.setText(FORMAT_YOLO)
            self.actions.save_format.setIcon(new_icon("format_yolo"))
            self.label_file_format = LabelFileFormat.YOLO
            LabelFile.suffix = TXT_EXT

        elif save_format == FORMAT_CREATEML:
            self.actions.save_format.setText(FORMAT_CREATEML)
            self.actions.save_format.setIcon(new_icon("format_createml"))
            self.label_file_format = LabelFileFormat.CREATE_ML
            LabelFile.suffix = JSON_EXT

    def change_format(self):
        if self.label_file_format == LabelFileFormat.PASCAL_VOC:
            self.set_format(FORMAT_YOLO)
        elif self.label_file_format == LabelFileFormat.YOLO:
            self.set_format(FORMAT_CREATEML)
        elif self.label_file_format == LabelFileFormat.CREATE_ML:
            self.set_format(FORMAT_PASCALVOC)
        else:
            raise ValueError('Unknown label file format.')
        self.set_dirty()

    def no_shapes(self):
        return not self.items_to_shapes

    def toggle_advanced_mode(self, value=True):
        self._beginner = not value
        self.canvas.set_editing(True)
        self.populate_mode_actions()
        # Update the checked state of the action
        if hasattr(self.actions, 'advancedMode'):
            self.actions.advancedMode.setChecked(value)
        if value:
            self.actions.createMode.setEnabled(True)
            self.actions.editMode.setEnabled(False)
            self.dock.setFeatures(self.dock.features() | self.dock_features)
        else:
            self.dock.setFeatures(self.dock.features() ^ self.dock_features)

    def populate_mode_actions(self):
        
        if self.beginner():
            tool, menu = self.actions.beginner, self.actions.beginnerContext
        else:
            tool, menu = self.actions.advanced, self.actions.advancedContext
        
        # Clear toolbar and create a unified container
        self.tools.clear()
        
        # Create a unified container for all toolbar content
        unified_container = QWidget()
        unified_layout = QVBoxLayout()
        unified_layout.setContentsMargins(2, 2, 2, 2)
        unified_layout.setSpacing(3)
        
        # Check if project is loaded and image is available
        has_project = self.current_project is not None
        has_image = self.file_path is not None and os.path.exists(self.file_path)
        
        # Add buttons in vertical layout (each button takes full width)
        for action_item in tool:
            if action_item is None:
                # Add separator line
                line = QFrame()
                line.setFrameShape(QFrame.Shape.HLine)
                line.setFrameShadow(QFrame.Shadow.Sunken)
                unified_layout.addWidget(line)
            elif hasattr(action_item, 'icon'):
                # It's a QAction, create a tool button that stretches to full width
                btn = QToolButton()
                btn.setDefaultAction(action_item)
                btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
                # Make button stretch to full width
                btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
                
                # Disable buttons if no project or no image loaded
                # But always enable verify, next, prev buttons if project is loaded
                if not has_project:
                    # No project loaded - disable all annotation buttons
                    if action_item in [self.actions.create, self.actions.edit, self.actions.delete, 
                                      self.actions.copy, self.actions.createMode, self.actions.editMode]:
                        action_item.setEnabled(False)
                elif not has_image:
                    # Project loaded but no image - disable annotation buttons
                    if action_item in [self.actions.create, self.actions.edit, self.actions.delete,
                                      self.actions.copy, self.actions.createMode, self.actions.editMode]:
                        action_item.setEnabled(False)
                
                unified_layout.addWidget(btn)
        
        # Add separator before sliders
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        unified_layout.addWidget(line)
        
        # Add brightness slider with label
        brightness_label = QLabel(self.get_str('lightWidgetTitle') + ':')
        brightness_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        unified_layout.addWidget(brightness_label)
        
        light_widget_container = self.light_widget.create_widget_with_label()
        unified_layout.addWidget(light_widget_container)
        
        # Add zoom slider with label
        zoom_label = QLabel(self.get_str('zoomin') + ':')
        zoom_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        unified_layout.addWidget(zoom_label)
        
        zoom_widget_container = self.zoom_widget.create_widget_with_label()
        unified_layout.addWidget(zoom_widget_container)
        
        unified_container.setLayout(unified_layout)
        
        # Add the unified container to toolbar
        self.tools.addWidget(unified_container)
        
        self.canvas.menus[0].clear()
        add_actions(self.canvas.menus[0], menu)
        self.menus.edit.clear()
        actions = (self.actions.create,) if self.beginner() \
            else (self.actions.createMode, self.actions.editMode)
        add_actions(self.menus.edit, actions + self.actions.editMenu)
        
        # Optimize toolbar layout: compact spacing and ensure buttons are always visible
        self.tools.setIconSize(QSize(16, 16))  # Smaller icons
        self.tools.setStyleSheet("""
            QToolBar {
                spacing: 2px;
                padding: 2px;
            }
            QToolButton {
                min-height: 24px;
                max-height: 28px;
                padding: 2px 4px;
                margin: 1px 0px;
                font-size: 13px;
            }
            /* Allow slider widgets to display properly */
            QWidget {
                min-height: 20px;
            }
            QSlider {
                min-width: 80px;
                max-width: 120px;
            }
        """)

    def set_beginner(self):
        self.tools.clear()
        add_actions(self.tools, self.actions.beginner)

    def set_advanced(self):
        self.tools.clear()
        add_actions(self.tools, self.actions.advanced)

    def set_dirty(self):
        self.dirty = True
        self.actions.save.setEnabled(True)

    def set_clean(self):
        self.dirty = False
        self.actions.save.setEnabled(False)
        self.actions.create.setEnabled(True)

    def toggle_actions(self, value=True):
        """Enable/Disable widgets which depend on an opened image."""
        for z in self.actions.zoomActions:
            z.setEnabled(value)
        for z in self.actions.lightActions:
            z.setEnabled(value)
        for action in self.actions.onLoadActive:
            action.setEnabled(value)
        # Enable/disable create button based on whether image is loaded
        self.actions.create.setEnabled(value)
        self.actions.createMode.setEnabled(value)

    def create_output_settings_widget(self):
        """Create the output settings dock widget with path input and format selection"""
        
        # Create dock widget
        dock = QDockWidget(self.get_str('outputDir'), self)
        dock.setObjectName('outputSettings')
        
        # Main container
        main_container = QWidget()
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(10)
        
        # Output directory section
        dir_group = QGroupBox(self.get_str('outputDir'))
        dir_layout = QVBoxLayout()
        dir_layout.setSpacing(5)
        
        # Directory input with browse button
        dir_input_layout = QHBoxLayout()
        self.output_dir_input = QLineEdit()
        self.output_dir_input.setPlaceholderText(self.get_str('changeSaveDir'))
        self.output_dir_input.setText(self.default_save_dir or '')
        self.output_dir_input.setReadOnly(True)
        
        browse_btn = QPushButton('...')
        browse_btn.setMaximumWidth(40)
        browse_btn.clicked.connect(self.change_save_dir_dialog)
        
        dir_input_layout.addWidget(self.output_dir_input)
        dir_input_layout.addWidget(browse_btn)
        dir_layout.addLayout(dir_input_layout)
        
        dir_group.setLayout(dir_layout)
        main_layout.addWidget(dir_group)
        
        # Output format section
        format_group = QGroupBox(self.get_str('outputFormat'))
        format_layout = QVBoxLayout()
        format_layout.setSpacing(5)
        
        # Format combo box
        self.output_format_combo = QComboBox()
        self.output_format_combo.addItem('PASCAL VOC', LabelFileFormat.PASCAL_VOC)
        self.output_format_combo.addItem('YOLO', LabelFileFormat.YOLO)
        self.output_format_combo.addItem('CreateML', LabelFileFormat.CREATE_ML)
        self.output_format_combo.addItem('COCO', LabelFileFormat.COCO)
        self.output_format_combo.addItem('CSV', LabelFileFormat.CSV)
        
        # Set current format
        if self.label_file_format == LabelFileFormat.PASCAL_VOC:
            self.output_format_combo.setCurrentIndex(0)
        elif self.label_file_format == LabelFileFormat.YOLO:
            self.output_format_combo.setCurrentIndex(1)
        elif self.label_file_format == LabelFileFormat.CREATE_ML:
            self.output_format_combo.setCurrentIndex(2)
        elif self.label_file_format == LabelFileFormat.COCO:
            self.output_format_combo.setCurrentIndex(3)
        elif self.label_file_format == LabelFileFormat.CSV:
            self.output_format_combo.setCurrentIndex(4)
        
        self.output_format_combo.currentIndexChanged.connect(self.on_output_format_changed)
        
        format_layout.addWidget(self.output_format_combo)
        format_group.setLayout(format_layout)
        main_layout.addWidget(format_group)
        
        main_layout.addStretch()
        main_container.setLayout(main_layout)
        
        dock.setWidget(main_container)
        return dock
    
    def on_output_format_changed(self, index):
        """Handle output format change from combo box"""
        format_data = self.output_format_combo.itemData(index)
        if format_data:
            self.set_format(format_data)
            self.set_dirty()

    def queue_event(self, function):
        QTimer.singleShot(0, function)

    def status(self, message, delay=5000):
        self.statusBar().showMessage(message, delay)

    def reset_state(self):
        self.items_to_shapes.clear()
        self.shapes_to_items.clear()
        self.label_list.clear()
        self.file_path = None
        self.image_data = None
        self.label_file = None
        self.canvas.reset_state()
        self.label_coordinates.clear()
        self.combo_box.cb.clear()

    def current_item(self):
        items = self.label_list.selectedItems()
        if items:
            return items[0]
        return None

    def add_recent_file(self, file_path):
        if file_path in self.recent_files:
            self.recent_files.remove(file_path)
        elif len(self.recent_files) >= self.max_recent:
            self.recent_files.pop()
        self.recent_files.insert(0, file_path)

    def beginner(self):
        return self._beginner

    def advanced(self):
        return not self.beginner()

    def show_tutorial_dialog(self, browser='default', link=None):
        if link is None:
            link = self.screencast

        if browser.lower() == 'default':
            wb.open(link, new=2)
        elif browser.lower() == 'chrome' and self.os_name == 'Windows':
            if shutil.which(browser.lower()):  # 'chrome' not in wb._browsers in windows
                wb.register('chrome', None, wb.BackgroundBrowser('chrome'))
            else:
                chrome_path = "D:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe"
                if os.path.isfile(chrome_path):
                    wb.register('chrome', None, wb.BackgroundBrowser(chrome_path))
            try:
                wb.get('chrome').open(link, new=2)
            except:
                wb.open(link, new=2)
        elif browser.lower() in wb._browsers:
            wb.get(browser.lower()).open(link, new=2)

    def show_default_tutorial_dialog(self):
        """Show a simple tutorial dialog with basic instructions (English only)"""
        dialog = QDialog(self)
        dialog.setWindowTitle('Quick Start Guide')
        dialog.setMinimumSize(650, 550)
        
        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Welcome message
        welcome_label = QLabel('Welcome to LabelCraft!')
        welcome_label.setStyleSheet('font-size: 16px; font-weight: bold;')
        welcome_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(welcome_label)
        
        # Basic steps section
        steps_title = QLabel('<b>Basic Annotation Steps:</b>')
        steps_title.setStyleSheet('font-size: 13px; font-weight: bold; margin-top: 10px;')
        main_layout.addWidget(steps_title)
        
        steps_text = QLabel(
            '<b>1. Create/Open Project:</b> File → New Project or Open Project<br>'
            '<b>2. Add Images:</b> Click "+ Add Images" or "+ Add Folder" in the bottom panel<br>'
            '<b>3. Annotate:</b> Double-click an image, then press \'W\' to draw bounding boxes<br>'
            '<b>4. Save:</b> Press Ctrl+S to save annotations (auto-saves when moving to next image)<br>'
            '<b>5. Export:</b> Output → Export to convert annotations to desired format'
        )
        steps_text.setWordWrap(True)
        steps_text.setStyleSheet('font-size: 12px; line-height: 1.6; padding-left: 10px;')
        main_layout.addWidget(steps_text)
        
        # Tips section
        tips_title = QLabel('<b>Helpful Tips:</b>')
        tips_title.setStyleSheet('font-size: 13px; font-weight: bold; margin-top: 10px;')
        main_layout.addWidget(tips_title)
        
        tips_text = QLabel(
            '<b>• Shortcuts:</b> Help → Keyboard shortcuts to view all shortcuts<br>'
            '<b>• Labels:</b> Use the right panel to filter and manage labels<br>'
            '<b>• Navigation:</b> Mouse wheel to zoom, drag to pan<br>'
            '<b>• Brightness:</b> Adjust image brightness with slider in toolbar'
        )
        tips_text.setWordWrap(True)
        tips_text.setStyleSheet('font-size: 12px; line-height: 1.6; padding-left: 10px;')
        main_layout.addWidget(tips_text)
        
        # More info section
        more_info_title = QLabel('<b>For more detailed documentation:</b>')
        more_info_title.setStyleSheet('font-size: 13px; font-weight: bold; margin-top: 10px;')
        main_layout.addWidget(more_info_title)
        
        github_link = QLabel(
            '• <a href="https://github.com/syd168/LabelCraft">Visit our GitHub repository for complete tutorials and examples</a><br>'
            '• <a href="https://github.com/syd168/LabelCraft/blob/master/README.md">Documentation & Tutorials</a><br>'
            '• <a href="https://github.com/syd168/LabelCraft/issues">Report Issues</a>'
        )
        github_link.setWordWrap(True)
        github_link.setOpenExternalLinks(True)
        github_link.setStyleSheet('font-size: 12px; line-height: 1.6; padding-left: 10px;')
        main_layout.addWidget(github_link)
        
        main_layout.addStretch()
        
        # Close button
        button_box = QDialogButtonBox(QDialogButtonBox.Close)
        button_box.rejected.connect(dialog.reject)
        main_layout.addWidget(button_box)
        
        dialog.setLayout(main_layout)
        dialog.exec()

    def show_info_dialog(self):
        """Show information about the application"""
        from libs.__init__ import __version__
        
        # Create a rich text dialog with project information
        dialog = QDialog(self)
        dialog.setWindowTitle(self.get_str('aboutTitle'))
        dialog.setMinimumSize(600, 500)
        
        # Main layout
        main_layout = QVBoxLayout()
        
        # Title and logo section
        title_layout = QHBoxLayout()
        
        # Try to load icon
        icon_label = QLabel()
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'resources', 'icons', 'app.png')
        if os.path.exists(icon_path):
            pixmap = QPixmap(icon_path)
            if not pixmap.isNull():
                icon_label.setPixmap(pixmap.scaled(64, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            icon_label.setText('📦')
            icon_label.setStyleSheet('font-size: 48px;')
        title_layout.addWidget(icon_label)
        title_layout.addSpacing(20)
        
        # Title text
        title_text = QVBoxLayout()
        app_name_label = QLabel('LabelCraft')
        app_name_label.setStyleSheet('font-size: 24px; font-weight: bold;')
        version_label = QLabel(f'{self.get_str("aboutVersion")} {__version__}')
        title_text.addWidget(app_name_label)
        title_text.addWidget(version_label)
        title_layout.addLayout(title_text)
        title_layout.addStretch()
        
        main_layout.addLayout(title_layout)
        main_layout.addSpacing(20)
        
        # Description
        desc_label = QLabel(self.get_str('aboutDescription'))
        desc_label.setWordWrap(True)
        main_layout.addWidget(desc_label)
        main_layout.addSpacing(15)
        
        # Features section
        features_title = QLabel(self.get_str('aboutFeatures'))
        features_title.setStyleSheet('font-weight: bold;')
        main_layout.addWidget(features_title)
        
        features_text = QLabel(
            f'{self.get_str("aboutFeatureMultiFormat")}<br>'
            f'{self.get_str("aboutFeatureSmartAnnotation")}<br>'
            f'{self.get_str("aboutFeatureProjectManagement")}<br>'
            f'{self.get_str("aboutFeatureWorkflow")}<br>'
            f'{self.get_str("aboutFeatureImageAdjustment")}<br>'
            f'{self.get_str("aboutFeatureMultilingual")}'
        )
        features_text.setWordWrap(True)
        main_layout.addWidget(features_text)
        main_layout.addSpacing(15)
        
        # Technical info
        tech_title = QLabel(self.get_str('aboutTechInfo'))
        tech_title.setStyleSheet('font-weight: bold;')
        main_layout.addWidget(tech_title)
        
        tech_info = QLabel(
            f'{self.get_str("aboutPythonVersion")}: {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}<br>'
            f'{self.get_str("aboutGUIFramework")}<br>'
            f'{self.get_str("aboutDevLanguage")}<br>'
            f'{self.get_str("aboutLicense")}'
        )
        tech_info.setWordWrap(True)
        main_layout.addWidget(tech_info)
        main_layout.addSpacing(15)
        
        # Links section
        links_title = QLabel(self.get_str('aboutLinks'))
        links_title.setStyleSheet('font-weight: bold;')
        main_layout.addWidget(links_title)
        
        links_text = QLabel(
            f'• <a href="https://github.com/syd168/LabelCraft">{self.get_str("aboutGitHubHome")}</a><br>'
            f'• <a href="https://github.com/syd168/LabelCraft/issues">{self.get_str("aboutIssueTracker")}</a><br>'
            f'• <a href="https://github.com/syd168/LabelCraft/blob/master/README.md">{self.get_str("aboutDocumentation")}</a>'
        )
        links_text.setWordWrap(True)
        links_text.setOpenExternalLinks(True)
        main_layout.addWidget(links_text)
        
        main_layout.addStretch()
        
        # Close button
        button_box = QDialogButtonBox(QDialogButtonBox.Close)
        button_box.rejected.connect(dialog.reject)
        main_layout.addWidget(button_box)
        
        dialog.setLayout(main_layout)
        dialog.exec()

    def show_shortcuts_dialog(self):
        """Show a dialog with all keyboard shortcuts"""

        # Define title style (theme-adaptive, no hardcoded colors)
        title_style = """
            QLabel {
                font-size: 14px;
                font-weight: bold;
                padding: 5px 0px;
            }
        """

        # Create dialog
        dialog = QDialog(self)
        dialog.setWindowTitle(self.get_str('shortcutTitle'))
        dialog.setMinimumSize(700, 600)

        # Create main layout
        main_layout = QVBoxLayout()

        # Create scroll area for better viewing
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)

        # Helper function to create shortcut row (using default style)
        def create_shortcut_row(action_text, key_text):
            row = QHBoxLayout()
            action_label = QLabel(action_text)
            key_label = QLabel(key_text)
            row.addWidget(action_label)
            row.addStretch()
            row.addWidget(key_label)
            return row

        # Section 1: File Operations
        section1_title = QLabel(self.get_str('shortcutFileOps'))
        section1_title.setStyleSheet(title_style)
        scroll_layout.addWidget(section1_title)

        scroll_layout.addLayout(create_shortcut_row(self.get_str('openFile'), 'Ctrl+O'))
        scroll_layout.addLayout(create_shortcut_row(self.get_str('openDir'), 'Ctrl+U'))
        scroll_layout.addLayout(create_shortcut_row(self.get_str('save'), 'Ctrl+S'))
        scroll_layout.addLayout(create_shortcut_row(self.get_str('nextImg'), 'D'))
        scroll_layout.addLayout(create_shortcut_row(self.get_str('prevImg'), 'A'))

        scroll_layout.addSpacing(15)

        # Section 2: Edit Operations
        section2_title = QLabel(self.get_str('shortcutEditOps'))
        scroll_layout.addWidget(section2_title)

        scroll_layout.addLayout(create_shortcut_row(self.get_str('crtBox'), 'W'))
        scroll_layout.addLayout(create_shortcut_row(self.get_str('delBox'), 'Delete'))
        scroll_layout.addLayout(create_shortcut_row(self.get_str('dupBox'), 'Ctrl+D'))
        scroll_layout.addLayout(create_shortcut_row(self.get_str('editLabel'), 'Ctrl+E'))
        scroll_layout.addLayout(create_shortcut_row(self.get_str('editBox'), 'Ctrl+J'))

        scroll_layout.addSpacing(15)

        # Section 3: View Operations
        section3_title = QLabel(self.get_str('shortcutViewOps'))
        scroll_layout.addWidget(section3_title)

        scroll_layout.addLayout(create_shortcut_row(self.get_str('zoomin'), 'Ctrl++'))
        scroll_layout.addLayout(create_shortcut_row(self.get_str('zoomout'), 'Ctrl+-'))
        scroll_layout.addLayout(create_shortcut_row(self.get_str('originalsize'), 'Ctrl+='))
        scroll_layout.addLayout(create_shortcut_row(self.get_str('fitWin'), 'Ctrl+F'))
        scroll_layout.addLayout(create_shortcut_row(self.get_str('fitWidth'), 'Ctrl+Shift+F'))

        scroll_layout.addSpacing(15)

        # Section 4: Brightness
        section4_title = QLabel(self.get_str('shortcutBrightness'))
        scroll_layout.addWidget(section4_title)

        scroll_layout.addLayout(create_shortcut_row(self.get_str('lightbrighten'), 'Ctrl+Shift++'))
        scroll_layout.addLayout(create_shortcut_row(self.get_str('lightdarken'), 'Ctrl+Shift+-'))
        scroll_layout.addLayout(create_shortcut_row(self.get_str('lightreset'), 'Ctrl+Shift+='))

        scroll_layout.addSpacing(15)

        # Section 5: Other
        section5_title = QLabel(self.get_str('shortcutOther'))
        scroll_layout.addWidget(section5_title)

        scroll_layout.addLayout(create_shortcut_row(self.get_str('advancedMode'), 'Ctrl+Shift+A'))
        scroll_layout.addLayout(create_shortcut_row(self.get_str('hideAllBox'), 'Ctrl+H'))
        scroll_layout.addLayout(create_shortcut_row(self.get_str('showAllBox'), 'Ctrl+A'))
        scroll_layout.addLayout(create_shortcut_row(self.get_str('singleClsMode'), 'Ctrl+Shift+S'))
        scroll_layout.addLayout(create_shortcut_row(self.get_str('displayLabel'), 'Ctrl+Shift+P'))

        scroll_layout.addStretch()

        scroll_area.setWidget(scroll_content)
        main_layout.addWidget(scroll_area)

        # Add close button
        button_box = QDialogButtonBox(QDialogButtonBox.Close)
        button_box.rejected.connect(dialog.reject)
        main_layout.addWidget(button_box)

        dialog.setLayout(main_layout)
        dialog.exec()

    def change_language(self, locale):
        """Change the application language (uses new i18n engine)"""
        # Use new i18n engine for dynamic switching
        self.i18n.set_language(locale)
        
        # Also update old string bundle for backward compatibility
        self.string_bundle = StringBundle.get_bundle(locale)

        # Update menu titles
        self.menus.file.setTitle(self.get_str('menu_file'))
        self.menus.edit.setTitle(self.get_str('menu_edit'))
        self.menus.view.setTitle(self.get_str('menu_view'))
        self.menus.output.setTitle(self.get_str('menu_output'))
        self.menus.language.setTitle(self.get_str('menu_lang'))
        self.menus.help.setTitle(self.get_str('menu_help'))
        self.menus.recentFiles.setTitle(self.get_str('menu_openRecent'))
        self.menus.recentProjects.setTitle(self.get_str('menu_recentProjects'))

        # Update dock titles
        self.dock.setWindowTitle(self.get_str('boxLabelText'))
        # Note: file_list is now part of the main dock, no separate file_dock
        if hasattr(self, 'output_settings_widget'):
            self.output_settings_widget.setWindowTitle(self.get_str('outputDir'))

        # Update checkbox text
        self.use_default_label_checkbox.setText(self.get_str('useDefaultLabel'))
        self.diffc_button.setText(self.get_str('useDifficult'))

        # Update actions text
        self.auto_saving.setText(self.get_str('autoSaveMode'))
        self.single_class_mode.setText(self.get_str('singleClsMode'))
        self.display_label_option.setText(self.get_str('displayLabel'))
        
        # Update export action
        if hasattr(self.actions, 'exportAnnotations'):
            self.actions.exportAnnotations.setText(self.get_str('exportAnnotations'))
            self.actions.exportAnnotations.setToolTip(self.get_str('exportAnnotationsDetail'))
        
        # Update project management actions
        if hasattr(self.actions, 'newProject'):
            self.actions.newProject.setText(self.get_str('newProject'))
            self.actions.newProject.setToolTip(self.get_str('newProjectDetail'))
        if hasattr(self.actions, 'openProject'):
            self.actions.openProject.setText(self.get_str('openProject'))
            self.actions.openProject.setToolTip(self.get_str('openProjectDetail'))
        if hasattr(self.actions, 'editProject'):
            self.actions.editProject.setText(self.get_str('editProject'))
            self.actions.editProject.setToolTip(self.get_str('editProjectDetail'))
        if hasattr(self.actions, 'saveProject'):
            self.actions.saveProject.setText(self.get_str('saveProject'))
            self.actions.saveProject.setToolTip(self.get_str('saveProjectDetail'))
        if hasattr(self.actions, 'closeProject'):
            self.actions.closeProject.setText(self.get_str('closeProject'))
            self.actions.closeProject.setToolTip(self.get_str('closeProjectDetail'))
        
        # Update right panel group boxes and widgets
        # Find all QGroupBox widgets in the dock and update their titles
        for widget in self.dock.findChildren(QGroupBox):
            title = widget.title()
            if title == '输出设置' or title == 'Output Settings':
                widget.setTitle(self.get_str('outputSettings'))
            elif title == '标签过滤' or title == 'Label Filter':
                widget.setTitle(self.get_str('labelFilter'))
            elif title == '标签列表' or title == 'Label List':
                widget.setTitle(self.get_str('labelList'))
            elif title == '已完成标注' or title == 'Completed Annotations':
                widget.setTitle(self.get_str('completedAnnotations'))
        
        # Update output path and format labels
        if hasattr(self, 'output_dir_label'):
            # Find the label before output_dir_label to update its text
            parent_widget = self.output_dir_label.parentWidget()
            if parent_widget:
                for child in parent_widget.findChildren(QLabel):
                    if child.text() == '输出路径：' or child.text() == 'Output Path:':
                        child.setText(self.get_str('outputPath'))
                    elif child.text() == '输出格式：' or child.text() == 'Output Format:':
                        child.setText(self.get_str('outputFormat'))
        
        # Update zoom and light widget tooltips
        if hasattr(self, 'zoom_widget'):
            self.zoom_widget.update_tooltip(self.get_str('zoomin'))
        if hasattr(self, 'light_widget'):
            self.light_widget.update_tooltip(self.get_str('lightWidgetTitle'))
        
        # Update pending queue buttons
        if hasattr(self, 'pending_list_widget'):
            for btn in self.pending_list_widget.parentWidget().findChildren(QPushButton):
                text = btn.text()
                if text == '+ 添加图像' or text == '+ Add Images':
                    btn.setText(self.get_str('addImages'))
                elif text == '+ 添加文件夹' or text == '+ Add Folder':
                    btn.setText(self.get_str('addFolder'))
                elif text == '清空' or text == 'Clear':
                    btn.setText(self.get_str('clearPending'))

        # Update toolbar actions tooltips and text
        if hasattr(self.actions, 'open'):
            self.actions.open.setText(self.get_str('openFile'))
            self.actions.open.setToolTip(self.get_str('openFileDetail'))
        if hasattr(self.actions, 'openDir'):
            self.actions.openDir.setText(self.get_str('openDir'))
        if hasattr(self.actions, 'changeSaveDir'):
            self.actions.changeSaveDir.setText(self.get_str('changeSaveDir'))
        if hasattr(self.actions, 'openAnnotation'):
            self.actions.openAnnotation.setText(self.get_str('openAnnotation'))
            self.actions.openAnnotation.setToolTip(self.get_str('openAnnotationDetail'))
        if hasattr(self.actions, 'copyPrevBounding'):
            self.actions.copyPrevBounding.setText(self.get_str('copyPrevBounding'))
        if hasattr(self.actions, 'save'):
            self.actions.save.setText(self.get_str('save'))
            self.actions.save.setToolTip(self.get_str('saveDetail'))
        if hasattr(self.actions, 'save_format'):
            # Update save format based on current format
            if self.label_file_format == LabelFileFormat.PASCAL_VOC:
                self.actions.save_format.setText('&PascalVOC')
            elif self.label_file_format == LabelFileFormat.YOLO:
                self.actions.save_format.setText('&YOLO')
            elif self.label_file_format == LabelFileFormat.CREATE_ML:
                self.actions.save_format.setText('&CreateML')
            self.actions.save_format.setToolTip(self.get_str('changeSaveFormat'))
        if hasattr(self.actions, 'quit'):
            self.actions.quit.setText(self.get_str('quit'))
            self.actions.quit.setToolTip(self.get_str('quitApp'))
        if hasattr(self.actions, 'create'):
            self.actions.create.setText(self.get_str('crtBox'))
            self.actions.create.setToolTip(self.get_str('crtBoxDetail'))
        if hasattr(self.actions, 'delete'):
            self.actions.delete.setText(self.get_str('delBox'))
            self.actions.delete.setToolTip(self.get_str('delBoxDetail'))
        if hasattr(self.actions, 'copy'):
            self.actions.copy.setText(self.get_str('dupBox'))
            self.actions.copy.setToolTip(self.get_str('dupBoxDetail'))
        if hasattr(self.actions, 'edit'):
            self.actions.edit.setText(self.get_str('editLabel'))
            self.actions.edit.setToolTip(self.get_str('editLabelDetail'))
        if hasattr(self.actions, 'createMode'):
            self.actions.createMode.setText(self.get_str('crtBox'))
            self.actions.createMode.setToolTip(self.get_str('crtBoxDetail'))
        if hasattr(self.actions, 'editMode'):
            self.actions.editMode.setText(self.get_str('editBox'))
            self.actions.editMode.setToolTip(self.get_str('editBoxDetail'))
        if hasattr(self.actions, 'shapeLineColor'):
            self.actions.shapeLineColor.setText(self.get_str('shapeLineColor'))
            self.actions.shapeLineColor.setToolTip(self.get_str('shapeLineColorDetail'))
        if hasattr(self.actions, 'shapeFillColor'):
            self.actions.shapeFillColor.setText(self.get_str('shapeFillColor'))
            self.actions.shapeFillColor.setToolTip(self.get_str('shapeFillColorDetail'))
        if hasattr(self.actions, 'lineColor'):
            self.actions.lineColor.setText(self.get_str('boxLineColor'))
            self.actions.lineColor.setToolTip(self.get_str('boxLineColorDetail'))
        if hasattr(self.actions, 'drawSquares'):
            self.actions.drawSquares.setText(self.get_str('drawSquares'))

        # Update zoom actions
        if hasattr(self.actions, 'zoomIn'):
            self.actions.zoomIn.setText(self.get_str('zoomin'))
            self.actions.zoomIn.setToolTip(self.get_str('zoominDetail'))
        if hasattr(self.actions, 'zoomOut'):
            self.actions.zoomOut.setText(self.get_str('zoomout'))
            self.actions.zoomOut.setToolTip(self.get_str('zoomoutDetail'))
        if hasattr(self.actions, 'zoomOrg'):
            self.actions.zoomOrg.setText(self.get_str('originalsize'))
            self.actions.zoomOrg.setToolTip(self.get_str('originalsizeDetail'))
        if hasattr(self.actions, 'fitWindow'):
            self.actions.fitWindow.setText(self.get_str('fitWin'))
            self.actions.fitWindow.setToolTip(self.get_str('fitWinDetail'))
        if hasattr(self.actions, 'fitWidth'):
            self.actions.fitWidth.setText(self.get_str('fitWidth'))
            self.actions.fitWidth.setToolTip(self.get_str('fitWidthDetail'))

        # Update light actions
        if hasattr(self.actions, 'lightBrighten'):
            self.actions.lightBrighten.setText(self.get_str('lightbrighten'))
            self.actions.lightBrighten.setToolTip(self.get_str('lightbrightenDetail'))
        if hasattr(self.actions, 'lightDarken'):
            self.actions.lightDarken.setText(self.get_str('lightdarken'))
            self.actions.lightDarken.setToolTip(self.get_str('lightdarkenDetail'))
        if hasattr(self.actions, 'lightOrg'):
            self.actions.lightOrg.setText(self.get_str('lightreset'))
            self.actions.lightOrg.setToolTip(self.get_str('lightresetDetail'))

        # Update other actions
        if hasattr(self.actions, 'verify'):
            self.actions.verify.setText(self.get_str('verifyImg'))
            self.actions.verify.setToolTip(self.get_str('verifyImgDetail'))
        if hasattr(self.actions, 'nextImg'):
            self.actions.nextImg.setText(self.get_str('nextImg'))
            self.actions.nextImg.setToolTip(self.get_str('nextImgDetail'))
        if hasattr(self.actions, 'prevImg'):
            self.actions.prevImg.setText(self.get_str('prevImg'))
            self.actions.prevImg.setToolTip(self.get_str('prevImgDetail'))
        if hasattr(self.actions, 'hideAll'):
            self.actions.hideAll.setText(self.get_str('hideAllBox'))
            self.actions.hideAll.setToolTip(self.get_str('hideAllBoxDetail'))
        if hasattr(self.actions, 'showAll'):
            self.actions.showAll.setText(self.get_str('showAllBox'))
            self.actions.showAll.setToolTip(self.get_str('showAllBoxDetail'))
        if hasattr(self.actions, 'labels'):
            self.actions.labels.setText(self.get_str('showHide'))
        if hasattr(self.actions, 'resetAll'):
            self.actions.resetAll.setText(self.get_str('resetAll'))
            self.actions.resetAll.setToolTip(self.get_str('resetAllDetail'))
        if hasattr(self.actions, 'deleteImg'):
            self.actions.deleteImg.setText(self.get_str('deleteImg'))
            self.actions.deleteImg.setToolTip(self.get_str('deleteImgDetail'))
        if hasattr(self.actions, 'advancedMode'):
            self.actions.advancedMode.setText(self.get_str('advancedMode'))
            self.actions.advancedMode.setToolTip(self.get_str('advancedModeDetail'))

        # Update help actions
        if hasattr(self, 'show_shortcut'):
            self.show_shortcut.setText(self.get_str('shortcut'))
        
        for action in self.menus.help.actions():
            if 'Tutorial' in action.text() or '教学' in action.text() or 'チュートリアル' in action.text():
                action.setText(self.get_str('tutorialDefault'))
                action.setToolTip(self.get_str('tutorialDetail'))
            elif 'Information' in action.text() or '信息' in action.text() or '情報' in action.text():
                action.setText(self.get_str('info'))

        # Update labels widget (show/hide action)
        labels_action = None
        for action in self.menus.view.actions():
            if 'Show/Hide' in action.text() or '显示/隐藏' in action.text() or '表示/非表示' in action.text():
                action.setText(self.get_str('showHide'))
                break

        # Update window title if file is loaded
        if self.file_path:
            counter = self.counter_str()
            self.setWindowTitle(__appname__ + ' ' + self.file_path + ' ' + counter)
        else:
            self.setWindowTitle(__appname__)

        # Rebuild toolbar to update brightness and zoom labels
        self.populate_mode_actions()

        # Refresh the UI
        self.update()
        print(f'Language changed to: {locale}')

    def create_shape(self):
        assert self.beginner()
        self.canvas.set_editing(False)
        self.actions.create.setEnabled(False)

    def toggle_drawing_sensitive(self, drawing=True):
        """In the middle of drawing, toggling between modes should be disabled."""
        self.actions.editMode.setEnabled(not drawing)
        if not drawing and self.beginner():
            # Cancel creation.
            print('Cancel creation.')
            self.canvas.set_editing(True)
            self.canvas.restore_cursor()
            self.actions.create.setEnabled(True)

    def toggle_draw_mode(self, edit=True):
        self.canvas.set_editing(edit)
        self.actions.createMode.setEnabled(edit)
        self.actions.editMode.setEnabled(not edit)

    def set_create_mode(self):
        assert self.advanced()
        self.toggle_draw_mode(False)

    def set_edit_mode(self):
        assert self.advanced()
        self.toggle_draw_mode(True)
        self.label_selection_changed()

    def update_file_menu(self):
        curr_file_path = self.file_path

        def exists(filename):
            return os.path.exists(filename)

        menu = self.menus.recentFiles
        menu.clear()
        files = [f for f in self.recent_files if f !=
                 curr_file_path and exists(f)]
        for i, f in enumerate(files):
            icon = new_icon('labels')
            action = QAction(
                icon, '&%d %s' % (i + 1, QFileInfo(f).fileName()), self)
            action.triggered.connect(partial(self.load_recent, f))
            menu.addAction(action)

    def pop_label_list_menu(self, point):
        self.menus.labelList.exec_(self.label_list.mapToGlobal(point))

    def edit_label(self):
        # Allow editing label by double-clicking on shape (from canvas signal)
        # or from label list double-click (only in edit mode)
        item = self.current_item()
        if not item:
            return
        text = self.label_dialog.pop_up(item.text())
        if text is not None:
            item.setText(text)
            item.setBackground(generate_color_by_text(text))
            self.set_dirty()
            self.update_combo_box()

    # Tzutalin 20160906 : Add file list and dock to move faster
    def file_item_double_clicked(self, item=None):
        """Double click on completed annotation item to load image and annotation"""
        if not item:
            return
        
        # Auto save before switching to another image
        if not self.auto_save_if_enabled():
            return  # User cancelled or no save path
        
        # Get annotation filename
        anno_filename = ustr(item.text())
        base_name = os.path.splitext(anno_filename)[0]
        
        # Determine annotation directory
        anno_dir = None
        if self.current_project and self.current_project.annotation_dir:
            anno_dir = os.path.join(self.current_project.annotation_dir, 'annotations')
            if not os.path.exists(anno_dir):
                anno_dir = self.current_project.annotation_dir
        elif self.default_save_dir:
            anno_dir = os.path.join(self.default_save_dir, 'annotations')
            if not os.path.exists(anno_dir):
                anno_dir = self.default_save_dir
        
        if not anno_dir or not os.path.exists(anno_dir):
            QMessageBox.warning(self, self.get_str('errorTitle'), self.get_str('annoDirNotFound'))
            return
        
        # Find corresponding image file
        # Try common image extensions
        image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tif', '.tiff', '.gif', '.webp']
        image_path = None
        
        # First, try in images/ subdirectory under annotation_dir (standard structure)
        # annotation_dir is like: /path/to/database/annotations
        # So images should be in: /path/to/database/images
        if anno_dir:
            database_dir = os.path.dirname(anno_dir)  # Get parent of annotations/
            images_dir = os.path.join(database_dir, 'images')
            if os.path.exists(images_dir):
                for ext in image_extensions:
                    candidate = os.path.join(images_dir, base_name + ext)
                    if os.path.exists(candidate):
                        image_path = candidate
                        break
        
        # If not found, try images/ under project_dir
        if not image_path and self.current_project and self.current_project.project_dir:
            images_dir = os.path.join(self.current_project.project_dir, 'images')
            if os.path.exists(images_dir):
                for ext in image_extensions:
                    candidate = os.path.join(images_dir, base_name + ext)
                    if os.path.exists(candidate):
                        image_path = candidate
                        break
        
        # If still not found, try annotation directory itself
        if not image_path and anno_dir:
            for ext in image_extensions:
                candidate = os.path.join(anno_dir, base_name + ext)
                if os.path.exists(candidate):
                    image_path = candidate
                    break
        
        if not image_path:
            QMessageBox.warning(
                self, 
                self.get_str('warningTitle'), 
                self.get_str('imageNotFound').format(base_name) + '\n\n'
                '请在 images/ 目录或项目根目录中添加该图像。'
            )
            return
        
        # Load the image and annotation
        print(f'Loading image: {image_path}')
        self.load_file(image_path)
        
        # After loading, refresh the completed annotations list
        # because load_file may have cleared it
        self.update_completed_annotations_list()
    
    def pending_item_double_clicked(self, item=None):
        """Double click on pending image to start annotation"""
        image_path = ustr(item.text())
        if image_path and os.path.exists(image_path):
            # Auto save before switching to another image
            if not self.auto_save_if_enabled():
                return  # User cancelled or no save path
            
            self.load_file(image_path)
            
            # After loading, refresh the completed annotations list
            # because load_file may have cleared it
            self.update_completed_annotations_list()
    
    def add_images_to_pending(self):
        """Add individual images to pending queue"""
        if not self.current_project:
            QMessageBox.warning(self, self.get_str('warningTitle'), self.get_str('pleaseCreateProject'))
            return
        
        formats = ['*.%s' % fmt.data().decode("ascii").lower() for fmt in QImageReader.supportedImageFormats()]
        filters = "Image files (%s)" % ' '.join(formats)
        
        file_paths, _ = QFileDialog.getOpenFileNames(
            self,
            self.get_str('addImages'),
            self.current_project.project_dir or '.',
            filters
        )
        
        if file_paths:
            for file_path in file_paths:
                file_path = ustr(file_path)
                # Check if already in pending list
                already_exists = False
                for i in range(self.pending_list_widget.count()):
                    if self.pending_list_widget.item(i).text() == file_path:
                        already_exists = True
                        break
                
                if not already_exists:
                    self.pending_list_widget.addItem(file_path)
            
            QMessageBox.information(self, self.get_str('successTitle'), self.get_str('imagesAdded').format(len(file_paths)))
    
    def add_folder_to_pending(self):
        """Add all images from a folder to pending queue"""
        
        if not self.current_project:
            QMessageBox.warning(self, self.get_str('warningTitle'), self.get_str('pleaseCreateProject'))
            return
        
        dir_path = QFileDialog.getExistingDirectory(
            self,
            '选择图像文件夹',
            self.current_project.project_dir or '.',
            QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks
        )
        
        if not dir_path:
            return
        
        dir_path = ustr(dir_path)
        images = self.scan_all_images(dir_path)
        
        added_count = 0
        for image_path in images:
            # Check if already in pending list
            already_exists = False
            for i in range(self.pending_list_widget.count()):
                if self.pending_list_widget.item(i).text() == image_path:
                    already_exists = True
                    break
            
            if not already_exists:
                self.pending_list_widget.addItem(image_path)
                added_count += 1
        
        QMessageBox.information(self, self.get_str('successTitle'), self.get_str('folderImagesAdded').format(added_count))
    
    def clear_pending_queue(self):
        """Clear all items from pending queue"""
        
        if self.pending_list_widget.count() == 0:
            return
        
        reply = QMessageBox.question(
            self,
            self.get_str('confirmTitle'),
            self.get_str('confirmClearPending'),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.pending_list_widget.clear()
            QMessageBox.information(self, self.get_str('successTitle'), self.get_str('pendingCleared'))
    
    def remove_from_pending_queue(self, image_path):
        """Remove an image from pending queue after annotation is saved"""
        for i in range(self.pending_list_widget.count()):
            if self.pending_list_widget.item(i).text() == image_path:
                self.pending_list_widget.takeItem(i)
                print(f'Removed from pending queue: {os.path.basename(image_path)}')
                break
    
    def mark_as_annotated(self, image_path):
        """Mark an image as annotated by changing its color to green in pending list"""
        for i in range(self.pending_list_widget.count()):
            item = self.pending_list_widget.item(i)
            if item.text() == image_path:
                # Set foreground color to green (theme-adaptive)
                item.setForeground(QColor(0, 180, 0))  # Green color
                # Optionally make it bold
                font = item.font()
                font.setBold(True)
                item.setFont(font)
                print(f'Marked as annotated: {os.path.basename(image_path)}')
                break
    
    def update_completed_annotations_list(self):
        """Update the completed annotations list by scanning annotations directory"""
        # Determine annotation directory
        anno_dir = None
        if self.current_project and self.current_project.annotation_dir:
            # Use standard directory structure: base_dir/annotations
            anno_dir = os.path.join(self.current_project.annotation_dir, 'annotations')
        elif self.default_save_dir and os.path.exists(self.default_save_dir):
            # Use standard directory structure: base_dir/annotations
            anno_dir = os.path.join(self.default_save_dir, 'annotations')
        
        if not anno_dir:
            return
        
        if not os.path.exists(anno_dir):
            # If annotations subdirectory doesn't exist, try the base directory (for backward compatibility)
            if self.current_project and self.current_project.annotation_dir:
                anno_dir = self.current_project.annotation_dir
            elif self.default_save_dir:
                anno_dir = self.default_save_dir
            else:
                return
        
        if not os.path.exists(anno_dir):
            return
        
        # Clear current list
        self.file_list_widget.clear()
        
        # Scan annotation files
        ext_map = {
            LabelFileFormat.PASCAL_VOC: '.xml',
            LabelFileFormat.YOLO: '.txt',
            LabelFileFormat.CREATE_ML: '.json'
        }
        ext = ext_map.get(self.label_file_format, '.xml')
        
        try:
            for filename in os.listdir(anno_dir):
                # Skip non-annotation files
                if filename.lower() == 'classes.txt':
                    continue
                if filename.lower().endswith(ext):
                    self.file_list_widget.addItem(filename)
            
            print(f'Updated completed annotations list: {self.file_list_widget.count()} items')
        except Exception as e:
            print(f'Error updating completed annotations list: {e}')

    # Add chris
    def button_state(self, item=None):
        """ Function to handle difficult examples
        Update on each object """
        if not self.canvas.editing():
            return

        item = self.current_item()
        if not item:  # If not selected Item, take the first one
            item = self.label_list.item(self.label_list.count() - 1)

        difficult = self.diffc_button.isChecked()

        # Use get() to avoid KeyError if mapping is out of sync
        shape = self.items_to_shapes.get(item)
        if not shape:
            return
        
        # Checked and Update
        if difficult != shape.difficult:
            shape.difficult = difficult
            self.set_dirty()
        else:  # User probably changed item visibility
            self.canvas.set_shape_visible(shape, item.checkState() == Qt.CheckState.Checked)

    # React to canvas signals.
    def shape_selection_changed(self, selected=False):
        if self._no_selection_slot:
            self._no_selection_slot = False
        else:
            shape = self.canvas.selected_shape
            if shape:
                self.shapes_to_items[shape].setSelected(True)
            else:
                self.label_list.clearSelection()
        self.actions.delete.setEnabled(selected)
        self.actions.copy.setEnabled(selected)
        self.actions.edit.setEnabled(selected)
        self.actions.shapeLineColor.setEnabled(selected)
        self.actions.shapeFillColor.setEnabled(selected)

    def add_label(self, shape):
        shape.paint_label = self.display_label_option.isChecked()
        item = HashableQListWidgetItem(shape.label)
        item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
        item.setCheckState(Qt.CheckState.Checked)
        item.setBackground(generate_color_by_text(shape.label))
        self.items_to_shapes[item] = shape
        self.shapes_to_items[shape] = item
        self.label_list.addItem(item)
        for action in self.actions.onShapesPresent:
            action.setEnabled(True)
        self.update_combo_box()

    def remove_label(self, shape):
        if shape is None:
            # print('rm empty label')
            return
        item = self.shapes_to_items[shape]
        self.label_list.takeItem(self.label_list.row(item))
        del self.shapes_to_items[shape]
        del self.items_to_shapes[item]
        self.update_combo_box()

    def load_labels(self, shapes):
        s = []
        for label, points, line_color, fill_color, difficult in shapes:
            shape = Shape(label=label)
            for x, y in points:

                # Ensure the labels are within the bounds of the image. If not, fix them.
                x, y, snapped = self.canvas.snap_point_to_canvas(x, y)
                if snapped:
                    self.set_dirty()

                shape.add_point(QPointF(x, y))
            shape.difficult = difficult
            shape.close()
            s.append(shape)

            if line_color:
                shape.line_color = QColor(*line_color)
            else:
                shape.line_color = generate_color_by_text(label)

            if fill_color:
                shape.fill_color = QColor(*fill_color)
            else:
                shape.fill_color = generate_color_by_text(label)

            self.add_label(shape)
        self.update_combo_box()
        self.canvas.load_shapes(s)

    def update_combo_box(self):
        # Get labels from current image shapes for filtering
        # This ensures the filter combo box only shows labels present in the current image
        current_labels = set()
        for shape in self.canvas.shapes:
            if shape.label:
                current_labels.add(shape.label)
        
        # Convert to sorted list and add empty option for "show all"
        unique_text_list = sorted(list(current_labels))
        unique_text_list.insert(0, "")  # Empty option at the beginning
        
        self.combo_box.update_items(unique_text_list)

    def save_labels(self, annotation_file_path):
        annotation_file_path = ustr(annotation_file_path)
        if self.label_file is None:
            self.label_file = LabelFile()
            self.label_file.verified = self.canvas.verified

        def format_shape(s):
            return dict(label=s.label,
                        line_color=s.line_color.getRgb(),
                        fill_color=s.fill_color.getRgb(),
                        points=[(p.x(), p.y()) for p in s.points],
                        # add chris
                        difficult=s.difficult)

        shapes = [format_shape(shape) for shape in self.canvas.shapes]
        # Can add different annotation formats here
        try:
            if self.label_file_format == LabelFileFormat.PASCAL_VOC:
                if annotation_file_path[-4:].lower() != ".xml":
                    annotation_file_path += XML_EXT
                self.label_file.save_pascal_voc_format(annotation_file_path, shapes, self.file_path, self.image_data,
                                                       self.line_color.getRgb(), self.fill_color.getRgb())
            elif self.label_file_format == LabelFileFormat.YOLO:
                if annotation_file_path[-4:].lower() != ".txt":
                    annotation_file_path += TXT_EXT
                self.label_file.save_yolo_format(annotation_file_path, shapes, self.file_path, self.image_data,
                                                 self.label_hist,
                                                 self.line_color.getRgb(), self.fill_color.getRgb())
            elif self.label_file_format == LabelFileFormat.CREATE_ML:
                if annotation_file_path[-5:].lower() != ".json":
                    annotation_file_path += JSON_EXT
                self.label_file.save_create_ml_format(annotation_file_path, shapes, self.file_path, self.image_data,
                                                      self.label_hist, self.line_color.getRgb(),
                                                      self.fill_color.getRgb())
            elif self.label_file_format == LabelFileFormat.COCO:
                if annotation_file_path[-5:].lower() != ".json":
                    annotation_file_path += '.json'
                self.label_file.save_coco_format(annotation_file_path, shapes, self.file_path, self.image_data,
                                                self.label_hist, self.line_color.getRgb(),
                                                self.fill_color.getRgb())
            elif self.label_file_format == LabelFileFormat.CSV:
                if annotation_file_path[-4:].lower() != ".csv":
                    annotation_file_path += '.csv'
                self.label_file.save_csv_format(annotation_file_path, shapes, self.file_path, self.image_data,
                                               self.label_hist, self.line_color.getRgb(),
                                               self.fill_color.getRgb())
            else:
                self.label_file.save(annotation_file_path, shapes, self.file_path, self.image_data,
                                     self.line_color.getRgb(), self.fill_color.getRgb())
            print('Image:{0} -> Annotation:{1}'.format(self.file_path, annotation_file_path))
            return True
        except LabelFileError as e:
            self.error_message(u'Error saving label data', u'<b>%s</b>' % e)
            return False

    def copy_selected_shape(self):
        self.add_label(self.canvas.copy_selected_shape())
        # fix copy and delete
        self.shape_selection_changed(True)

    def combo_selection_changed(self, index):
        """
        Handle label filtering from combo box.
        
        When a label is selected:
        - If empty: show all shapes (check all items)
        - If specific label: hide other labels, only show matching shapes
        
        This allows users to focus on specific object types during annotation.
        
        Note: The selected label is also used as default for new annotations
        (see new_shape method).
        """
        text = self.combo_box.cb.itemText(index)
        
        # Save the selected label for use in new_shape
        if text:
            self.prev_label_text = text
            self.lastLabel = text
        
        # Filter the label list visibility by setting check states
        for i in range(self.label_list.count()):
            if text == "":
                # Empty selection: show all shapes
                self.label_list.item(i).setCheckState(Qt.CheckState.Checked)
            elif text != self.label_list.item(i).text():
                # Hide shapes with different labels
                self.label_list.item(i).setCheckState(Qt.CheckState.Unchecked)
            else:
                # Show shapes with matching label
                self.label_list.item(i).setCheckState(Qt.CheckState.Checked)

    def default_label_combo_selection_changed(self, index):
        if index >= 0 and index < len(self.label_hist):
            self.default_label = self.label_hist[index]

    def label_selection_changed(self):
        item = self.current_item()
        if item and self.canvas.editing():
            self._no_selection_slot = True
            # Use get() to avoid KeyError if mapping is out of sync
            shape = self.items_to_shapes.get(item)
            if shape:
                self.canvas.select_shape(shape)
                # Add Chris
                self.diffc_button.setChecked(shape.difficult)

    def label_item_changed(self, item):
        # Use get() to avoid KeyError if mapping is out of sync
        shape = self.items_to_shapes.get(item)
        if not shape:
            return
        label = item.text()
        if label != shape.label:
            shape.label = item.text()
            shape.line_color = generate_color_by_text(shape.label)
            self.set_dirty()
        else:  # User probably changed item visibility
            self.canvas.set_shape_visible(shape, item.checkState() == Qt.CheckState.Checked)

    # Callback functions:
    def new_shape(self):
        """
        Create a new annotation shape.
        
        Priority for label selection:
        1. If default label is enabled, use default label (no dialog)
        2. If single class mode is enabled and has previous label, use it (no dialog)
        3. Otherwise, show label dialog for user input
        
        Note: The combo box is only for filtering visible shapes,
        not for providing default labels.
        """
        # Check if default label is enabled
        if self.use_default_label_checkbox.isChecked():
            # Priority 1: Use default label
            text = self.default_label
        elif self.single_class_mode.isChecked() and self.prev_label_text:
            # Priority 2: Single class mode - use the last used label without dialog
            text = self.prev_label_text
        else:
            # Priority 3: Normal mode - show label dialog
            if len(self.label_hist) > 0:
                self.label_dialog = LabelDialog(
                    parent=self, list_item=self.label_hist)
            
            # Show dialog with previous label as suggestion
            text = self.label_dialog.pop_up(text=self.prev_label_text)
            if text is not None:
                self.lastLabel = text

        # Add Chris
        self.diffc_button.setChecked(False)
        if text is not None:
            self.prev_label_text = text
            generate_color = generate_color_by_text(text)
            shape = self.canvas.set_last_label(text, generate_color, generate_color)
            self.add_label(shape)
            # Stay in create mode to allow continuous annotation
            # Only switch to edit mode when user explicitly clicks edit button
            if self.beginner():
                self.canvas.set_editing(False)  # Stay in create mode
                self.actions.create.setEnabled(True)
            else:
                self.actions.createMode.setEnabled(True)
            self.set_dirty()

            if text not in self.label_hist:
                self.label_hist.append(text)
                # Update combo box to include the new label
                self.update_combo_box()
        else:
            # self.canvas.undoLastLine()
            self.canvas.reset_all_lines()

    def scroll_request(self, delta, orientation):
        units = - delta / (8 * 15)
        
        # Try multiple key types for maximum compatibility with PySide6
        bar = None
        if hasattr(orientation, 'value'):
            # If orientation is an enum, try both enum and int value
            bar = self.scroll_bars.get(orientation) or self.scroll_bars.get(orientation.value)
        else:
            # If orientation is already an int
            bar = self.scroll_bars.get(orientation)
        
        # Fallback to vertical scrollbar if not found
        if bar is None:
            bar = self.scroll_bars.get(Qt.Orientation.Vertical) or self.scroll_bars.get(0)
        
        if bar:
            bar.setValue(int(bar.value() + bar.singleStep() * units))

    def set_zoom(self, value):
        self.actions.fitWidth.setChecked(False)
        self.actions.fitWindow.setChecked(False)
        self.zoom_mode = self.MANUAL_ZOOM
        # Arithmetic on scaling factor often results in float
        # Convert to int to avoid type errors
        self.zoom_widget.set_zoom_percentage(int(value))

    def add_zoom(self, increment=10):
        current_zoom = self.zoom_widget.get_zoom_percentage()
        self.set_zoom(current_zoom + increment)

    def zoom_request(self, delta):
        # get the current scrollbar positions
        # calculate the percentages ~ coordinates
        h_bar = self.scroll_bars.get(Qt.Orientation.Horizontal, self.scroll_bars.get(1))
        v_bar = self.scroll_bars.get(Qt.Orientation.Vertical, self.scroll_bars.get(0))

        # get the current maximum, to know the difference after zooming
        h_bar_max = h_bar.maximum()
        v_bar_max = v_bar.maximum()

        # get the cursor position and canvas size
        # calculate the desired movement from 0 to 1
        # where 0 = move left
        #       1 = move right
        # up and down analogous
        cursor = QCursor()
        pos = cursor.pos()
        relative_pos = QWidget.mapFromGlobal(self, pos)

        cursor_x = relative_pos.x()
        cursor_y = relative_pos.y()

        w = self.scroll_area.width()
        h = self.scroll_area.height()

        # the scaling from 0 to 1 has some padding
        # you don't have to hit the very leftmost pixel for a maximum-left movement
        margin = 0.1
        move_x = (cursor_x - margin * w) / (w - 2 * margin * w)
        move_y = (cursor_y - margin * h) / (h - 2 * margin * h)

        # clamp the values from 0 to 1
        move_x = min(max(move_x, 0), 1)
        move_y = min(max(move_y, 0), 1)

        # zoom in
        units = delta // (8 * 15)
        scale = 10
        self.add_zoom(scale * units)

        # get the difference in scrollbar values
        # this is how far we can move
        d_h_bar_max = h_bar.maximum() - h_bar_max
        d_v_bar_max = v_bar.maximum() - v_bar_max

        # get the new scrollbar values
        new_h_bar_value = int(h_bar.value() + move_x * d_h_bar_max)
        new_v_bar_value = int(v_bar.value() + move_y * d_v_bar_max)

        h_bar.setValue(new_h_bar_value)
        v_bar.setValue(new_v_bar_value)

    def light_request(self, delta):
        self.add_light(5 * delta // (8 * 15))

    def set_fit_window(self, value=True):
        if value:
            self.actions.fitWidth.setChecked(False)
        self.zoom_mode = self.FIT_WINDOW if value else self.MANUAL_ZOOM
        self.adjust_scale()

    def set_fit_width(self, value=True):
        if value:
            self.actions.fitWindow.setChecked(False)
        self.zoom_mode = self.FIT_WIDTH if value else self.MANUAL_ZOOM
        self.adjust_scale()

    def set_light(self, value):
        self.actions.lightOrg.setChecked(int(value) == 50)
        # Arithmetic on scaling factor often results in float
        # Convert to int to avoid type errors
        self.light_widget.set_light_percentage(int(value))

    def add_light(self, increment=10):
        current_light = self.light_widget.get_light_percentage()
        self.set_light(current_light + increment)

    def toggle_polygons(self, value):
        for item, shape in self.items_to_shapes.items():
            item.setCheckState(Qt.CheckState.Checked if value else Qt.CheckState.Unchecked)

    def load_file(self, file_path=None):
        """Load the specified file, or the last opened file if None."""
        self.reset_state()
        self.canvas.setEnabled(False)
        if file_path is None:
            file_path = self.settings.get(SETTING_FILENAME)
        # Make sure that filePath is a regular python string, rather than QString
        file_path = ustr(file_path)

        # Fix bug: An  index error after select a directory when open a new file.
        unicode_file_path = ustr(file_path)
        unicode_file_path = os.path.abspath(unicode_file_path)
        # Tzutalin 20160906 : Add file list and dock to move faster
        # Highlight the file item
        # Note: In project mode, file_list_widget shows completed annotations (scanned from filesystem)
        # and m_img_list shows pending queue. They are independent, so don't clear file_list_widget.
        if not self.current_project and unicode_file_path and self.file_list_widget.count() > 0:
            if unicode_file_path in self.m_img_list:
                index = self.m_img_list.index(unicode_file_path)
                file_widget_item = self.file_list_widget.item(index)
                file_widget_item.setSelected(True)
            else:
                self.file_list_widget.clear()
                self.m_img_list.clear()

        if unicode_file_path and os.path.exists(unicode_file_path):
            if LabelFile.is_label_file(unicode_file_path):
                try:
                    self.label_file = LabelFile(unicode_file_path)
                except LabelFileError as e:
                    self.error_message(u'Error opening file',
                                       (u"<p><b>%s</b></p>"
                                        u"<p>Make sure <i>%s</i> is a valid label file.")
                                       % (e, unicode_file_path))
                    self.status("Error reading %s" % unicode_file_path)

                    return False
                self.image_data = self.label_file.image_data
                self.line_color = QColor(*self.label_file.lineColor)
                self.fill_color = QColor(*self.label_file.fillColor)
                self.canvas.verified = self.label_file.verified
            else:
                # Load image:
                # read data first and store for saving into label file.
                self.image_data = read(unicode_file_path, None)
                self.label_file = None
                self.canvas.verified = False

            if isinstance(self.image_data, QImage):
                image = self.image_data
            else:
                image = QImage.fromData(self.image_data)
            if image.isNull():
                self.error_message(u'Error opening file',
                                   u"<p>Make sure <i>%s</i> is a valid image file." % unicode_file_path)
                self.status("Error reading %s" % unicode_file_path)
                return False
            self.status("Loaded %s" % os.path.basename(unicode_file_path))
            self.image = image
            self.file_path = unicode_file_path
            self.canvas.load_pixmap(QPixmap.fromImage(image))
            if self.label_file:
                self.load_labels(self.label_file.shapes)
            self.set_clean()
            self.canvas.setEnabled(True)
            self.adjust_scale(initial=True)
            self.paint_canvas()
            self.add_recent_file(self.file_path)
            self.toggle_actions(True)
            self.show_bounding_box_from_annotation_file(self.file_path)

            counter = self.counter_str()
            self.setWindowTitle(__appname__ + ' ' + file_path + ' ' + counter)

            # Default : select last item if there is at least one item
            if self.label_list.count():
                self.label_list.setCurrentItem(self.label_list.item(self.label_list.count() - 1))
                self.label_list.item(self.label_list.count() - 1).setSelected(True)

            self.canvas.setFocus()
            
            # Update label filter combo box to show labels in current image
            self.update_combo_box()
            
            # Update file list colors and progress (only in non-project mode)
            # In project mode, file_list_widget shows completed annotations (scanned from filesystem)
            # and is managed independently by update_completed_annotations_list()
            if not self.current_project and self.file_list_widget.count() > 0:
                self.update_file_list_colors()
            
            return True
        return False

    def counter_str(self):
        """
        Converts image counter to string representation.
        """
        return '[{} / {}]'.format(self.cur_img_idx + 1, self.img_count)

    def format_coordinates(self, width=None, height=None, x=None, y=None):
        """
        Format coordinates text for status bar with current language
        """
        if width is not None and height is not None:
            # Full format with width, height, x, y
            return '%s: %d, %s: %d / %s: %d; %s: %d' % (
                self.get_str('coordWidth'), width,
                self.get_str('coordHeight'), height,
                self.get_str('coordX'), x,
                self.get_str('coordY'), y
            )
        else:
            # Simple format with just x, y
            return '%s: %d; %s: %d' % (
                self.get_str('coordX'), x,
                self.get_str('coordY'), y
            )

    def show_bounding_box_from_annotation_file(self, file_path):
        """Load annotation file for the given image path"""
        basename = os.path.basename(os.path.splitext(file_path)[0])
        
        # Try standard directory structure first: base_dir/annotations/
        if self.default_save_dir is not None:
            anno_dir = os.path.join(self.default_save_dir, 'annotations')
            xml_path = os.path.join(anno_dir, basename + XML_EXT)
            txt_path = os.path.join(anno_dir, basename + TXT_EXT)
            json_path = os.path.join(anno_dir, basename + JSON_EXT)
            
            # If standard directory doesn't exist, try base directory (backward compatibility)
            if not os.path.exists(anno_dir):
                anno_dir = self.default_save_dir
                xml_path = os.path.join(anno_dir, basename + XML_EXT)
                txt_path = os.path.join(anno_dir, basename + TXT_EXT)
                json_path = os.path.join(anno_dir, basename + JSON_EXT)

            """Annotation file priority:
            PascalXML > YOLO > CreateML
            """
            if os.path.isfile(xml_path):
                self.load_pascal_xml_by_filename(xml_path)
            elif os.path.isfile(txt_path):
                self.load_yolo_txt_by_filename(txt_path)
            elif os.path.isfile(json_path):
                self.load_create_ml_json_by_filename(json_path, file_path)
        else:
            # Fallback: look in the same directory as the image
            xml_path = os.path.splitext(file_path)[0] + XML_EXT
            txt_path = os.path.splitext(file_path)[0] + TXT_EXT
            json_path = os.path.splitext(file_path)[0] + JSON_EXT

            if os.path.isfile(xml_path):
                self.load_pascal_xml_by_filename(xml_path)
            elif os.path.isfile(txt_path):
                self.load_yolo_txt_by_filename(txt_path)
            elif os.path.isfile(json_path):
                self.load_create_ml_json_by_filename(json_path, file_path)

    def resizeEvent(self, event):
        if self.canvas and not self.image.isNull() \
                and self.zoom_mode != self.MANUAL_ZOOM:
            self.adjust_scale()
        super(MainWindow, self).resizeEvent(event)

    def paint_canvas(self):
        assert not self.image.isNull(), "cannot paint null image"
        self.canvas.scale = 0.01 * self.zoom_widget.get_zoom_percentage()
        self.canvas.overlay_color = self.light_widget.color()
        self.canvas.label_font_size = int(0.02 * max(self.image.width(), self.image.height()))
        self.canvas.adjustSize()
        self.canvas.update()

    def adjust_scale(self, initial=False):
        value = self.scalers[self.FIT_WINDOW if initial else self.zoom_mode]()
        self.zoom_widget.set_zoom_percentage(int(100 * value))

    def scale_fit_window(self):
        """Figure out the size of the pixmap in order to fit the main widget."""
        e = 2.0  # So that no scrollbars are generated.
        w1 = self.centralWidget().width() - e
        h1 = self.centralWidget().height() - e
        a1 = w1 / h1
        # Calculate a new scale value based on the pixmap's aspect ratio.
        w2 = self.canvas.pixmap.width() - 0.0
        h2 = self.canvas.pixmap.height() - 0.0
        a2 = w2 / h2
        return w1 / w2 if a2 >= a1 else h1 / h2

    def scale_fit_width(self):
        # The epsilon does not seem to work too well here.
        w = self.centralWidget().width() - 2.0
        return w / self.canvas.pixmap.width()

    def closeEvent(self, event):
        if not self.may_continue():
            event.ignore()
        settings = self.settings
        # If it loads images from dir, don't load it at the beginning
        if self.dir_name is None:
            settings[SETTING_FILENAME] = self.file_path if self.file_path else ''
        else:
            settings[SETTING_FILENAME] = ''

        settings[SETTING_WIN_SIZE] = self.size()
        settings[SETTING_WIN_POSE] = self.pos()
        settings[SETTING_WIN_STATE] = self.saveState()
        settings[SETTING_LINE_COLOR] = self.line_color
        settings[SETTING_FILL_COLOR] = self.fill_color
        settings[SETTING_RECENT_FILES] = self.recent_files
        settings[SETTING_ADVANCE_MODE] = not self._beginner
        if self.default_save_dir and os.path.exists(self.default_save_dir):
            settings[SETTING_SAVE_DIR] = ustr(self.default_save_dir)
        else:
            settings[SETTING_SAVE_DIR] = ''

        if self.last_open_dir and os.path.exists(self.last_open_dir):
            settings[SETTING_LAST_OPEN_DIR] = self.last_open_dir
        else:
            settings[SETTING_LAST_OPEN_DIR] = ''

        settings[SETTING_AUTO_SAVE] = self.auto_saving.isChecked()
        settings[SETTING_SINGLE_CLASS] = self.single_class_mode.isChecked()
        settings[SETTING_PAINT_LABEL] = self.display_label_option.isChecked()
        settings[SETTING_DRAW_SQUARE] = self.draw_squares_option.isChecked()
        settings[SETTING_LABEL_FILE_FORMAT] = self.label_file_format
        settings.save()

    def load_recent(self, filename):
        if self.may_continue():
            self.load_file(filename)

    def scan_all_images(self, folder_path):
        extensions = ['.%s' % fmt.data().decode("ascii").lower() for fmt in QImageReader.supportedImageFormats()]
        images = []

        for root, dirs, files in os.walk(folder_path):
            for file in files:
                if file.lower().endswith(tuple(extensions)):
                    relative_path = os.path.join(root, file)
                    path = ustr(os.path.abspath(relative_path))
                    images.append(path)
        natural_sort(images, key=lambda x: x.lower())
        return images

    def change_save_dir_dialog(self, _value=False):
        # Check if there are existing annotations in the current directory
        has_existing_annotations = False
        old_anno_dir = self.default_save_dir
        
        if old_anno_dir and os.path.exists(old_anno_dir):
            # Check for any annotation files
            for ext in ['.xml', '.txt', '.json']:
                if any(f.endswith(ext) for f in os.listdir(old_anno_dir)):
                    has_existing_annotations = True
                    break
        
        # Warn user if changing save directory after annotations have been created
        if has_existing_annotations and self.current_project:
            reply = QMessageBox.warning(
                self,
                self.get_str('warningChangeOutputPath'),
                self.get_str('detectExistingAnnotations') + '\n\n' +
                f'{self.get_str("currentDir")}{old_anno_dir}\n\n' +
                self.get_str('changeOutputPathWarning') + '\n' +
                '• ' + self.get_str('noOpenProjectWarning2') + '\n' +
                '• ' + self.get_str('modifyOutputPathWarning').split('\n')[1] + '\n' +
                '• ' + self.get_str('modifyOutputPathWarning').split('\n')[2] + '\n\n' +
                self.get_str('migrateAnnotations'),
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
                QMessageBox.Cancel
            )
            
            if reply == QMessageBox.Cancel:
                return
            elif reply == QMessageBox.Yes:
                # Migrate annotations to new directory
                if not self._migrate_annotations(old_anno_dir, None):  # Will ask for new dir
                    return
            # If No, continue without migration
        elif self.default_save_dir is not None and len(self.m_img_list) > 0:
            reply = QMessageBox.warning(
                self,
                self.get_str('warningTitle2'),
                self.get_str('modifyOutputPathWarning') + '\n\n' +
                self.get_str('continueEditQuestion'),
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.No:
                return
        
        if self.default_save_dir is not None:
            path = ustr(self.default_save_dir)
        else:
            path = '.'

        dir_path = ustr(QFileDialog.getExistingDirectory(self,
                                                         '%s - %s' % (__appname__, self.get_str('selectDatabaseDirTitle')), path,
                                                         QFileDialog.ShowDirsOnly
                                                         | QFileDialog.DontResolveSymlinks))

        if dir_path is not None and len(dir_path) > 1:
            self.default_save_dir = dir_path
            # Update the output dir input in right dock
            if hasattr(self, 'output_dir_input'):
                self.output_dir_input.setText(dir_path)

            
            # Sync with project if in project mode
            if self.current_project:
                self.current_project.annotation_dir = dir_path

        # Only show bounding boxes if file_path is valid
        if self.file_path:
            self.show_bounding_box_from_annotation_file(self.file_path)

        self.statusBar().showMessage('%s . %s%s' %
                                     (self.get_str('setDatabaseDirStatus'), self.get_str('annotationsAndImagesWillSaveTo'), self.default_save_dir))
        self.statusBar().show()

    def _migrate_annotations(self, old_dir, new_dir=None):
        """Migrate annotation files from old directory to new directory (deprecated, use _migrate_and_convert_annotations)"""
        
        if not old_dir or not os.path.exists(old_dir):
            return False
        
        # If new_dir not provided, ask user
        if not new_dir:
            new_dir = ustr(QFileDialog.getExistingDirectory(
                self,
                self.get_str('selectExportDirTitle'),
                old_dir,
                QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks
            ))
            
            if not new_dir or len(new_dir) <= 1:
                return False
        
        if old_dir == new_dir:
            QMessageBox.information(self, self.get_str('infoTitle'), self.get_str('migrationNotNeeded'))
            return True
        
        # Ask user to choose copy or move
        reply = QMessageBox.question(
            self,
            self.get_str('migrationModeTitle'),
            f'{self.get_str("migrateFrom")}\n{old_dir}\n\n{self.get_str("migrateTo")}\n{new_dir}\n\n'
            f'{self.get_str("chooseMigrationMode")}\n\n'
            f'• {self.get_str("copyKeepOriginal")}\n'
            f'• {self.get_str("moveDeleteOriginal")}',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )
        
        mode = 'copy' if reply == QMessageBox.Yes else 'move'
        
        # Use the new migration method
        ext_map = {
            LabelFileFormat.PASCAL_VOC: '.xml',
            LabelFileFormat.YOLO: '.txt',
            LabelFileFormat.CREATE_ML: '.json'
        }
        current_format_name = {
            LabelFileFormat.PASCAL_VOC: 'PASCAL_VOC',
            LabelFileFormat.YOLO: 'YOLO',
            LabelFileFormat.CREATE_ML: 'CREATE_ML'
        }.get(self.label_file_format, 'PASCAL_VOC')
        
        return self._migrate_and_convert_annotations(
            old_dir, new_dir, current_format_name, current_format_name, mode
        )

    def change_output_format(self, index):
        """Handle output format change from combo box"""
        if index < 0:
            return
        
        # Get the selected format
        new_format = self.output_format_combo.itemData(index)
        if new_format is None:
            return
        
        old_format = self.label_file_format
        
        # If format is actually changing and there are existing annotations, warn user
        if new_format != old_format and self.current_project:
            # Check if there are existing annotations
            anno_dir = self.default_save_dir or self.current_project.annotation_dir
            has_annotations = False
            
            if anno_dir and os.path.exists(anno_dir):
                ext_map = {
                    LabelFileFormat.PASCAL_VOC: '.xml',
                    LabelFileFormat.YOLO: '.txt',
                    LabelFileFormat.CREATE_ML: '.json'
                }
                old_ext = ext_map.get(old_format, '.xml')
                if any(f.endswith(old_ext) for f in os.listdir(anno_dir)):
                    has_annotations = True
            
            if has_annotations:
                format_names = {
                    LabelFileFormat.PASCAL_VOC: 'PASCAL VOC (XML)',
                    LabelFileFormat.YOLO: 'YOLO (TXT)',
                    LabelFileFormat.CREATE_ML: 'CreateML (JSON)'
                }
                
                reply = QMessageBox.warning(
                    self,
                    self.get_str('warningChangeOutputFormat'),
                    f'{self.get_str("detectExistingFiles")}\n\n' +
                    f'{self.get_str("currentFormat")}{format_names.get(old_format, str(old_format))}\n' +
                    f'{self.get_str("newFormat")}{format_names.get(new_format, str(new_format))}\n\n' +
                    self.get_str('changeFormatWarning') + '\n' +
                    '• ' + self.get_str('changeFormatWarning').split('\n')[1] + '\n' +
                    '• ' + self.get_str('changeFormatWarning').split('\n')[2] + '\n' +
                    '• ' + self.get_str('changeFormatWarning').split('\n')[3] + '\n' +
                    '• ' + self.get_str('changeFormatWarning').split('\n')[4] + '\n\n' +
                    self.get_str('recommendations') + '\n' +
                    '• ' + self.get_str('recommendations').split('\n')[1] + '\n' +
                    '• ' + self.get_str('recommendations').split('\n')[2] + '\n\n' +
                    self.get_str('continueEditQuestion'),
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                
                if reply == QMessageBox.No:
                    # Revert to old format
                    format_index_map = {
                        LabelFileFormat.PASCAL_VOC: 0,
                        LabelFileFormat.YOLO: 1,
                        LabelFileFormat.CREATE_ML: 2
                    }
                    self.output_format_combo.setCurrentIndex(format_index_map.get(old_format, 0))
                    return
        
        # Apply the format change
        self.label_file_format = new_format
        
        # Sync with project if in project mode
        if self.current_project:
            format_names = {
                LabelFileFormat.PASCAL_VOC: 'PASCAL_VOC',
                LabelFileFormat.YOLO: 'YOLO',
                LabelFileFormat.CREATE_ML: 'CREATE_ML'
            }
            self.current_project.format = format_names.get(new_format, 'PASCAL_VOC')
        
        print(f'Output format changed from {old_format} to {new_format}')
        self.statusBar().showMessage(f'输出格式已更改为: {self.output_format_combo.currentText()}')

    def open_annotation_dialog(self, _value=False):
        if self.file_path is None:
            self.statusBar().showMessage('Please select image first')
            self.statusBar().show()
            return

        path = os.path.dirname(ustr(self.file_path)) \
            if self.file_path else '.'
        if self.label_file_format == LabelFileFormat.PASCAL_VOC:
            filters = "Open Annotation XML file (%s)" % ' '.join(['*.xml'])
            filename = ustr(QFileDialog.getOpenFileName(self, '%s - Choose a xml file' % __appname__, path, filters))
            if filename:
                if isinstance(filename, (tuple, list)):
                    filename = filename[0]
            self.load_pascal_xml_by_filename(filename)

        elif self.label_file_format == LabelFileFormat.CREATE_ML:

            filters = "Open Annotation JSON file (%s)" % ' '.join(['*.json'])
            filename = ustr(QFileDialog.getOpenFileName(self, '%s - Choose a json file' % __appname__, path, filters))
            if filename:
                if isinstance(filename, (tuple, list)):
                    filename = filename[0]

            self.load_create_ml_json_by_filename(filename, self.file_path)

    def open_dir_dialog(self, _value=False, dir_path=None, silent=False):
        if not self.may_continue():
            return

        default_open_dir_path = dir_path if dir_path else '.'
        if self.last_open_dir and os.path.exists(self.last_open_dir):
            default_open_dir_path = self.last_open_dir
        else:
            default_open_dir_path = os.path.dirname(self.file_path) if self.file_path else '.'
        if silent != True:
            target_dir_path = ustr(QFileDialog.getExistingDirectory(self,
                                                                    '%s - Open Directory' % __appname__,
                                                                    default_open_dir_path,
                                                                    QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks))
        else:
            target_dir_path = ustr(default_open_dir_path)
        
        # Warn if changing output directory with existing annotations
        old_anno_dir = self.default_save_dir
        has_existing_annotations = False
        
        if old_anno_dir and os.path.exists(old_anno_dir) and self.current_project:
            for ext in ['.xml', '.txt', '.json']:
                if any(f.endswith(ext) for f in os.listdir(old_anno_dir)):
                    has_existing_annotations = True
                    break
        
        if has_existing_annotations and old_anno_dir != target_dir_path:
            reply = QMessageBox.warning(
                self,
                '⚠️ 警告：修改输出路径',
                f'当前输出目录已有标注文件！\n\n'
                f'旧目录：{old_anno_dir}\n'
                f'新目录：{target_dir_path}\n\n'
                '是否迁移现有标注文件到新目录？',
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
                QMessageBox.Cancel
            )
            
            if reply == QMessageBox.Cancel:
                return
            elif reply == QMessageBox.Yes:
                # Migrate before changing
                if not self._migrate_annotations(old_anno_dir, target_dir_path):
                    return
        
        self.last_open_dir = target_dir_path
        self.import_dir_images(target_dir_path)
        self.default_save_dir = target_dir_path
        # Update the output dir input in right dock
        if hasattr(self, 'output_dir_input'):
            self.output_dir_input.setText(target_dir_path)
        
        # Sync with project if in project mode
        if self.current_project:
            self.current_project.annotation_dir = target_dir_path
        if self.file_path:
            self.show_bounding_box_from_annotation_file(file_path=self.file_path)

    def import_dir_images(self, dir_path):
        if not self.may_continue() or not dir_path:
            return

        self.last_open_dir = dir_path
        self.dir_name = dir_path
        self.file_path = None
        self.file_list_widget.clear()
        self.m_img_list = self.scan_all_images(dir_path)
        self.img_count = len(self.m_img_list)
        self.open_next_image()
        for imgPath in self.m_img_list:
            item = QListWidgetItem(imgPath)
            # Check if annotation file exists and mark with green color
            if self._has_annotation(imgPath):
                item.setForeground(QColor('green'))
            else:
                # Unannotated files: use blue for better visibility
                item.setForeground(QColor('#2196F3'))  # Material Design Blue
            self.file_list_widget.addItem(item)
    
    def _has_annotation(self, image_path):
        """Check if annotation file exists for the given image"""
        base_name = os.path.splitext(os.path.basename(image_path))[0]
        
        # Check in standard directory structure first: base_dir/annotations/
        if self.default_save_dir:
            anno_dir = os.path.join(self.default_save_dir, 'annotations')
            # If standard directory doesn't exist, try base directory (backward compatibility)
            if not os.path.exists(anno_dir):
                anno_dir = self.default_save_dir
        else:
            anno_dir = os.path.dirname(image_path)
        
        # Check all possible annotation formats
        for ext in ['.xml', '.txt', '.json']:
            anno_path = os.path.join(anno_dir, base_name + ext)
            if os.path.exists(anno_path):
                return True
        return False
    
    def update_file_list_colors(self):
        """Update file list item colors based on annotation status"""
        for i in range(self.file_list_widget.count()):
            item = self.file_list_widget.item(i)
            img_path = item.text()
            if self._has_annotation(img_path):
                # Annotated files: green (use theme-adaptive color)
                item.setForeground(QColor(0, 180, 0))  # Green color
            else:
                # Unannotated files: use theme's text color for better visibility
                item.setForeground(QColor())  # Reset to default theme color
        
        # Update progress info
        self.update_progress_info()
    
    def update_progress_info(self):
        """Update annotation progress information"""
        # Check if progress widgets exist (they may not be created in all modes)
        if not hasattr(self, 'progress_label') or not hasattr(self, 'next_unannotated_btn'):
            return
        
        if not self.m_img_list:
            self.progress_label.setText(self.get_str('annotatedProgress').format(0, 0))
            self.next_unannotated_btn.setEnabled(False)
            return
        
        total = len(self.m_img_list)
        annotated = sum(1 for img_path in self.m_img_list if self._has_annotation(img_path))
        
        self.progress_label.setText(self.get_str('annotatedProgress').format(annotated, total))
        
        # Enable/disable next unannotated button
        has_unannotated = annotated < total
        self.next_unannotated_btn.setEnabled(has_unannotated)
    
    def jump_to_next_unannotated(self):
        """Jump to the next unannotated image"""
        if not self.m_img_list or not self.file_path:
            return
        
        current_idx = self.cur_img_idx
        total = len(self.m_img_list)
        
        # Search from current position to end
        for i in range(current_idx + 1, total):
            if not self._has_annotation(self.m_img_list[i]):
                self.cur_img_idx = i
                filename = self.m_img_list[i]
                self.load_file(filename)
                return
        
        # If not found after current, search from beginning
        for i in range(0, current_idx):
            if not self._has_annotation(self.m_img_list[i]):
                self.cur_img_idx = i
                filename = self.m_img_list[i]
                self.load_file(filename)
                QMessageBox.information(
                    self,
                    self.get_str('tip'),
                    self.get_str('jumpedToFirstUnannotated').format(total - sum(1 for img in self.m_img_list if self._has_annotation(img)))
                )
                return
        
        # All images are annotated
        QMessageBox.information(self, self.get_str('tip'), self.get_str('allImagesAnnotated'))

    def verify_image(self, _value=False):
        # Proceeding next image without dialog if having any label
        if self.file_path is not None:
            try:
                self.label_file.toggle_verify()
            except AttributeError:
                # If the labelling file does not exist yet, create if and
                # re-save it with the verified attribute.
                self.save_file()
                if self.label_file is not None:
                    self.label_file.toggle_verify()
                else:
                    return

            self.canvas.verified = self.label_file.verified
            self.paint_canvas()
            self.save_file()

    def open_prev_image(self, _value=False):
        # Auto save if enabled (will prompt if not enabled and has unsaved changes)
        if self.dirty and not self.auto_saving.isChecked():
            reply = QMessageBox.question(
                self,
                self.get_str('unsaveChanges'),
                self.get_str('currentImageHasUnsaved') + '\n\n' +
                self.get_str('recommendAutoSave') + '\n\n' +
                self.get_str('enableAutoSaveContinue'),
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
                QMessageBox.Yes
            )
            if reply == QMessageBox.Cancel:
                return
            elif reply == QMessageBox.Yes:
                self.auto_saving.setChecked(True)
        
        # Auto save before switching
        if not self.auto_save_if_enabled():
            return

        if self.img_count <= 0:
            return

        if self.file_path is None:
            return

        if self.cur_img_idx - 1 >= 0:
            self.cur_img_idx -= 1
            filename = self.m_img_list[self.cur_img_idx]
            if filename:
                self.statusBar().showMessage(self.get_str('switchedToPrevious').format(os.path.basename(filename), self.cur_img_idx + 1, self.img_count))
                self.load_file(filename)

    def open_next_image(self, _value=False):
        # Auto save if enabled (will prompt if not enabled and has unsaved changes)
        if self.dirty and not self.auto_saving.isChecked():
            reply = QMessageBox.question(
                self,
                self.get_str('unsaveChanges'),
                self.get_str('currentImageHasUnsaved') + '\n\n' +
                self.get_str('recommendAutoSave') + '\n\n' +
                self.get_str('enableAutoSaveContinue'),
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
                QMessageBox.Yes
            )
            if reply == QMessageBox.Cancel:
                return
            elif reply == QMessageBox.Yes:
                self.auto_saving.setChecked(True)
        
        # Auto save before switching
        if not self.auto_save_if_enabled():
            return

        if self.img_count <= 0:
            return

        if not self.m_img_list:
            return

        filename = None
        if self.file_path is None:
            filename = self.m_img_list[0]
            self.cur_img_idx = 0
        else:
            if self.cur_img_idx + 1 < self.img_count:
                self.cur_img_idx += 1
                filename = self.m_img_list[self.cur_img_idx]

        if filename:
            self.statusBar().showMessage(self.get_str('switchedToNext').format(os.path.basename(filename), self.cur_img_idx + 1, self.img_count))
            self.load_file(filename)

    def open_file(self, _value=False):
        if not self.may_continue():
            return
        path = os.path.dirname(ustr(self.file_path)) if self.file_path else '.'
        formats = ['*.%s' % fmt.data().decode("ascii").lower() for fmt in QImageReader.supportedImageFormats()]
        filters = "Image & Label files (%s)" % ' '.join(formats + ['*%s' % LabelFile.suffix])
        filename, _ = QFileDialog.getOpenFileName(self, '%s - Choose Image or Label file' % __appname__, path, filters)
        if filename:
            if isinstance(filename, (tuple, list)):
                filename = filename[0]
            self.cur_img_idx = 0
            self.img_count = 1
            self.load_file(filename)

    def save_file(self, _value=False):
        """Save annotation file and copy image to project's output directory with proper structure"""
        if not self.file_path:
            return
        
        # Priority: default_save_dir (which is synced with project.annotation_dir)
        # This ensures user's current setting is always used
        if self.default_save_dir is not None and len(ustr(self.default_save_dir)):
            # Create proper directory structure based on format
            anno_dir, img_dir = self._get_output_dirs(ustr(self.default_save_dir))
            
            image_file_name = os.path.basename(self.file_path)
            saved_file_name = os.path.splitext(image_file_name)[0]
            saved_path = os.path.join(anno_dir, saved_file_name)
            self._save_file(saved_path)
            # Copy image file to images directory
            self._copy_image_to_output(img_dir, image_file_name)
            # After manual save, auto switch to next image
            self.open_next_image()
        elif self.current_project and self.current_project.annotation_dir:
            # Fallback to project's annotation_dir if default_save_dir is not set
            anno_dir, img_dir = self._get_output_dirs(self.current_project.annotation_dir)
            
            image_file_name = os.path.basename(self.file_path)
            saved_file_name = os.path.splitext(image_file_name)[0]
            saved_path = os.path.join(anno_dir, saved_file_name)
            self._save_file(saved_path)
            # Copy image file to images directory
            self._copy_image_to_output(img_dir, image_file_name)
            # Sync default_save_dir with project
            self.default_save_dir = self.current_project.annotation_dir
            # After manual save, auto switch to next image
            self.open_next_image()
        else:
            # Last fallback: save to same directory as image
            image_file_dir = os.path.dirname(self.file_path)
            image_file_name = os.path.basename(self.file_path)
            saved_file_name = os.path.splitext(image_file_name)[0]
            saved_path = os.path.join(image_file_dir, saved_file_name)
            self._save_file(saved_path)
            # After manual save, auto switch to next image
            self.open_next_image()

    def _save_file(self, annotation_file_path):
        if annotation_file_path and self.save_labels(annotation_file_path):
            self.set_clean()
            self.statusBar().showMessage('Saved to  %s' % annotation_file_path)
            self.statusBar().show()
            
            # After saving, mark as annotated (green color) instead of removing
            if self.file_path:
                self.mark_as_annotated(self.file_path)
                self.update_completed_annotations_list()
    
    def _copy_image_to_output(self, output_dir, image_file_name):
        """Copy image file to output directory
        
        Args:
            output_dir: Directory to copy image to
            image_file_name: Name of the image file
        """
        if not self.file_path or not os.path.exists(self.file_path):
            return
        
        try:
            import shutil
            # Ensure output directory exists
            os.makedirs(output_dir, exist_ok=True)
            
            # Copy image file
            dst_path = os.path.join(output_dir, image_file_name)
            
            # Only copy if file doesn't exist or is different
            if not os.path.exists(dst_path):
                shutil.copy2(self.file_path, dst_path)
                print(f'Copied image: {image_file_name} to {output_dir}')
            else:
                # Check if files are different (by size and modification time)
                src_stat = os.stat(self.file_path)
                dst_stat = os.stat(dst_path)
                if src_stat.st_size != dst_stat.st_size or src_stat.st_mtime != dst_stat.st_mtime:
                    shutil.copy2(self.file_path, dst_path)
                    print(f'Updated image: {image_file_name} in {output_dir}')
        except Exception as e:
            print(f'Warning: Failed to copy image: {e}')
    
    def _get_output_dirs(self, base_dir):
        """Get annotation and image directories based on output format
        
        Args:
            base_dir: Base output directory
            
        Returns:
            tuple: (annotation_dir, image_dir)
        """
        # Create standard directory structure
        anno_dir = os.path.join(base_dir, 'annotations')
        img_dir = os.path.join(base_dir, 'images')
        
        # Create directories if they don't exist
        os.makedirs(anno_dir, exist_ok=True)
        os.makedirs(img_dir, exist_ok=True)
        
        return anno_dir, img_dir

    def close_file(self, _value=False):
        if not self.may_continue():
            return
        self.reset_state()
        self.set_clean()
        self.toggle_actions(False)
        self.canvas.setEnabled(False)

    def delete_image(self):
        delete_path = self.file_path
        if delete_path is not None:
            idx = self.cur_img_idx
            if os.path.exists(delete_path):
                os.remove(delete_path)
            self.import_dir_images(self.last_open_dir)
            if self.img_count > 0:
                self.cur_img_idx = min(idx, self.img_count - 1)
                filename = self.m_img_list[self.cur_img_idx]
                self.load_file(filename)
            else:
                self.close_file()

    def reset_all(self):
        self.settings.reset()
        self.close()
        process = QProcess()
        process.startDetached(os.path.abspath(__file__))

    def may_continue(self):
        if not self.dirty:
            return True
        else:
            discard_changes = self.discard_changes_dialog()
            if discard_changes == QMessageBox.No:
                return True
            elif discard_changes == QMessageBox.Yes:
                self.save_file()
                return True
            else:
                return False

    def discard_changes_dialog(self):
        yes, no, cancel = QMessageBox.Yes, QMessageBox.No, QMessageBox.Cancel
        msg = u'You have unsaved changes, would you like to save them and proceed?\nClick "No" to undo all changes.'
        return QMessageBox.warning(self, u'Attention', msg, yes | no | cancel)

    def error_message(self, title, message):
        return QMessageBox.critical(self, title,
                                    '<p><b>%s</b></p>%s' % (title, message))

    def current_path(self):
        return os.path.dirname(self.file_path) if self.file_path else '.'

    def choose_color1(self):
        color = self.color_dialog.getColor(self.line_color, u'Choose line color',
                                           default=DEFAULT_LINE_COLOR)
        if color:
            self.line_color = color
            Shape.line_color = color
            self.canvas.set_drawing_color(color)
            self.canvas.update()
            self.set_dirty()

    def delete_selected_shape(self):
        self.remove_label(self.canvas.delete_selected())
        self.set_dirty()
        if self.no_shapes():
            for action in self.actions.onShapesPresent:
                action.setEnabled(False)

    def choose_shape_line_color(self):
        color = self.color_dialog.getColor(self.line_color, u'Choose Line Color',
                                           default=DEFAULT_LINE_COLOR)
        if color:
            self.canvas.selected_shape.line_color = color
            self.canvas.update()
            self.set_dirty()

    def choose_shape_fill_color(self):
        color = self.color_dialog.getColor(self.fill_color, u'Choose Fill Color',
                                           default=DEFAULT_FILL_COLOR)
        if color:
            self.canvas.selected_shape.fill_color = color
            self.canvas.update()
            self.set_dirty()

    def copy_shape(self):
        if self.canvas.selected_shape is None:
            # True if one accidentally touches the left mouse button before releasing
            return
        self.canvas.end_move(copy=True)
        self.add_label(self.canvas.selected_shape)
        self.set_dirty()

    def move_shape(self):
        self.canvas.end_move(copy=False)
        self.set_dirty()

    def load_predefined_classes(self, predef_classes_file):
        if predef_classes_file is not None and os.path.exists(predef_classes_file) is True:
            with codecs.open(predef_classes_file, 'r', 'utf8') as f:
                for line in f:
                    line = line.strip()
                    if self.label_hist is None:
                        self.label_hist = [line]
                    else:
                        self.label_hist.append(line)

    def load_label_categories_file(self):
        """Load label categories from a text file (one label per line)"""
        
        # Strong warning before loading new labels
        if len(self.label_hist) > 0 or len(self.m_img_list) > 0:
            reply = QMessageBox.critical(
                self,
                self.get_str('seriousWarningTitle'),
                self.get_str('loadLabelsCriticalWarning'),
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.No:
                return
        
        # Open file dialog to select label categories file
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            self.get_str('loadLabelsFileTitle'),
            self.last_open_dir or '.',
            'Text Files (*.txt);;All Files (*)'
        )
        
        if not file_path:
            return
        
        file_path = ustr(file_path)
        
        if not os.path.exists(file_path):
            QMessageBox.warning(self, self.get_str('errorTitle'), self.get_str('fileNotExistError') + file_path)
            return
        
        try:
            # Read labels from file
            new_labels = []
            with codecs.open(file_path, 'r', 'utf8') as f:
                for line in f:
                    line = line.strip()
                    if line:  # Skip empty lines
                        new_labels.append(line)
            
            if not new_labels:
                QMessageBox.warning(self, self.get_str('warningTitle'), self.get_str('noValidLabelsFound2'))
                return
            
            # Update label_hist with new labels (replace old ones)
            old_count = len(self.label_hist)
            self.label_hist = new_labels
            
            # Update default label combo box
            self.default_label_combo_box.update_items(self.label_hist)
            
            # Show default label section since we now have labels
            if hasattr(self, 'use_default_label_checkbox'):
                self.use_default_label_checkbox.setVisible(True)
            if hasattr(self, 'default_label_combo_box'):
                self.default_label_combo_box.setVisible(True)
            
            # Update label filter combo box (will be updated when loading an image)
            self.update_combo_box()
            
            # Save last directory
            self.last_open_dir = os.path.dirname(file_path)
            
            # Show warning about potential issues
            QMessageBox.warning(
                self,
                self.get_str('warningTitle'),
                self.get_str('loadedNewLabelsMsg').format(len(new_labels)) + '\n\n'
                f'{self.get_str("previousLabelsCount2").format(old_count)}\n\n'
                f'{self.get_str("checkExistingAnnotations2")}'
            )
            
            print(f'Loaded {len(new_labels)} labels from: {file_path}')
            
        except Exception as e:
            QMessageBox.critical(self, self.get_str('errorTitle'), self.get_str('loadLabelFailedMessage2') + str(e))
    
    def edit_project_dialog(self):
        """Edit current project settings"""
        
        if not self.current_project:
            QMessageBox.warning(self, self.get_str('warningTitle'), self.get_str('noOpenProjectWarning3'))
            return
        
        # Show warning about editing project
        warning_msg = self.get_str('editProjectWarningMsg')
        reply = QMessageBox.warning(
            self,
            self.get_str('editProjectWarningTitle'),
            warning_msg + '\n\n' +
            self.get_str('backupRecommendation2') + '\n\n' +
            self.get_str('continueEditQuestion'),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.No:
            return
        
        # Open new project dialog with current project data pre-filled (edit mode)
        dialog = NewProjectDialog(self, edit_mode=True)
        
        # Pre-fill with current project data
        dialog.name_input.setText(self.current_project.name)
        dialog.dir_input.setText(self.current_project.project_dir)
        
        # Set format (using radio buttons)
        format_map = {
            'PASCAL_VOC': dialog.format_voc,
            'YOLO': dialog.format_yolo,
            'CREATE_ML': dialog.format_createml
        }
        radio_button = format_map.get(self.current_project.format, dialog.format_voc)
        radio_button.setChecked(True)
        
        # Load labels
        for label in self.current_project.labels:
            dialog.labels.append(label)
            dialog.label_list.addItem(label)
        
        if dialog.exec() == QDialog.Accepted:
            project_data = dialog.get_project_data()
            
            # Calculate annotation directory based on project directory
            import os
            project_dir = project_data['project_dir']
            annotation_dir = os.path.join(project_dir, 'annotations')
            
            # Check if output path or format changed
            old_anno_dir = self.current_project.annotation_dir
            new_anno_dir = annotation_dir
            old_format = self.current_project.format
            new_format = project_data['format']
            
            path_changed = old_anno_dir != new_anno_dir
            format_changed = old_format != new_format
            
            # If path or format changed and there are annotations, ask to migrate
            has_annotations = False
            if old_anno_dir and os.path.exists(old_anno_dir):
                ext_map = {
                    'PASCAL_VOC': '.xml',
                    'YOLO': '.txt',
                    'CREATE_ML': '.json'
                }
                old_ext = ext_map.get(old_format, '.xml')
                if any(f.endswith(old_ext) for f in os.listdir(old_anno_dir)):
                    has_annotations = True
            
            if (path_changed or format_changed) and has_annotations:
                migrate_reply = QMessageBox.question(
                    self,
                    self.get_str('migrationDialogTitle'),
                    f'{self.get_str("configChangeDetected2")}\n\n' +
                    f'{"• " + self.get_str("outputPath") + ": " + old_anno_dir + " → " + new_anno_dir if path_changed else ""}\n' +
                    f'{"• " + self.get_str("outputFormat") + ": " + old_format + " → " + new_format if format_changed else ""}\n\n' +
                    f'{self.get_str("annotationFilesFound2").format(len([f for f in os.listdir(old_anno_dir) if f.endswith(ext_map.get(old_format, ".xml"))]))}\n\n' +
                    f'{self.get_str("chooseAction3")}\n\n' +
                    f'• {self.get_str("copyText")}：{self.get_str("copyKeepOriginal")}\n' +
                    f'• {self.get_str("moveText")}：{self.get_str("moveDeleteOriginal")}\n' +
                    f'• {self.get_str("skipMigration")}',
                    QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
                    QMessageBox.Yes
                )
                
                if migrate_reply == QMessageBox.Cancel:
                    return
                elif migrate_reply == QMessageBox.Yes:
                    # Copy files to new directory
                    if not self._migrate_and_convert_annotations(
                        old_anno_dir, new_anno_dir, old_format, new_format, mode='copy'
                    ):
                        return
                elif migrate_reply == QMessageBox.No:
                    # Move files to new directory
                    if not self._migrate_and_convert_annotations(
                        old_anno_dir, new_anno_dir, old_format, new_format, mode='move'
                    ):
                        return
            
            # Update current project
            try:
                self.current_project.name = project_data['name']
                self.current_project.project_dir = project_data['project_dir']
                self.current_project.annotation_dir = annotation_dir
                self.current_project.labels = project_data['labels']
                self.current_project.format = project_data['format']
                
                print(f'Project updated:')
                print(f'  project_dir: {self.current_project.project_dir}')
                print(f'  annotation_dir: {self.current_project.annotation_dir}')
                print(f'  Expected images dir: {os.path.join(self.current_project.project_dir, "images")}')
                
                # Save project file
                self.current_project.save()
                
                # Reload project to update UI
                self.load_project(self.current_project)
                
                QMessageBox.information(
                    self,
                    self.get_str('successTitle'),
                    self.get_str('projectUpdatedSuccess2').format(self.current_project.name)
                )
                
            except Exception as e:
                QMessageBox.critical(self, self.get_str('errorTitle'), self.get_str('updateProjectFailedMessage2') + str(e))
    
    def _migrate_and_convert_annotations(self, old_dir, new_dir, old_format, new_format, mode='copy'):
        """Migrate annotation files from old directory to new directory with format conversion
        
        Args:
            old_dir: Source directory
            new_dir: Destination directory
            old_format: Source format (PASCAL_VOC, YOLO, CREATE_ML)
            new_format: Destination format
            mode: 'copy' (keep original) or 'move' (delete original)
        """
        
        if not old_dir or not os.path.exists(old_dir):
            return False
        
        # Ensure new directory exists
        os.makedirs(new_dir, exist_ok=True)
        
        # Find all annotation files in old directory
        ext_map = {
            'PASCAL_VOC': '.xml',
            'YOLO': '.txt',
            'CREATE_ML': '.json'
        }
        
        old_ext = ext_map.get(old_format, '.xml')
        migrated_count = 0
        converted_count = 0
        
        try:
            import shutil
            for filename in os.listdir(old_dir):
                if filename.lower().endswith(old_ext):
                    src_path = os.path.join(old_dir, filename)
                    
                    # If format changed, need to convert
                    if old_format != new_format:
                        # For now, just copy the file (conversion is complex)
                        # TODO: Implement format conversion
                        base_name = os.path.splitext(filename)[0]
                        new_ext = ext_map.get(new_format, '.xml')
                        dst_path = os.path.join(new_dir, base_name + new_ext)
                        
                        if mode == 'copy':
                            shutil.copy2(src_path, dst_path)
                        else:  # move
                            shutil.move(src_path, dst_path)
                        
                        converted_count += 1
                    else:
                        # Same format, just copy/move
                        dst_path = os.path.join(new_dir, filename)
                        
                        if mode == 'copy':
                            shutil.copy2(src_path, dst_path)
                        else:  # move
                            shutil.move(src_path, dst_path)
                        
                        migrated_count += 1
            
            total = migrated_count + converted_count
            if total > 0:
                mode_text = self.get_str('copyText') if mode == 'copy' else self.get_str('moveText')
                msg = self.get_str('migrationSuccessMsg2').format(mode_text, total) + '\n\n'
                if converted_count > 0:
                    msg += self.get_str('convertedCount2').format(converted_count) + '\n'
                    msg += self.get_str('manualCheckRecommended2') + '\n\n'
                msg += f'{self.get_str("fromText")}{old_dir}\n{self.get_str("toText")}{new_dir}\n\n'
                if mode == 'copy':
                    msg += '✅ ' + self.get_str('originalFilesKept')
                else:
                    msg += '⚠️ ' + self.get_str('originalFilesDeleted')
                
                QMessageBox.information(self, self.get_str('migrationComplete2'), msg)
                print(f'{mode_text.capitalize()}d {total} annotation files from {old_dir} to {new_dir}')
            else:
                QMessageBox.information(self, self.get_str('infoTitle'), self.get_str('noAnnotationsFound2').format(old_dir))
            
            return True
            
        except Exception as e:
            QMessageBox.critical(self, self.get_str('errorTitle'), self.get_str('migrationFailedMessage2') + str(e))
            import traceback
            traceback.print_exc()
            return False

    # Project management methods
    def auto_save_if_enabled(self):
        """Auto save if enabled and there are unsaved changes"""
        if self.auto_saving.isChecked() and self.dirty:
            # In project mode or has default save dir, auto save
            if (self.current_project and self.current_project.annotation_dir) or \
               (self.default_save_dir is not None and len(ustr(self.default_save_dir))):
                print('Auto saving...')
                self.save_file()
                return True
            else:
                # No save path configured, ask user to set it
                self.change_save_dir_dialog()
                return False
        return True  # No need to save or already saved
    
    def new_project_dialog(self):
        """Show new project dialog and create project"""
        dialog = NewProjectDialog(self)
        if dialog.exec() == QDialog.Accepted:
            project_data = dialog.get_project_data()
            
            try:
                # Use the user-selected directory as project_dir (database directory)
                project_dir = project_data['project_dir']
                
                # Create project
                project = Project(
                    name=project_data['name'],
                    project_dir=project_dir,
                    labels=project_data['labels'],
                    format=project_data['format']
                )
                
                # Auto-save project file in the database directory
                project_name = project_data['name'].replace(' ', '_')
                project_file = os.path.join(project_dir, f'{project_name}.labelcraft')
                project.save(project_file)
                
                # Load the project
                self.load_project(project)
                
                print(f'New project created:')
                print(f'  Project file: {project.project_file}')
                print(f'  project_dir (database): {project.project_dir}')
                print(f'  annotation_dir: {project.annotation_dir}')
                print(f'  images_dir: {os.path.join(project.project_dir, "images")}')
                
                QMessageBox.information(
                    self,
                    self.get_str('successTitle'),
                    self.get_str('projectCreatedSuccess2').format(project.name) + '\n\n'
                    f'{self.get_str("projectLocation2")} {project_dir}\n'
                    f'{self.get_str("projectFile2")} {project_file}\n\n'
                    f'{project.get_info_summary()}'
                )
                
            except Exception as e:
                QMessageBox.critical(self, self.get_str('errorTitle'), self.get_str('createProjectFailed2') + str(e))
    
    def open_project_dialog(self):
        """Open an existing project"""
        
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            self.get_str('openProjectTitle'),
            self.last_open_dir or '.',
            'LabelCraft Project (*.labelcraft);;All Files (*)'
        )
        
        if not file_path:
            return
        
        try:
            # Load project
            project = Project.load(file_path)
            self.load_project(project)
            
            QMessageBox.information(
                self,
                self.get_str('successTitle'),
                self.get_str('projectLoaded').format(project.name) + '\n\n' + project.get_info_summary()
            )
            
        except FileNotFoundError:
            QMessageBox.critical(self, self.get_str('errorTitle'), self.get_str('projectFileNotExist').format(file_path))
        except Exception as e:
            QMessageBox.critical(self, self.get_str('errorTitle'), self.get_str('loadProjectFailed') + str(e))
    
    def load_project(self, project):
        """Load a project into the application"""
        self.current_project = project
        
        # Update label history
        self.label_hist = project.labels.copy()
        
        # Update default save directory
        self.default_save_dir = project.annotation_dir
        if hasattr(self, 'output_dir_label'):
            self.output_dir_label.setText(project.annotation_dir or '未设置')
        
        # Update output format
        format_map = {
            'PASCAL_VOC': LabelFileFormat.PASCAL_VOC,
            'YOLO': LabelFileFormat.YOLO,
            'CREATE_ML': LabelFileFormat.CREATE_ML
        }
        format_names = {
            'PASCAL_VOC': 'PASCAL VOC',
            'YOLO': 'YOLO',
            'CREATE_ML': 'CreateML'
        }
        self.label_file_format = format_map.get(project.format, LabelFileFormat.PASCAL_VOC)
        if hasattr(self, 'output_format_label'):
            self.output_format_label.setText(format_names.get(project.format, 'PASCAL VOC'))
        
        # Update default label combo box
        self.default_label_combo_box.update_items(self.label_hist)
        
        # Show/hide default label section based on whether labels exist
        has_labels = len(self.label_hist) > 0
        if hasattr(self, 'use_default_label_checkbox'):
            self.use_default_label_checkbox.setVisible(has_labels)
        if hasattr(self, 'default_label_combo_box'):
            self.default_label_combo_box.setVisible(has_labels)
        
        # Update label filter combo box
        self.update_combo_box()
        
        # Note: In the new design, images are not auto-loaded.
        # Users need to manually add images to the pending queue.
        # The project_dir is available via: self.current_project.project_dir
        
        # Ensure annotations directory exists
        if project.annotation_dir and not os.path.exists(project.annotation_dir):
            try:
                os.makedirs(project.annotation_dir, exist_ok=True)
                print(f'Created annotations directory: {project.annotation_dir}')
            except Exception as e:
                print(f'Warning: Could not create annotations directory: {e}')
        
        # Update completed annotations list
        self.update_completed_annotations_list()
        
        # Update window title
        self.setWindowTitle(f'{__appname__} - {project.name}')
        
        # Enable save project action
        self.actions.saveProject.setEnabled(True)
        self.actions.closeProject.setEnabled(True)
        self.actions.editProject.setEnabled(True)
        
        # Add to recent projects
        if project.project_file:
            RecentProjectsManager.add_project(project.project_file, project.name)
        
        print(f'Project loaded: {project.name}')
    
    def save_project(self):
        """Save current project"""
        if not self.current_project:
            QMessageBox.warning(self, '警告', '没有打开的项目')
            return
        
        try:
            # Update project with current state
            self.current_project.labels = self.label_hist.copy()
            self.current_project.annotation_dir = self.default_save_dir or ''
            
            # Save project file
            self.current_project.save()
            
            QMessageBox.information(self, '成功', '项目已保存')
            print(f'Project saved: {self.current_project.project_file}')
            
        except Exception as e:
            QMessageBox.critical(self, '错误', f'保存项目失败:\n{str(e)}')
    
    def close_project(self):
        """Close current project after saving and reset to initial state"""
        if not self.current_project:
            QMessageBox.warning(self, '警告', '没有打开的项目')
            return
        
        # Ask user to confirm
        reply = QMessageBox.question(
            self,
            '关闭项目',
            f'是否保存并关闭项目 "{self.current_project.name}"？',
            QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
            QMessageBox.Yes
        )
        
        if reply == QMessageBox.Cancel:
            return
        
        if reply == QMessageBox.Yes:
            # Save current image annotation if there are unsaved changes
            if self.dirty and self.file_path:
                try:
                    self.save_file()
                    print(f'Current image annotation saved before closing project')
                except Exception as e:
                    print(f'Warning: Failed to save current image: {e}')
            
            # Save project configuration
            try:
                self.current_project.labels = self.label_hist.copy()
                self.current_project.annotation_dir = self.default_save_dir or ''
                self.current_project.save()
                print(f'Project saved before closing: {self.current_project.project_file}')
            except Exception as e:
                QMessageBox.critical(self, '错误', f'保存项目失败:\n{str(e)}')
                return
        
        # Reset to initial state
        self.reset_to_initial_state()
        
        QMessageBox.information(self, '成功', '项目已关闭')
        print('Project closed')
    
    def reset_to_initial_state(self):
        """Reset application to initial state (no project loaded)"""
        
        # Clear current project
        self.current_project = None
        
        # Clear label history
        self.label_hist = []
        
        # Reset default save directory
        self.default_save_dir = None
        if hasattr(self, 'output_dir_label'):
            self.output_dir_label.setText(self.get_str('notSet'))
        
        # Reset output format label
        self.label_file_format = LabelFileFormat.PASCAL_VOC
        if hasattr(self, 'output_format_label'):
            self.output_format_label.setText(self.get_str('exportFormatVOC').split('(')[0].strip())
        
        # Clear default label combo box
        self.default_label_combo_box.update_items([])
        
        # Hide default label section when no labels
        if hasattr(self, 'use_default_label_checkbox'):
            self.use_default_label_checkbox.setVisible(False)
        if hasattr(self, 'default_label_combo_box'):
            self.default_label_combo_box.setVisible(False)
        
        # Clear label filter combo box
        self.combo_box.update_items([])
        
        # Clear image list
        self.m_img_list = []
        self.file_path = None
        self.last_open_dir = None
        self.cur_img_idx = 0
        self.img_count = 0
        
        # Clear canvas
        self.canvas.load_shapes([])
        self.canvas.reset_state()
        
        # Clear label list
        self.label_list.clear()
        
        # Clear file list (completed annotations)
        self.file_list_widget.clear()
        
        # Clear pending queue
        if hasattr(self, 'pending_list_widget'):
            self.pending_list_widget.clear()
        
        # Disable save project action
        self.actions.saveProject.setEnabled(False)
        self.actions.closeProject.setEnabled(False)
        self.actions.editProject.setEnabled(False)
        
        # Disable annotation buttons when no project loaded
        for action_item in [self.actions.create, self.actions.edit, self.actions.delete,
                           self.actions.copy, self.actions.createMode, self.actions.editMode]:
            action_item.setEnabled(False)
        
        # Reset window title
        self.setWindowTitle(__appname__)
        
        # Reset dirty flag
        self.dirty = False
    
    def update_recent_projects_menu(self):
        """Update the recent projects menu with latest projects"""
        
        self.menus.recentProjects.clear()
        
        recent_projects = RecentProjectsManager.load_recent_projects()
        
        if not recent_projects:
            # Show placeholder if no recent projects
            empty_action = QAction(self.get_str('noRecentProjects'), self)
            empty_action.setEnabled(False)
            self.menus.recentProjects.addAction(empty_action)
            return
        
        # Add each recent project as a menu item
        for i, project_info in enumerate(recent_projects):
            project_name = project_info.get('name', 'Unknown')
            project_path = project_info.get('path', '')
            
            # Create action with project name
            action_text = f"{i + 1}. {project_name}"
            action = QAction(action_text, self)
            action.setData(project_path)
            action.triggered.connect(partial(self.open_recent_project, project_path))
            self.menus.recentProjects.addAction(action)
        
        # Add separator and clear option
        self.menus.recentProjects.addSeparator()
        clear_action = QAction(self.get_str('clearList'), self)
        clear_action.triggered.connect(self.clear_recent_projects)
        self.menus.recentProjects.addAction(clear_action)
    
    def open_recent_project(self, project_path):
        """Open a project from recent projects list"""
        
        if not os.path.exists(project_path):
            QMessageBox.warning(
                self,
                self.get_str('warningTitle'),
                self.get_str('projectFileNotExist2') + f'\n{project_path}\n\n' + self.get_str('willRemoveFromList')
            )
            RecentProjectsManager.remove_project(project_path)
            return
        
        try:
            # Load project
            project = Project.load(project_path)
            self.load_project(project)
            
        except Exception as e:
            QMessageBox.critical(self, self.get_str('errorTitle'), self.get_str('loadProjectFailed2') + f'\n{str(e)}')
    
    def clear_recent_projects(self):
        """Clear all recent projects"""
        
        reply = QMessageBox.question(
            self,
            self.get_str('confirmTitle2'),
            self.get_str('confirmClearRecentProjects'),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            RecentProjectsManager.save_recent_projects([])
            QMessageBox.information(self, self.get_str('successTitle'), self.get_str('recentProjectsCleared'))

    def load_pascal_xml_by_filename(self, xml_path):
        if self.file_path is None:
            return
        if os.path.isfile(xml_path) is False:
            return

        self.set_format(FORMAT_PASCALVOC)

        t_voc_parse_reader = PascalVocReader(xml_path)
        shapes = t_voc_parse_reader.get_shapes()
        self.load_labels(shapes)
        self.canvas.verified = t_voc_parse_reader.verified

    def load_yolo_txt_by_filename(self, txt_path):
        if self.file_path is None:
            return
        if os.path.isfile(txt_path) is False:
            return

        self.set_format(FORMAT_YOLO)
        t_yolo_parse_reader = YoloReader(txt_path, self.image)
        shapes = t_yolo_parse_reader.get_shapes()
        print(shapes)
        self.load_labels(shapes)
        self.canvas.verified = t_yolo_parse_reader.verified

    def load_create_ml_json_by_filename(self, json_path, file_path):
        if self.file_path is None:
            return
        if os.path.isfile(json_path) is False:
            return

        self.set_format(FORMAT_CREATEML)

        create_ml_parse_reader = CreateMLReader(json_path, file_path)
        shapes = create_ml_parse_reader.get_shapes()
        self.load_labels(shapes)
        self.canvas.verified = create_ml_parse_reader.verified

    def copy_previous_bounding_boxes(self):
        current_index = self.m_img_list.index(self.file_path)
        if current_index - 1 >= 0:
            prev_file_path = self.m_img_list[current_index - 1]
            self.show_bounding_box_from_annotation_file(prev_file_path)
            self.save_file()

    def toggle_paint_labels_option(self):
        for shape in self.canvas.shapes:
            shape.paint_label = self.display_label_option.isChecked()

    def toggle_draw_square(self):
        self.canvas.set_drawing_shape_to_square(self.draw_squares_option.isChecked())

    def export_annotations_dialog(self, _value=False):
        """Export all annotations and corresponding images to a specified directory
        
        This function exports:
        - Annotated images (only those with annotations)
        - Annotation files in selected format
        - Does NOT include project files (.labelcraft)
        """
        
        # Check if there are any annotations to export
        # Determine annotation directory
        anno_dir = None
        if self.current_project and self.current_project.annotation_dir:
            anno_dir = os.path.join(self.current_project.annotation_dir, 'annotations')
        elif self.default_save_dir:
            anno_dir = self.default_save_dir
        
        if not anno_dir or not os.path.exists(anno_dir):
            QMessageBox.warning(self, self.get_str('warningTitle'), 
                self.get_str('noSavedAnnotations') + '\n\n' +
                self.get_str('pleaseAnnotateFirst'))
            return
        
        # Scan for annotation files
        import glob
        annotation_files = []
        for ext in ['*.xml', '*.txt', '*.json']:
            annotation_files.extend(glob.glob(os.path.join(anno_dir, ext)))
        
        # Exclude classes.txt for YOLO format
        annotation_files = [f for f in annotation_files if not f.endswith('classes.txt')]
        
        if not annotation_files:
            QMessageBox.warning(self, '警告', 
                '没有找到已保存的标注文件。\n\n'
                f'检查目录: {anno_dir}\n\n'
                '请先标注并保存至少一张图像，然后再导出。')
            return
        
        # Create format selection dialog
        from PySide6.QtWidgets import QFileDialog, QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QGroupBox, QRadioButton, QCheckBox
        
        dialog = QDialog(self)
        dialog.setWindowTitle(self.get_str('exportDialogTitle'))
        dialog.setMinimumSize(500, 450)
        
        main_layout = QVBoxLayout()
        
        # Format selection group
        format_group = QGroupBox(self.get_str('formatSelection'))
        format_layout = QVBoxLayout()
        
        format_voc = QRadioButton('PASCAL VOC (XML)')
        format_yolo = QRadioButton('YOLO (TXT)')
        format_createml = QRadioButton('CreateML (JSON)')
        format_coco = QRadioButton('COCO (JSON)')
        format_csv = QRadioButton('CSV')
        
        # Set default based on current format
        if self.label_file_format == LabelFileFormat.PASCAL_VOC:
            format_voc.setChecked(True)
        elif self.label_file_format == LabelFileFormat.YOLO:
            format_yolo.setChecked(True)
        elif self.label_file_format == LabelFileFormat.CREATE_ML:
            format_createml.setChecked(True)
        elif self.label_file_format == LabelFileFormat.COCO:
            format_coco.setChecked(True)
        elif self.label_file_format == LabelFileFormat.CSV:
            format_csv.setChecked(True)
        else:
            format_voc.setChecked(True)
        
        format_layout.addWidget(format_voc)
        format_layout.addWidget(format_yolo)
        format_layout.addWidget(format_createml)
        format_layout.addWidget(format_coco)
        format_layout.addWidget(format_csv)
        format_group.setLayout(format_layout)
        main_layout.addWidget(format_group)
        
        # Options group
        options_group = QGroupBox(self.get_str('exportOptions'))
        options_layout = QVBoxLayout()
        
        export_images_check = QCheckBox(self.get_str('exportImagesOption'))
        export_images_check.setChecked(True)
        options_layout.addWidget(export_images_check)
        
        only_annotated_check = QCheckBox(self.get_str('onlyAnnotatedOption'))
        only_annotated_check.setChecked(True)
        options_layout.addWidget(only_annotated_check)
        
        options_group.setLayout(options_layout)
        main_layout.addWidget(options_group)
        
        # Info label
        info_label = QLabel(
            self.get_str('exportInstructions') + '\n'
            + self.get_str('willCreateDirs') + '\n'
            + self.get_str('skipUnannotated') + '\n'
            + self.get_str('noProjectFile') + '\n'
            + self.get_str('supportConversion')
        )
        info_label.setWordWrap(True)
        main_layout.addWidget(info_label)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_ok = QPushButton(self.get_str('startExport'))
        button_cancel = QPushButton(self.get_str('cancel'))
        button_layout.addStretch()
        button_layout.addWidget(button_ok)
        button_layout.addWidget(button_cancel)
        main_layout.addLayout(button_layout)
        
        dialog.setLayout(main_layout)
        
        # Connect buttons
        selected_format = [None]
        def on_ok():
            if format_voc.isChecked():
                selected_format[0] = LabelFileFormat.PASCAL_VOC
            elif format_yolo.isChecked():
                selected_format[0] = LabelFileFormat.YOLO
            elif format_createml.isChecked():
                selected_format[0] = LabelFileFormat.CREATE_ML
            elif format_coco.isChecked():
                selected_format[0] = LabelFileFormat.COCO
            elif format_csv.isChecked():
                selected_format[0] = LabelFileFormat.CSV
            dialog.accept()
        
        button_ok.clicked.connect(on_ok)
        button_cancel.clicked.connect(dialog.reject)
        
        # Show dialog
        if dialog.exec() != QDialog.Accepted or selected_format[0] is None:
            return
        
        # Open directory selection dialog
        export_dir = QFileDialog.getExistingDirectory(
            self,
            self.get_str('selectExportDir'),
            self.last_open_dir or '.',
            QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks
        )
        
        if not export_dir:
            return
        
        export_dir = ustr(export_dir)
        
        # Create subdirectories for export
        import shutil
        dest_images_dir = os.path.join(export_dir, 'images')
        dest_annotations_dir = os.path.join(export_dir, 'annotations')
        
        os.makedirs(dest_images_dir, exist_ok=True)
        os.makedirs(dest_annotations_dir, exist_ok=True)
        
        # Determine output format extension
        if selected_format[0] == LabelFileFormat.PASCAL_VOC:
            ext = '.xml'
        elif selected_format[0] == LabelFileFormat.YOLO:
            ext = '.txt'
        elif selected_format[0] == LabelFileFormat.CREATE_ML:
            ext = '.json'
        elif selected_format[0] == LabelFileFormat.COCO:
            ext = '.json'
        elif selected_format[0] == LabelFileFormat.CSV:
            ext = '.csv'
        else:
            ext = '.xml'
        
        exported_count = 0
        skipped_count = 0
        error_count = 0
        
        # Import the annotation converter
        from libs.annotation_converter import AnnotationConverter
        
        # Detect input format based on file extension
        def detect_format(file_path):
            ext = os.path.splitext(file_path)[1].lower()
            if ext == '.xml':
                return 'voc'
            elif ext == '.txt':
                return 'yolo'
            elif ext == '.json':
                # Try to detect if it's CreateML or COCO
                try:
                    with open(file_path, 'r') as f:
                        data = json.load(f)
                    if isinstance(data, list) and len(data) > 0 and 'image' in data[0]:
                        return 'createml'
                    elif 'images' in data and 'annotations' in data:
                        return 'coco'
                except:
                    pass
                return 'createml'  # Default to CreateML
            elif ext == '.csv':
                return 'csv'
            return 'voc'  # Default
        
        # Map LabelFileFormat to converter format strings
        format_map = {
            LabelFileFormat.PASCAL_VOC: 'voc',
            LabelFileFormat.YOLO: 'yolo',
            LabelFileFormat.CREATE_ML: 'createml',
            LabelFileFormat.COCO: 'coco',
            LabelFileFormat.CSV: 'csv'
        }
        
        output_format_str = format_map.get(selected_format[0], 'voc')
        
        # Get classes list for YOLO and COCO formats
        classes_list = self.label_hist if self.label_hist else []
        
        try:
            # Iterate through all annotation files
            for anno_file_path in annotation_files:
                if not os.path.exists(anno_file_path):
                    continue
                
                anno_filename = os.path.basename(anno_file_path)
                base_name = os.path.splitext(anno_filename)[0]
                
                # Find corresponding image file
                img_path = None
                image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tif', '.tiff', '.gif', '.webp']
                
                # Method 1: Try project's images directory (standard structure)
                if self.current_project and self.current_project.project_dir:
                    images_dir = os.path.join(self.current_project.project_dir, 'images')
                    if os.path.exists(images_dir):
                        for ext in image_extensions:
                            candidate = os.path.join(images_dir, base_name + ext)
                            if os.path.exists(candidate):
                                img_path = candidate
                                break
                
                # Method 2: Try annotation_dir's sibling images directory (database structure)
                # If annotation_dir is like /path/database/annotations, look for /path/database/images
                if not img_path:
                    # Check if we have annotation_dir from project
                    actual_anno_dir = None
                    if self.current_project and self.current_project.annotation_dir:
                        actual_anno_dir = os.path.join(self.current_project.annotation_dir, 'annotations')
                    elif self.default_save_dir:
                        actual_anno_dir = self.default_save_dir
                    
                    if actual_anno_dir and os.path.exists(actual_anno_dir):
                        database_dir = os.path.dirname(actual_anno_dir)
                        images_dir = os.path.join(database_dir, 'images')
                        if os.path.exists(images_dir):
                            for ext in image_extensions:
                                candidate = os.path.join(images_dir, base_name + ext)
                                if os.path.exists(candidate):
                                    img_path = candidate
                                    break
                
                # Method 3: Try annotation file's directory (same folder as annotation)
                if not img_path:
                    anno_dir_path = os.path.dirname(anno_file_path)
                    for ext in image_extensions:
                        candidate = os.path.join(anno_dir_path, base_name + ext)
                        if os.path.exists(candidate):
                            img_path = candidate
                            break
                
                # Method 4: Try current working directory
                if not img_path:
                    for ext in image_extensions:
                        candidate = os.path.join(os.getcwd(), base_name + ext)
                        if os.path.exists(candidate):
                            img_path = candidate
                            break
                
                # If still not found, skip this annotation
                if not img_path:
                    print(f"Warning: Image not found for {anno_filename}")
                    print(f"  Searched in:")
                    if self.current_project and self.current_project.project_dir:
                        print(f"    - {os.path.join(self.current_project.project_dir, 'images')}")
                    if self.default_save_dir:
                        database_dir = os.path.dirname(self.default_save_dir)
                        print(f"    - {os.path.join(database_dir, 'images')}")
                    print(f"    - {os.path.dirname(anno_file_path)}")
                    print(f"    - {os.getcwd()}")
                    skipped_count += 1
                    continue
                
                img_name = os.path.basename(img_path)
                dest_anno_file = base_name + ext
                
                # We already know this has annotation (we're iterating annotation files)
                source_anno_path = anno_file_path
                
                try:
                    # Copy image if option is checked
                    if export_images_check.isChecked():
                        dest_img_path = os.path.join(dest_images_dir, img_name)
                        # Check if source and destination are the same file
                        if os.path.abspath(img_path) != os.path.abspath(dest_img_path):
                            shutil.copy2(img_path, dest_img_path)
                        else:
                            print(f"Skipping copy: source and destination are the same file")
                    
                    # Handle annotation conversion using the unified converter
                    dest_anno_path = os.path.join(dest_annotations_dir, dest_anno_file)
                    
                    # Detect input format
                    input_format_str = detect_format(anno_file_path)
                    
                    # Convert using the unified converter
                    AnnotationConverter.convert(
                        input_path=anno_file_path,
                        input_format=input_format_str,
                        output_path=dest_anno_path,
                        output_format=output_format_str,
                        classes_list=classes_list
                    )
                    
                    exported_count += 1
                    
                    # Update progress
                    if exported_count % 10 == 0:
                        self.statusBar().showMessage(f'正在导出: {exported_count} / {len(annotation_files)}')
                        QApplication.processEvents()
                        
                except Exception as e:
                    print(f"Error exporting {img_name}: {e}")
                    import traceback
                    traceback.print_exc()
                    error_count += 1
            
            # Show result
            result_msg = f'{self.get_str("exportComplete")}\n\n'
            result_msg += f'{self.get_str("successfullyExported").format(exported_count)}\n'
            if skipped_count > 0:
                result_msg += f'{self.get_str("skippedImageNotFound").format(skipped_count)}\n'
            if error_count > 0:
                result_msg += f'{self.get_str("errors").format(error_count)}\n'
            result_msg += f'\n{self.get_str("exportFormat")}: {selected_format[0].name}\n'
            result_msg += f'{self.get_str("exportLocation")}: {export_dir}'
            
            QMessageBox.information(self, self.get_str('exportComplete'), result_msg)
            
            print(f"Export completed: {exported_count} files exported to {export_dir}")
            
        except Exception as e:
            QMessageBox.critical(self, self.get_str('errorTitle'), 
                f'{self.get_str("exportFailed")}\n\n{str(e)}')
            import traceback
            traceback.print_exc()


def inverted(color):
    return QColor(*[255 - v for v in color.getRgb()])


def read(filename, default=None):
    try:
        reader = QImageReader(filename)
        reader.setAutoTransform(True)
        return reader.read()
    except:
        return default


def get_main_app(argv=None):
    """
    Standard boilerplate Qt application code.
    Do everything but app.exec_() -- so that we can test the application in one thread
    """
    if not argv:
        argv = []
    app = QApplication(argv)
    app.setApplicationName(__appname__)
    app.setWindowIcon(new_icon("app"))
    
    # Tzutalin 201705+: Accept extra arguments to change predefined class file
    argparser = argparse.ArgumentParser(
        prog='labelcraft',
        description=f'{__appname__} - A modern graphical image annotation tool',
        epilog='Examples:\n'
               '  labelcraft                          # Start without parameters\n'
               '  labelcraft /path/to/images          # Open images from directory\n'
               '  labelcraft --classes classes.txt    # Use custom class file\n'
               '  labelcraft --save-dir ./output      # Set default save directory\n',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # Positional arguments (optional)
    argparser.add_argument(
        "image_dir",
        nargs="?",
        help="Directory containing images to annotate (optional)"
    )
    
    # Optional arguments with better descriptions
    argparser.add_argument(
        "--classes", "-c",
        dest="class_file",
        default=os.path.join(os.path.dirname(__file__), "data", "predefined_classes.txt"),
        help="Path to predefined classes file (default: data/predefined_classes.txt)"
    )
    
    argparser.add_argument(
        "--save-dir", "-s",
        dest="save_dir",
        nargs="?",
        help="Default directory to save annotations (optional)"
    )
    
    argparser.add_argument(
        "--version", "-v",
        action="version",
        version=f"{__appname__} {__version__}",
        help="Show program version and exit"
    )
    
    args = argparser.parse_args(argv[1:])

    args.image_dir = args.image_dir and os.path.normpath(args.image_dir)
    args.class_file = args.class_file and os.path.normpath(args.class_file)
    args.save_dir = args.save_dir and os.path.normpath(args.save_dir)

    # Usage : labelcraft.py image classFile saveDir
    win = MainWindow(args.image_dir,
                     args.class_file,
                     args.save_dir)
    
    # Process events before showing to ensure proper initialization
    app.processEvents()
    
    # Set a minimum size to avoid layout calculation issues
    win.setMinimumSize(800, 600)
    win.show()
    
    # Process events after showing
    app.processEvents()
    
    return app, win


def main():
    """construct main app and run it"""
    app, _win = get_main_app(sys.argv)
    return app.exec()


if __name__ == '__main__':
    main()
