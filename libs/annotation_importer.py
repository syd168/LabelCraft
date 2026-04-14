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
        
        # Step 3: Scan for annotation files
        annotation_files = self._scan_annotation_files(source_dir, selected_format)
        if not annotation_files:
            QMessageBox.warning(
                self.parent,
                self.get_str('warningTitle'),
                self.get_str('importNoFilesFound').format(source_dir)
            )
            return False
        
        # Step 4: Confirm and perform import
        return self._confirm_and_import(source_dir, annotation_files, selected_format)
    
    def _select_format_dialog(self):
        """Show dialog to select source annotation format."""
        format_dialog = QDialog(self.parent)
        format_dialog.setWindowTitle(self.get_str('importDialogTitle'))
        format_dialog.setMinimumWidth(400)
        
        format_layout = QVBoxLayout()
        
        # Format selection
        format_group = QGroupBox(self.get_str('importSourceFormat'))
        format_group_layout = QVBoxLayout()
        
        format_combo = QComboBox()
        format_options = [
            ('voc', 'PASCAL VOC (XML)'),
            ('yolo', 'YOLO (TXT)'),
            ('coco', 'COCO (JSON)'),
            ('createml', 'CreateML (JSON)'),
            ('json', 'LabelCraft JSON'),
            ('csv', 'CSV')
        ]
        
        for value, text in format_options:
            format_combo.addItem(text, value)
        
        format_group_layout.addWidget(format_combo)
        format_group.setLayout(format_group_layout)
        format_layout.addWidget(format_group)
        
        # Info message
        info_label = QLabel(
            'ℹ️ ' + self.get_str('importInfoMessage')
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet('padding: 10px; border-radius: 5px;')
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
        
        ext_pattern = ext_map.get(selected_format, '*.*')
        
        # For YOLO format, search in labels/ subdirectory recursively
        if selected_format == 'yolo':
            labels_dir = os.path.join(source_dir, 'labels')
            if os.path.exists(labels_dir):
                # Recursively search in labels/ directory
                for root, dirs, files in os.walk(labels_dir):
                    for file in files:
                        if file.endswith('.txt'):
                            annotation_files.append(os.path.join(root, file))
            else:
                # No labels/ directory, search in current directory
                annotation_files = glob.glob(os.path.join(source_dir, ext_pattern))
        else:
            # For other formats, search in current directory
            annotation_files = glob.glob(os.path.join(source_dir, ext_pattern))
        
        # Filter out non-annotation JSON files for JSON formats
        if selected_format in ['coco', 'createml', 'json']:
            annotation_files = [f for f in annotation_files 
                              if not os.path.basename(f).startswith(('data', 'classes'))]
        
        return sorted(annotation_files)
    
    def _confirm_and_import(self, source_dir, annotation_files, selected_format):
        """Show confirmation dialog and perform import."""
        confirm_dialog = QDialog(self.parent)
        confirm_dialog.setWindowTitle(self.get_str('importConfirmTitle'))
        confirm_dialog.setMinimumWidth(600)
        
        main_layout = QVBoxLayout()
        
        # Source info
        info_group = QGroupBox(self.get_str('importSourceGroup'))
        info_layout = QVBoxLayout()
        info_layout.addWidget(QLabel(f"{self.get_str('importSourceDir')} {source_dir}"))
        info_layout.addWidget(QLabel(f"{self.get_str('importDetectedFiles')} {len(annotation_files)}"))
        
        format_names = {
            'voc': 'PASCAL VOC (XML)',
            'yolo': 'YOLO (TXT)',
            'coco': 'COCO (JSON)',
            'createml': 'CreateML (JSON)',
            'json': 'LabelCraft JSON',
            'csv': 'CSV'
        }
        info_layout.addWidget(QLabel(f"{self.get_str('importSelectedFormat')} {format_names.get(selected_format, selected_format)}"))
        info_group.setLayout(info_layout)
        main_layout.addWidget(info_group)
        
        # Target info
        target_group = QGroupBox(self.get_str('importTargetGroup'))
        target_layout = QVBoxLayout()
        target_layout.addWidget(QLabel(f"{self.get_str('importProjectName')} {self.current_project.name}"))
        target_layout.addWidget(QLabel(f"{self.get_str('importOutputDir')} {self.current_project.annotation_dir}"))
        format_names_proj = {
            'PASCAL_VOC': 'PASCAL VOC',
            'YOLO': 'YOLO',
            'CREATE_ML': 'CreateML',
            'LABELCRAFT_JSON': 'LabelCraft JSON',
            'COCO': 'COCO',
            'CSV': 'CSV'
        }
        target_layout.addWidget(QLabel(f"{self.get_str('importProjectFormat')} {format_names_proj.get(self.current_project.format, self.current_project.format)}"))
        labels_preview = ", ".join(self.current_project.labels[:10])
        if len(self.current_project.labels) > 10:
            labels_preview += "..."
        target_layout.addWidget(QLabel(f"{self.get_str('importClassList')} {labels_preview}"))
        target_group.setLayout(target_layout)
        main_layout.addWidget(target_group)
        
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
        warning_label = QLabel(
            self.get_str('importWarningTitle') + '\n'
            + self.get_str('importWarningLine1') + '\n'
            + self.get_str('importWarningLine2') + '\n'
            + self.get_str('importWarningLine3') + '\n'
            + self.get_str('importWarningLine4')
        )
        warning_label.setWordWrap(True)
        warning_label.setStyleSheet('color: #ff6600; padding: 10px; background-color: #fff3e0; border-radius: 5px;')
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
                selected_format,
                copy_images_check.isChecked(),
                skip_existing_check.isChecked()
            )
        
        button_import.clicked.connect(on_import)
        button_cancel.clicked.connect(confirm_dialog.reject)
        
        # Show dialog
        if confirm_dialog.exec() != QDialog.Accepted:
            return False
        
        return True
    
    def _perform_import(self, source_dir, annotation_files, source_format, copy_images, skip_existing):
        """Perform the actual import operation."""
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
        
        # Get classes list
        classes_list = self.current_project.labels if self.current_project.labels else []
        
        imported_count = 0
        skipped_count = 0
        error_count = 0
        total = len(annotation_files)
        
        # Show progress
        progress_dialog = QProgressDialog('正在导入标注...', '取消', 0, total, self.parent)
        progress_dialog.setWindowModality(Qt.WindowModal)
        progress_dialog.setMinimumDuration(0)
        
        for idx, anno_file in enumerate(annotation_files):
            if progress_dialog.wasCanceled():
                break
            
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
        
        # Show result
        result_msg = self.get_str('importCompleteMsg').format(
            imported_count,
            skipped_count,
            error_count,
            target_anno_dir
        )
        
        QMessageBox.information(self.parent, self.get_str('importCompleteTitle'), result_msg)
        
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
