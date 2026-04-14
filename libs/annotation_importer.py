#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Annotation Importer - Handles importing annotations from external directories

This module provides functionality to import annotation data from various formats
into the current project, with automatic format conversion and image copying.
"""
import os
import glob
import shutil
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                                QGroupBox, QComboBox, QPushButton, QCheckBox,
                                QProgressDialog, QMessageBox, QApplication)
from PySide6.QtCore import Qt


class AnnotationImporter:
    """
    Handles the complete annotation import workflow.
    
    Usage:
        importer = AnnotationImporter(parent_window, current_project, get_str_func)
        success = importer.import_annotations()
    """
    
    def __init__(self, parent, current_project, get_str_func):
        """
        Initialize the annotation importer.
        
        Args:
            parent: Parent widget (MainWindow)
            current_project: Current project object
            get_str_func: Function to get translated strings
        """
        self.parent = parent
        self.current_project = current_project
        self.get_str = get_str_func
        
    def import_annotations(self):
        """
        Main entry point for importing annotations.
        Returns True if import was successful, False otherwise.
        """
        # Check if a project is open
        if not self.current_project:
            QMessageBox.warning(
                self.parent,
                self.get_str('warningTitle'),
                self.get_str('noOpenProjectWarning2') + '\n\n' +
                self.get_str('importNoProjectWarning')
            )
            return False
        
        # Step 1: Select source format
        selected_format = self._select_format_dialog()
        if not selected_format:
            return False
        
        # Step 2: Select source directory
        source_dir = self._select_source_directory()
        if not source_dir:
            return False
        
        # Step 2.5: If auto-detect selected, determine format BEFORE scanning
        actual_format_for_scan = selected_format
        if selected_format == 'auto':
            # Try to detect format from directory structure first
            detected_hint = self._detect_format_hint()
            if detected_hint:
                actual_format_for_scan = detected_hint
                print(f"[Auto-detect] Using format hint: {detected_hint}")
            else:
                # No hint, use generic scan (will detect from file content later)
                actual_format_for_scan = None
                print("[Auto-detect] No format hint, will scan all files")
        
        # Step 3: Scan for annotation files
        # If we have a detected format, use it for scanning; otherwise scan broadly
        scan_format = actual_format_for_scan if actual_format_for_scan else 'auto'
        annotation_files = self._scan_annotation_files(source_dir, scan_format)
        if not annotation_files:
            QMessageBox.warning(
                self.parent,
                self.get_str('warningTitle'),
                self.get_str('importNoFilesFound').format(source_dir)
            )
            return False
        
        # Step 3.5: If auto-detect, determine actual format from scanned files
        actual_format = selected_format
        if selected_format == 'auto':
            actual_format = self._detect_actual_format(annotation_files, source_dir)
            if not actual_format:
                QMessageBox.warning(
                    self.parent,
                    self.get_str('warningTitle'),
                    self.get_str('importAutoDetectFailed')
                )
                return False
            print(f"Auto-detected format: {actual_format}")
        
        # Step 4: Confirm and perform import with actual format
        # For YOLO format, try to extract labels from data.yaml
        yolo_labels = None
        if actual_format == 'yolo' or selected_format == 'yolo':
            try:
                yolo_labels = self._parse_yolo_data_yaml(source_dir)
                if yolo_labels:
                    print(f"Detected {len(yolo_labels)} classes from data.yaml: {yolo_labels[:5]}...")
            except Exception as e:
                print(f"Warning: Failed to parse data.yaml: {e}")
                print("Continuing without data.yaml labels...")
                yolo_labels = None
        
        return self._confirm_and_import(source_dir, annotation_files, selected_format, actual_format, yolo_labels)
    
    def _select_format_dialog(self):
        """Show dialog to select source annotation format with auto-detection."""
        format_dialog = QDialog(self.parent)
        format_dialog.setWindowTitle(self.get_str('importDialogTitle'))
        format_dialog.setMinimumWidth(450)
        
        format_layout = QVBoxLayout()
        
        # Format selection
        format_group = QGroupBox(self.get_str('importSourceFormat'))
        format_group_layout = QVBoxLayout()
        
        format_combo = QComboBox()
        format_options = [
            ('auto', '🔍 Auto-detect (Recommended)'),
            ('voc', 'PASCAL VOC (XML)'),
            ('yolo', 'YOLO (TXT)'),
            ('coco', 'COCO (JSON)'),
            ('createml', 'CreateML (JSON)'),
            ('json', 'LabelCraft JSON'),
            ('csv', 'CSV')
        ]
        
        for value, text in format_options:
            format_combo.addItem(text, value)
        
        # Auto-select based on common patterns
        detected_format = self._detect_format_hint()
        if detected_format:
            for i in range(format_combo.count()):
                if format_combo.itemData(i) == detected_format:
                    format_combo.setCurrentIndex(i)
                    break
        
        format_group_layout.addWidget(format_combo)
        format_group.setLayout(format_group_layout)
        format_layout.addWidget(format_group)
        
        # Info message
        info_label = QLabel(
            'ℹ️ ' + self.get_str('importInfoMessage')
        )
        info_label.setWordWrap(True)
        # Use Qt palette for automatic theme adaptation
        info_label.setStyleSheet(
            'padding: 10px; border-radius: 5px; '
            'background-color: palette(alternate-base); '
            'color: palette(text);'
        )
        format_layout.addWidget(info_label)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_next = QPushButton(self.get_str('importButtonNext'))
        btn_cancel = QPushButton(self.get_str('importButtonCancel'))
        btn_layout.addStretch()
        btn_layout.addWidget(btn_next)
        btn_layout.addWidget(btn_cancel)
        format_layout.addLayout(btn_layout)
        
        format_dialog.setLayout(format_layout)
        
        selected_format = None
        
        def on_next():
            nonlocal selected_format
            selected_format = format_combo.currentData()
            format_dialog.accept()
        
        btn_next.clicked.connect(on_next)
        btn_cancel.clicked.connect(format_dialog.reject)
        
        if format_dialog.exec() != QDialog.Accepted:
            return None
        
        return selected_format
    
    def _detect_format_hint(self):
        """
        Detect likely format based on common directory structures and files.
        This is a hint, not definitive detection.
        
        Returns:
            str: Detected format code or None
        """
        # Check last_open_dir for hints
        check_dir = getattr(self.parent, 'last_open_dir', None)
        if not check_dir or not os.path.exists(check_dir):
            return None
        
        # ===== YOLO Detection (highest priority) =====
        
        # 1. Check for data.yaml in current directory
        data_yaml_path = os.path.join(check_dir, 'data.yaml')
        if os.path.exists(data_yaml_path):
            print(f"[Format Hint] Found data.yaml in {check_dir}")
            return 'yolo'
        
        # 2. Check parent directory for data.yaml (if user selected images/ or labels/)
        parent_dir = os.path.dirname(check_dir)
        if os.path.exists(os.path.join(parent_dir, 'data.yaml')):
            print(f"[Format Hint] Found data.yaml in parent dir {parent_dir}")
            return 'yolo'
        
        # 3. Check grandparent directory (in case of deeper nesting)
        grandparent_dir = os.path.dirname(parent_dir)
        if os.path.exists(os.path.join(grandparent_dir, 'data.yaml')):
            print(f"[Format Hint] Found data.yaml in grandparent dir {grandparent_dir}")
            return 'yolo'
        
        # 4. Check for labels/ directory (classic YOLO structure)
        if os.path.exists(os.path.join(check_dir, 'labels')):
            print(f"[Format Hint] Found labels/ directory in {check_dir}")
            return 'yolo'
        
        # 5. If current dir IS labels/, check for sibling images/
        if os.path.basename(check_dir).lower() == 'labels':
            images_dir = os.path.join(parent_dir, 'images')
            if os.path.exists(images_dir):
                print(f"[Format Hint] Current dir is labels/, found sibling images/")
                return 'yolo'
        
        # 6. If current dir IS images/, check for sibling labels/
        if os.path.basename(check_dir).lower() == 'images':
            labels_dir = os.path.join(parent_dir, 'labels')
            if os.path.exists(labels_dir):
                print(f"[Format Hint] Current dir is images/, found sibling labels/")
                return 'yolo'
        
        # ===== VOC Detection =====
        # Check for XML files (PASCAL VOC format)
        xml_files = glob.glob(os.path.join(check_dir, '*.xml'))
        if xml_files:
            print(f"[Format Hint] Found {len(xml_files)} XML files")
            return 'voc'
        
        # Also check Annotations/ subdirectory (common VOC structure)
        annotations_dir = os.path.join(check_dir, 'Annotations')
        if os.path.exists(annotations_dir):
            xml_in_subdir = glob.glob(os.path.join(annotations_dir, '*.xml'))
            if xml_in_subdir:
                print(f"[Format Hint] Found {len(xml_in_subdir)} XML files in Annotations/")
                return 'voc'
        
        # ===== COCO/CreateML Detection =====
        json_files = glob.glob(os.path.join(check_dir, '*.json'))
        if json_files:
            # Filter out non-annotation JSON files
            annotation_jsons = [f for f in json_files 
                              if not os.path.basename(f).lower().startswith(('data', 'classes', 'info', 'config'))]
            
            if annotation_jsons:
                # Check file content to distinguish COCO vs CreateML
                for jf in annotation_jsons[:3]:
                    try:
                        with open(jf, 'r') as f:
                            import json as json_module
                            data = json_module.load(f)
                            
                            # COCO format: dict with 'images', 'annotations', 'categories'
                            if isinstance(data, dict) and 'images' in data and 'annotations' in data:
                                print(f"[Format Hint] Detected COCO format in {os.path.basename(jf)}")
                                return 'coco'
                            
                            # CreateML format: list of objects with 'image' key
                            elif isinstance(data, list) and len(data) > 0:
                                if isinstance(data[0], dict) and 'image' in data[0]:
                                    print(f"[Format Hint] Detected CreateML format in {os.path.basename(jf)}")
                                    return 'createml'
                    except Exception as e:
                        print(f"[Format Hint] Failed to parse {jf}: {e}")
                        pass
        
        # Check for standard COCO filenames
        coco_filenames = ['instances_train2017.json', 'instances_val2017.json', 
                         'instances_default.json', 'coco_annotations.json']
        for coco_name in coco_filenames:
            if os.path.exists(os.path.join(check_dir, coco_name)):
                print(f"[Format Hint] Found standard COCO filename: {coco_name}")
                return 'coco'
        
        # Check for standard CreateML filename
        if os.path.exists(os.path.join(check_dir, 'annotations.json')):
            print(f"[Format Hint] Found standard CreateML filename: annotations.json")
            return 'createml'
        
        # ===== CSV Detection =====
        csv_files = glob.glob(os.path.join(check_dir, '*.csv'))
        if csv_files:
            # Filter out non-annotation CSV files
            annotation_csvs = [f for f in csv_files 
                             if not os.path.basename(f).lower().startswith(('data', 'classes', 'info'))]
            if annotation_csvs:
                print(f"[Format Hint] Found {len(annotation_csvs)} CSV files")
                return 'csv'
        
        print(f"[Format Hint] No specific format detected in {check_dir}")
        return None
    
    def _detect_actual_format(self, annotation_files, source_dir):
        """
        Detect the actual format by examining the annotation files.
        This is called after scanning to determine the real format when 'auto' is selected.
        
        Args:
            annotation_files: List of annotation file paths
            source_dir: Source directory path
            
        Returns:
            str: Detected format code or None
        """
        if not annotation_files:
            return None
        
        # Check first few files to determine format
        sample_files = annotation_files[:3]
        
        for sample_file in sample_files:
            ext = os.path.splitext(sample_file)[1].lower()
            
            # XML -> VOC
            if ext == '.xml':
                return 'voc'
            
            # TXT -> YOLO (check content)
            elif ext == '.txt':
                try:
                    with open(sample_file, 'r') as f:
                        first_line = f.readline().strip()
                        # YOLO format: class_id x y w h (space-separated numbers)
                        parts = first_line.split()
                        if len(parts) == 5 and all(self._is_number(p) for p in parts):
                            return 'yolo'
                except:
                    pass
            
            # JSON -> Check content
            elif ext == '.json':
                try:
                    with open(sample_file, 'r') as f:
                        import json as json_module
                        data = json_module.load(f)
                        
                        # COCO format: dict with 'images', 'annotations', 'categories'
                        if isinstance(data, dict) and 'images' in data and 'annotations' in data:
                            return 'coco'
                        
                        # CreateML format: list of objects
                        elif isinstance(data, list) and len(data) > 0:
                            if isinstance(data[0], dict) and 'image' in data[0]:
                                return 'createml'
                        
                        # LabelCraft JSON: single annotation object
                        elif isinstance(data, dict) and ('shapes' in data or 'annotation' in data):
                            return 'json'
                except:
                    pass
            
            # CSV
            elif ext == '.csv':
                return 'csv'
        
        return None
    
    def _is_number(self, s):
        """Check if string is a number."""
        try:
            float(s)
            return True
        except ValueError:
            return False
    
    def _parse_yolo_data_yaml(self, source_dir):
        """
        Parse YOLO data.yaml file to extract class names.
        
        Args:
            source_dir: Source directory path (may contain data.yaml or be in images/labels/)
            
        Returns:
            list: List of class names or None if not found
        """
        # Try to import yaml
        try:
            import yaml
        except ImportError as e:
            print(f"Warning: PyYAML is not installed. Cannot parse data.yaml.")
            print(f"Error: {e}")
            print("Install it with: pip install PyYAML")
            return None
        
        # Try to find data.yaml in multiple locations
        possible_paths = [
            os.path.join(source_dir, 'data.yaml'),
            os.path.join(os.path.dirname(source_dir), 'data.yaml'),  # If source_dir is images/ or labels/
        ]
        
        data_yaml_path = None
        for path in possible_paths:
            if os.path.exists(path):
                data_yaml_path = path
                break
        
        if not data_yaml_path:
            return None
        
        try:
            with open(data_yaml_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            # Extract class names from 'names' field
            if 'names' in data:
                names = data['names']
                
                # Handle both list and dict formats
                if isinstance(names, list):
                    # List format: ['cat', 'dog', 'bird']
                    return [str(name).strip() for name in names if name]
                elif isinstance(names, dict):
                    # Dict format: {0: 'cat', 1: 'dog'}
                    return [str(names[k]).strip() for k in sorted(names.keys()) if names[k]]
            
            # Fallback: try 'nc' (number of classes) and generate generic names
            if 'nc' in data:
                nc = int(data['nc'])
                print(f"Warning: data.yaml has 'nc' but no 'names'. Generated {nc} generic class names.")
                return [f'class_{i}' for i in range(nc)]
            
            return None
            
        except Exception as e:
            print(f"Warning: Failed to parse data.yaml: {e}")
            return None
    
    def _select_source_directory(self):
        """Show directory selection dialog."""
        from PySide6.QtWidgets import QFileDialog
        
        source_dir = QFileDialog.getExistingDirectory(
            self.parent,
            self.get_str('importSelectDirTitle'),
            self.parent.last_open_dir or '.',
            QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks
        )
        
        if not source_dir:
            return None
        
        from libs.ustr import ustr
        return ustr(source_dir)
    
    def _scan_annotation_files(self, source_dir, selected_format):
        """
        Scan for annotation files based on selected format.
        
        For YOLO format, searches recursively in labels/ subdirectory.
        For 'auto' format, scans for all common annotation file types.
        For other formats, searches in the specified directory.
        """
        annotation_files = []
        
        # Map format to file extension
        ext_map = {
            'voc': '*.xml',
            'yolo': '*.txt',
            'coco': '*.json',
            'createml': '*.json',
            'json': '*.json',
            'csv': '*.csv'
        }
        
        # For 'auto' format, scan for all common annotation types
        if selected_format == 'auto':
            print(f"[Scan] Auto mode: scanning for all annotation file types in {source_dir}")
            # Scan for all common annotation extensions
            for ext in ['*.xml', '*.txt', '*.json', '*.csv']:
                files = glob.glob(os.path.join(source_dir, ext))
                annotation_files.extend(files)
            
            # Also check for YOLO labels/ directory
            labels_dir = os.path.join(source_dir, 'labels')
            if os.path.exists(labels_dir):
                print(f"[Scan] Found labels/ directory, scanning recursively")
                for root, dirs, files in os.walk(labels_dir):
                    for file in files:
                        if file.endswith('.txt') and not file.startswith('.'):
                            annotation_files.append(os.path.join(root, file))
            
            # Filter out non-annotation files
            annotation_files = [f for f in annotation_files 
                              if not os.path.basename(f).lower().startswith(('data', 'classes', 'info', 'config'))]
        elif selected_format == 'yolo':
            # For YOLO format, search in labels/ subdirectory recursively
            labels_dir = os.path.join(source_dir, 'labels')
            if os.path.exists(labels_dir):
                # Recursively search in labels/ directory
                for root, dirs, files in os.walk(labels_dir):
                    for file in files:
                        if file.endswith('.txt') and not file.startswith('.'):
                            annotation_files.append(os.path.join(root, file))
            else:
                # No labels/ directory, search in current directory
                ext_pattern = ext_map.get(selected_format, '*.txt')
                annotation_files = glob.glob(os.path.join(source_dir, ext_pattern))
        else:
            # For other formats, search in current directory
            ext_pattern = ext_map.get(selected_format, '*.*')
            annotation_files = glob.glob(os.path.join(source_dir, ext_pattern))
        
        # Filter out hidden files and directories
        annotation_files = [f for f in annotation_files 
                          if not os.path.basename(f).startswith('.')]
        
        print(f"[Scan] Found {len(annotation_files)} annotation files")
        return sorted(annotation_files)
    
    def _confirm_and_import(self, source_dir, annotation_files, selected_format, actual_format=None, yolo_labels=None):
        """
        Show confirmation dialog and perform import.
        
        Args:
            source_dir: Source directory path
            annotation_files: List of annotation files
            selected_format: Format selected by user (may be 'auto')
            actual_format: Actual detected format (used for conversion)
            yolo_labels: Labels extracted from data.yaml (for YOLO format)
        """
        # If actual_format not provided, use selected_format
        if actual_format is None:
            actual_format = selected_format
        confirm_dialog = QDialog(self.parent)
        confirm_dialog.setWindowTitle(self.get_str('importConfirmTitle'))
        confirm_dialog.setMinimumWidth(650)
        
        main_layout = QVBoxLayout()
        
        # Source info with preview
        info_group = QGroupBox(self.get_str('importSourceGroup'))
        info_layout = QVBoxLayout()
        
        # Basic info
        basic_info = QLabel(
            f"<b>{self.get_str('importSourceDir')}</b> {source_dir}<br>"
            f"<b>{self.get_str('importDetectedFiles')}</b> <span style='color: blue;'>{len(annotation_files)}</span> files"
        )
        basic_info.setWordWrap(True)
        info_layout.addWidget(basic_info)
        
        format_names = {
            'auto': 'Auto-detect',
            'voc': 'PASCAL VOC (XML)',
            'yolo': 'YOLO (TXT)',
            'coco': 'COCO (JSON)',
            'createml': 'CreateML (JSON)',
            'json': 'LabelCraft JSON',
            'csv': 'CSV'
        }
        
        # Show selected format and detected format if different
        if selected_format == 'auto' and actual_format != 'auto':
            format_display = f"{format_names.get(selected_format, selected_format)} → <b>{format_names.get(actual_format, actual_format)}</b>"
        else:
            format_display = format_names.get(selected_format, selected_format)
        
        info_layout.addWidget(QLabel(f"<b>{self.get_str('importSelectedFormat')}</b> {format_display}"))
        
        # Preview sample files
        if annotation_files:
            preview_label = QLabel("<b>" + self.get_str('importSampleFiles') + "</b>")
            info_layout.addWidget(preview_label)
            
            preview_text = "\n".join([
                f"  • {os.path.basename(f)}"
                for f in annotation_files[:5]
            ])
            if len(annotation_files) > 5:
                preview_text += "\n  " + self.get_str('importMoreFiles').format(len(annotation_files) - 5)
            
            preview_widget = QLabel(preview_text)
            # Use palette for automatic theme adaptation
            preview_widget.setStyleSheet(
                'background-color: palette(base); padding: 8px; border-radius: 4px; '
                'font-family: monospace; font-size: 11px; color: palette(text);'
            )
            preview_widget.setWordWrap(True)
            info_layout.addWidget(preview_widget)
        
        info_group.setLayout(info_layout)
        main_layout.addWidget(info_group)
        
        # Target info
        target_group = QGroupBox(self.get_str('importTargetGroup'))
        target_layout = QVBoxLayout()
        
        format_names_proj = {
            'PASCAL_VOC': 'PASCAL VOC',
            'YOLO': 'YOLO',
            'CREATE_ML': 'CreateML',
            'LABELCRAFT_JSON': 'LabelCraft JSON',
            'COCO': 'COCO',
            'CSV': 'CSV'
        }
        
        target_info = QLabel(
            f"<b>{self.get_str('importProjectName')}</b> {self.current_project.name}<br>"
            f"<b>{self.get_str('importOutputDir')}</b> {self.current_project.annotation_dir}<br>"
            f"<b>{self.get_str('importProjectFormat')}</b> {format_names_proj.get(self.current_project.format, self.current_project.format)}"
        )
        target_info.setWordWrap(True)
        target_layout.addWidget(target_info)
        
        # Labels preview with count
        if self.current_project.labels:
            labels_count = len(self.current_project.labels)
            labels_preview = ", ".join(self.current_project.labels[:10])
            if labels_count > 10:
                labels_preview += f"... (+{labels_count - 10} more)"
            
            labels_label = QLabel(f"<b>{self.get_str('importClassList')}</b> ({labels_count} classes):")
            labels_widget = QLabel(labels_preview)
            labels_widget.setWordWrap(True)
            # Use palette for automatic theme adaptation
            labels_widget.setStyleSheet(
                'background-color: palette(alternate-base); padding: 8px; border-radius: 4px; '
                'font-size: 11px; color: palette(text);'
            )
            target_layout.addWidget(labels_label)
            target_layout.addWidget(labels_widget)
        else:
            warning_labels = QLabel(
                "⚠️ <b>" + self.get_str('importNoLabelsWarning') + "</b><br>"
                + self.get_str('importNoLabelsHint')
            )
            warning_labels.setWordWrap(True)
            # Use palette colors for warning that adapt to theme
            warning_labels.setStyleSheet(
                'color: palette(dark); padding: 8px; '
                'background-color: palette(light); '
                'border-radius: 4px; border-left: 3px solid palette(dark);'
            )
            target_layout.addWidget(warning_labels)
        
        target_group.setLayout(target_layout)
        main_layout.addWidget(target_group)
        
        # YOLO detected labels info (if available)
        if yolo_labels:
            yolo_info_group = QGroupBox("📋 YOLO data.yaml Detected Classes")
            yolo_info_layout = QVBoxLayout()
            
            yolo_count = len(yolo_labels)
            yolo_preview = ", ".join(yolo_labels[:10])
            if yolo_count > 10:
                yolo_preview += f"... (+{yolo_count - 10} more)"
            
            yolo_info = QLabel(
                f"<b>Detected {yolo_count} classes from data.yaml:</b><br>"
                f"{yolo_preview}"
            )
            yolo_info.setWordWrap(True)
            yolo_info.setStyleSheet(
                'background-color: palette(alternate-base); padding: 10px; '
                'border-radius: 4px; color: palette(text);'
            )
            yolo_info_layout.addWidget(yolo_info)
            
            # Show different hints based on project labels
            if self.current_project.labels:
                # Project has labels, show mapping warning
                project_count = len(self.current_project.labels)
                hint_label = QLabel(
                    f"⚠️ <b>Note:</b> Your project has {project_count} defined labels. "
                    f"Imported annotations will be mapped to <b>project labels</b> by class ID. "
                    f"If the class order differs between source and project, labels may be incorrect."
                )
                hint_label.setWordWrap(True)
                hint_label.setStyleSheet(
                    'padding: 8px; color: palette(dark); font-size: 11px; '
                    'background-color: palette(light); border-radius: 4px; '
                    'border-left: 3px solid palette(dark);'
                )
                yolo_info_layout.addWidget(hint_label)
            else:
                # No project labels, suggest adding them
                hint_label = QLabel(
                    "💡 <b>Tip:</b> These labels will be used for conversion. "
                    "Consider adding them to your project for consistency."
                )
                hint_label.setWordWrap(True)
                hint_label.setStyleSheet(
                    'padding: 8px; color: palette(text); font-size: 11px;'
                )
                yolo_info_layout.addWidget(hint_label)
            
            yolo_info_group.setLayout(yolo_info_layout)
            main_layout.addWidget(yolo_info_group)
        
        # Options
        options_group = QGroupBox(self.get_str('importOptionsGroup'))
        options_layout = QVBoxLayout()
        
        copy_images_check = QCheckBox(self.get_str('importCopyImages'))
        copy_images_check.setChecked(True)
        options_layout.addWidget(copy_images_check)
        
        skip_existing_check = QCheckBox(self.get_str('importSkipExisting'))
        skip_existing_check.setChecked(True)
        options_layout.addWidget(skip_existing_check)
        
        options_group.setLayout(options_layout)
        main_layout.addWidget(options_group)
        
        # Warning message
        warning_items = [
            self.get_str('importWarningLine1'),
            self.get_str('importWarningLine2'),
            self.get_str('importWarningLine3'),
            self.get_str('importWarningLine4')
        ]
        warning_text = "\n".join([f"• {item}" for item in warning_items])
        
        warning_label = QLabel(
            f"<b>{self.get_str('importWarningTitle')}</b><br><br>"
            f"{warning_text}"
        )
        warning_label.setWordWrap(True)
        # Use palette colors that adapt to light/dark themes
        warning_label.setStyleSheet(
            'color: palette(dark); padding: 12px; '
            'background-color: palette(light); '
            'border-radius: 5px; border-left: 4px solid palette(dark);'
        )
        main_layout.addWidget(warning_label)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_import = QPushButton(self.get_str('importButtonStart'))
        button_cancel = QPushButton(self.get_str('importButtonCancel'))
        button_layout.addStretch()
        button_layout.addWidget(button_import)
        button_layout.addWidget(button_cancel)
        main_layout.addLayout(button_layout)
        
        confirm_dialog.setLayout(main_layout)
        
        # Connect buttons
        def on_import():
            confirm_dialog.accept()
            self._perform_import(
                source_dir,
                annotation_files,
                actual_format,  # Use actual_format for conversion
                copy_images_check.isChecked(),
                skip_existing_check.isChecked(),
                yolo_labels  # Pass YOLO labels from data.yaml
            )
        
        button_import.clicked.connect(on_import)
        button_cancel.clicked.connect(confirm_dialog.reject)
        
        # Store yolo_labels for use in import
        self._yolo_labels_for_import = yolo_labels
        
        # Show dialog
        if confirm_dialog.exec() != QDialog.Accepted:
            return False
        
        return True
    
    def _perform_import(self, source_dir, annotation_files, source_format, copy_images, skip_existing, yolo_labels=None):
        """
        Perform the actual import operation.
        
        Args:
            source_dir: Source directory
            annotation_files: List of annotation files
            source_format: Source format code
            copy_images: Whether to copy images
            skip_existing: Whether to skip existing files
            yolo_labels: Labels from data.yaml (for YOLO format)
        """
        from libs.annotation_converter import AnnotationConverter
        
        # Get target directories
        target_anno_dir = os.path.join(self.current_project.annotation_dir, 'annotations')
        target_img_dir = os.path.join(self.current_project.annotation_dir, 'images')
        os.makedirs(target_anno_dir, exist_ok=True)
        os.makedirs(target_img_dir, exist_ok=True)
        
        # Get current project format
        format_map = {
            'PASCAL_VOC': 'voc',
            'YOLO': 'yolo',
            'CREATE_ML': 'createml',
            'LABELCRAFT_JSON': 'json',
            'COCO': 'coco',
            'CSV': 'csv'
        }
        target_format = format_map.get(self.current_project.format, 'voc')
        
        # Get classes list - prioritize project labels over source labels
        # This ensures imported annotations match the project's label definitions
        labels_added_to_project = False
        
        if self.current_project.labels:
            # Project has defined labels, use them (most important)
            classes_list = self.current_project.labels
            print(f"Using {len(classes_list)} classes from project: {classes_list[:5]}...")
            
            # If YOLO has different labels, warn user about potential mismatch
            if yolo_labels and set(yolo_labels) != set(classes_list):
                print(f"Warning: YOLO data.yaml has different labels: {yolo_labels[:5]}...")
                print(f"Imported annotations will be mapped to project labels by class ID.")
                print(f"This may cause incorrect labels if the class order differs!")
        elif yolo_labels:
            # No project labels, use YOLO labels from data.yaml AND add them to project
            classes_list = yolo_labels
            print(f"Project has no labels. Using {len(classes_list)} classes from YOLO data.yaml: {classes_list[:5]}...")
            
            # Automatically add these labels to the project
            try:
                self.current_project.labels = classes_list.copy()
                self.current_project.save()  # Save project to persist labels
                labels_added_to_project = True
                print(f"✓ Added {len(classes_list)} labels to project automatically")
            except Exception as e:
                print(f"Warning: Failed to add labels to project: {e}")
        else:
            # No labels available at all
            classes_list = []
            print("Warning: No labels available. YOLO annotations will use numeric IDs.")
        
        imported_count = 0
        skipped_count = 0
        error_count = 0
        total = len(annotation_files)
        
        # Show progress
        progress_dialog = QProgressDialog(
            f'{self.get_str("importDialogTitle")}...',
            self.get_str('importButtonCancel'),
            0, total,
            self.parent
        )
        progress_dialog.setWindowModality(Qt.WindowModal)
        progress_dialog.setMinimumDuration(0)
        progress_dialog.setWindowTitle(self.get_str('importDialogTitle'))
        
        for idx, anno_file in enumerate(annotation_files):
            if progress_dialog.wasCanceled():
                break
            
            # Update progress with current file name
            current_file = os.path.basename(anno_file)
            progress_dialog.setLabelText(
                f'{self.get_str("importDialogTitle")}...\n'
                f'[{idx + 1}/{total}] {current_file}'
            )
            progress_dialog.setValue(idx)
            QApplication.processEvents()
            
            anno_filename = os.path.basename(anno_file)
            base_name = os.path.splitext(anno_filename)[0]
            
            try:
                # Check if already exists
                target_ext_map = {
                    'voc': '.xml',
                    'yolo': '.txt',
                    'createml': '.json',
                    'json': '.json',
                    'coco': '.json',
                    'csv': '.csv'
                }
                target_ext = target_ext_map.get(target_format, '.xml')
                target_anno_file = os.path.join(target_anno_dir, base_name + target_ext)
                
                if skip_existing and os.path.exists(target_anno_file):
                    print(f"Skipping existing: {anno_filename}")
                    skipped_count += 1
                    continue
                
                # Convert annotation if needed
                if source_format != target_format:
                    success = AnnotationConverter.convert(
                        input_path=anno_file,
                        input_format=source_format,
                        output_path=target_anno_file,
                        output_format=target_format,
                        classes_list=classes_list
                    )
                    
                    if not success:
                        print(f"Conversion failed for: {anno_filename}")
                        error_count += 1
                        continue
                else:
                    # Same format, just copy
                    shutil.copy2(anno_file, target_anno_file)
                
                # Find and copy corresponding image
                if copy_images:
                    self._copy_image(base_name, source_dir, anno_file, target_img_dir)
                
                imported_count += 1
                print(f"Imported: {anno_filename}")
                
            except Exception as e:
                print(f"Error importing {anno_filename}: {e}")
                import traceback
                traceback.print_exc()
                error_count += 1
        
        progress_dialog.close()
        
        # Show detailed result
        result_parts = [
            f"<b>{self.get_str('importCompleteTitle')}</b>",
            "",
            f"✅ <b>Successfully imported:</b> {imported_count} files",
        ]
        
        if skipped_count > 0:
            result_parts.append(f"⏭️ <b>Skipped (existing):</b> {skipped_count} files")
        
        if error_count > 0:
            result_parts.append(f"❌ <b>Errors:</b> {error_count} files")
        
        result_parts.extend([
            "",
            f"<b>Target directory:</b><br>{target_anno_dir}",
        ])
        
        result_msg = "<br>".join(result_parts)
        
        # Use different icon based on result
        if error_count == 0 and imported_count > 0:
            QMessageBox.information(self.parent, self.get_str('importCompleteTitle'), result_msg)
        elif imported_count > 0:
            QMessageBox.warning(self.parent, self.get_str('importCompleteTitle'), result_msg)
        else:
            QMessageBox.critical(self.parent, self.get_str('importCompleteTitle'), result_msg)
        
        # Refresh file list
        if hasattr(self.parent, 'refresh_annotation_list'):
            self.parent.refresh_annotation_list()
        
        print(f"Import completed: {imported_count} files imported to {target_anno_dir}")
    
    def _copy_image(self, base_name, source_dir, anno_file, target_img_dir):
        """
        Find and copy the corresponding image file.
        
        For YOLO format with directory structure, tries to find images based on
        the relative path of the annotation file.
        """
        img_found = False
        image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tif', '.tiff', '.gif', '.webp']
        
        # For YOLO format, try to preserve directory structure
        if anno_file.startswith(os.path.join(source_dir, 'labels')):
            # Extract relative path from labels/ directory
            rel_path = os.path.relpath(os.path.dirname(anno_file), 
                                      os.path.join(source_dir, 'labels'))
            
            # Try to find image in corresponding images/ subdirectory
            images_base = os.path.join(source_dir, 'images', rel_path)
            if os.path.exists(images_base):
                for ext in image_extensions:
                    img_path = os.path.join(images_base, base_name + ext)
                    if os.path.exists(img_path):
                        # Create subdirectory in target if needed
                        target_subdir = os.path.join(target_img_dir, rel_path)
                        os.makedirs(target_subdir, exist_ok=True)
                        shutil.copy2(img_path, os.path.join(target_subdir, os.path.basename(img_path)))
                        img_found = True
                        break
        
        # If not found yet, try standard locations
        if not img_found:
            search_dirs = [
                source_dir,
                os.path.join(source_dir, 'images'),
                os.path.dirname(source_dir),
                os.path.join(os.path.dirname(source_dir), 'images')
            ]
            
            for search_dir in search_dirs:
                if not os.path.exists(search_dir):
                    continue
                
                for ext in image_extensions:
                    img_path = os.path.join(search_dir, base_name + ext)
                    if os.path.exists(img_path):
                        shutil.copy2(img_path, os.path.join(target_img_dir, os.path.basename(img_path)))
                        img_found = True
                        break
                
                if img_found:
                    break
        
        if not img_found:
            print(f"Warning: Image not found for {base_name}")
