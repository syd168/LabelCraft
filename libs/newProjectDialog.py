"""
New Project Dialog for LabelCraft
Guides users through creating a new annotation project
"""
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                                QLineEdit, QPushButton, QFileDialog,
                                QListWidget, QListWidgetItem, QMessageBox,
                                QGroupBox, QRadioButton, QButtonGroup,
                                QTextEdit, QInputDialog, QSpinBox, QWidget,
                                QScrollArea, QSizePolicy, QFrame, QFormLayout,
                                QToolButton)
from PySide6.QtCore import Qt


class I18nMixin:
    """Mixin class to provide i18n support for dialogs"""
    
    def tr(self, key: str, default: str = None, **kwargs):
        """
        Translate a string - standard i18n method name (Qt convention).
        Delegates to parent window's translation system.
        """
        if self.parent_window and hasattr(self.parent_window, 'tr'):
            return self.parent_window.tr(key, default=default, **kwargs)
        return default if default is not None else key
    
    # Alias for backward compatibility
    get_str = tr
    
    def retranslate(self):
        """Retranslate UI elements when language changes"""
        # This should be overridden by subclasses
        pass


class NewProjectDialog(QDialog, I18nMixin):
    """Dialog for creating a new annotation project"""
    
    def __init__(self, parent=None, edit_mode=False):
        super(NewProjectDialog, self).__init__(parent)
        self.edit_mode = edit_mode
        self.parent_window = parent
        
        # Connect to language change signal if parent has i18n engine
        if parent and hasattr(parent, 'i18n'):
            parent.i18n.language_changed.connect(self.retranslate)
        
        # Set initial title
        self.setWindowTitle(self.get_str('editProjectDialogTitle' if edit_mode else 'newProjectDialogTitle'))
        self.setMinimumSize(720, 520)
        self.resize(780, 580)
        # Remember last user size so task toggles don't fight the user
        self._dialog_base_height = 580
        self._dialog_pose_height = 680
        
        self.labels = []
        self.setup_ui()

    def _tip_label(self, short_text, tip_text):
        """Short field label; full explanation on hover."""
        label = QLabel(short_text)
        label.setToolTip(tip_text)
        return label

    def _help_button(self, tip_text):
        """Small (?) control that only shows detail on hover."""
        btn = QToolButton()
        btn.setText('?')
        btn.setToolTip(tip_text)
        btn.setAutoRaise(True)
        btn.setFixedSize(20, 20)
        btn.setStyleSheet(
            'QToolButton { color: palette(mid); font-weight: bold; border: none; }'
            'QToolButton:hover { color: palette(highlight); }'
        )
        return btn
        
    def setup_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(12, 12, 12, 12)
        outer.setSpacing(10)

        # Scrollable body so pose options / format / buttons don't pile up
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        content = QWidget()
        main_layout = QVBoxLayout(content)
        main_layout.setContentsMargins(4, 4, 12, 4)
        main_layout.setSpacing(12)
        
        # Project Name
        name_group = QGroupBox(self.get_str('projectInfoGroup'))
        name_layout = QVBoxLayout()
        name_layout.setSpacing(8)
        
        name_input_layout = QHBoxLayout()
        name_label = QLabel(self.get_str('projectNameLabel'))
        name_label.setMinimumWidth(88)
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText(self.get_str('projectNamePlaceholder'))
        name_input_layout.addWidget(name_label)
        name_input_layout.addWidget(self.name_input)
        name_layout.addLayout(name_input_layout)
        
        # Project directory
        dir_input_layout = QHBoxLayout()
        dir_label = QLabel(self.get_str('projectDirLabel'))
        dir_label.setMinimumWidth(88)
        self.dir_input = QLineEdit()
        self.dir_input.setPlaceholderText(self.get_str('projectDirPlaceholder'))
        self.dir_input.setReadOnly(True)
        dir_browse_btn = QPushButton(self.get_str('browseButton'))
        dir_browse_btn.setMaximumWidth(40)
        dir_browse_btn.clicked.connect(self.browse_project_dir)
        dir_input_layout.addWidget(dir_label)
        dir_input_layout.addWidget(self.dir_input)
        dir_input_layout.addWidget(dir_browse_btn)
        name_layout.addLayout(dir_input_layout)
        
        name_group.setLayout(name_layout)
        main_layout.addWidget(name_group)
        
        # Labels: left = input, right = list
        label_group = QGroupBox(self.get_str('labelsGroup'))
        label_group.setToolTip(self.get_str('labelSectionTip'))
        label_layout = QVBoxLayout()
        label_layout.setSpacing(8)

        title_row = QHBoxLayout()
        title_row.addStretch()
        title_row.addWidget(self._help_button(self.get_str('labelSectionTip')))
        label_layout.addLayout(title_row)

        columns = QHBoxLayout()
        columns.setSpacing(12)

        # Left: enter labels
        left_col = QVBoxLayout()
        left_col.setSpacing(6)
        left_title = QLabel(self.get_str('labelInputTitle'))
        left_title.setStyleSheet('font-weight: bold;')
        left_title.setToolTip(self.get_str('labelInputHint'))
        left_col.addWidget(left_title)
        self.label_input = QTextEdit()
        self.label_input.setPlaceholderText(self.get_str('labelInputPlaceholder'))
        self.label_input.setToolTip(self.get_str('labelInputHint'))
        self.label_input.setMinimumHeight(120)
        self.label_input.installEventFilter(self)
        left_col.addWidget(self.label_input, 1)
        left_btns = QHBoxLayout()
        batch_add_btn = QPushButton(self.get_str('batchAddLabels'))
        batch_add_btn.setToolTip(self.get_str('labelInputHint'))
        batch_add_btn.clicked.connect(self.parse_and_add_labels)
        add_label_btn = QPushButton(self.get_str('addLabel'))
        add_label_btn.clicked.connect(self.add_label)
        left_btns.addWidget(batch_add_btn)
        left_btns.addWidget(add_label_btn)
        left_btns.addStretch()
        left_col.addLayout(left_btns)
        columns.addLayout(left_col, 1)

        # Right: added labels list
        right_col = QVBoxLayout()
        right_col.setSpacing(6)
        right_title = QLabel(self.get_str('labelListTitle'))
        right_title.setStyleSheet('font-weight: bold;')
        right_col.addWidget(right_title)
        self.label_list = QListWidget()
        self.label_list.setMinimumHeight(120)
        right_col.addWidget(self.label_list, 1)
        right_btns = QHBoxLayout()
        remove_label_btn = QPushButton(self.get_str('removeLabel'))
        remove_label_btn.clicked.connect(self.remove_label)
        clear_labels_btn = QPushButton(self.get_str('clearLabels'))
        clear_labels_btn.clicked.connect(self.clear_labels)
        load_labels_btn = QPushButton(self.get_str('loadLabelsFromFile'))
        load_labels_btn.clicked.connect(self.load_labels_from_file)
        right_btns.addWidget(remove_label_btn)
        right_btns.addWidget(clear_labels_btn)
        right_btns.addStretch()
        right_btns.addWidget(load_labels_btn)
        right_col.addLayout(right_btns)
        columns.addLayout(right_col, 1)

        label_layout.addLayout(columns)
        label_group.setLayout(label_layout)
        main_layout.addWidget(label_group)

        # Task selection: detect vs pose
        task_group = QGroupBox(self.get_str('annotationTaskGroup'))
        task_layout = QVBoxLayout()
        task_layout.setSpacing(8)

        task_row = QHBoxLayout()
        self.task_button_group = QButtonGroup()
        self.task_detect = QRadioButton(self.get_str('taskDetect'))
        self.task_pose = QRadioButton(self.get_str('taskPose'))
        self.task_detect.setToolTip(self.get_str('taskDetectTip'))
        self.task_pose.setToolTip(self.get_str('taskPoseTip'))
        self.task_detect.setChecked(True)
        self.task_button_group.addButton(self.task_detect, 0)
        self.task_button_group.addButton(self.task_pose, 1)
        task_row.addWidget(self.task_detect)
        task_row.addWidget(self.task_pose)
        task_row.addStretch()
        task_row.addWidget(self._help_button(self.get_str('poseProjectTip')))
        task_layout.addLayout(task_row)

        # Pose fields: short label | input  (details via tooltip)
        self.pose_config_widget = QWidget()
        pose_form = QFormLayout(self.pose_config_widget)
        pose_form.setContentsMargins(4, 6, 4, 2)
        pose_form.setHorizontalSpacing(12)
        pose_form.setVerticalSpacing(8)
        pose_form.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        pose_form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)

        self.kpt_count_spin = QSpinBox()
        self.kpt_count_spin.setRange(1, 64)
        self.kpt_count_spin.setValue(3)
        self.kpt_count_spin.setMinimumWidth(80)
        self.kpt_count_spin.setToolTip(self.get_str('keypointCountTip'))
        self.kpt_count_label = self._tip_label(
            self.get_str('keypointCountLabelShort'), self.get_str('keypointCountTip'))
        pose_form.addRow(self.kpt_count_label, self.kpt_count_spin)

        self.kpt_names_input = QLineEdit()
        self.kpt_names_input.setPlaceholderText(self.get_str('kptNamesPlaceholder'))
        self.kpt_names_input.setText(self.get_str('kptNamesPlaceholder'))
        self.kpt_names_input.setToolTip(self.get_str('keypointNamesTip'))
        self.kpt_names_label = self._tip_label(
            self.get_str('keypointNamesLabelShort'), self.get_str('keypointNamesTip'))
        pose_form.addRow(self.kpt_names_label, self.kpt_names_input)

        self.flip_idx_input = QLineEdit()
        self.flip_idx_input.setPlaceholderText(self.get_str('flipIdxPlaceholder'))
        self.flip_idx_input.setText(self.get_str('flipIdxPlaceholder'))
        self.flip_idx_input.setToolTip(self.get_str('flipIdxTip'))
        self.flip_idx_label = self._tip_label(
            self.get_str('flipIdxLabelShort'), self.get_str('flipIdxTip'))
        pose_form.addRow(self.flip_idx_label, self.flip_idx_input)

        self.skeleton_input = QLineEdit()
        self.skeleton_input.setPlaceholderText(self.get_str('skeletonPlaceholder'))
        self.skeleton_input.setText(self.get_str('skeletonPlaceholder'))
        self.skeleton_input.setToolTip(self.get_str('skeletonTip'))
        self.skeleton_label = self._tip_label(
            self.get_str('skeletonLabelShort'), self.get_str('skeletonTip'))
        pose_form.addRow(self.skeleton_label, self.skeleton_input)

        self.pose_config_widget.setVisible(False)
        task_layout.addWidget(self.pose_config_widget)
        task_group.setLayout(task_layout)
        main_layout.addWidget(task_group)

        self.task_detect.toggled.connect(self._on_task_changed)
        self.task_pose.toggled.connect(self._on_task_changed)
        self.kpt_count_spin.valueChanged.connect(self._sync_default_kpt_names)
        
        # Format selection - only internal storage formats
        format_group = QGroupBox(self.get_str('formatGroup'))
        format_layout = QHBoxLayout()
        format_layout.setSpacing(16)
        
        self.format_group = QButtonGroup()
        self.format_voc = QRadioButton(self.get_str('formatPascalVoc'))
        self.format_json = QRadioButton(self.get_str('formatLabelCraftJson'))
        
        self.format_voc.setChecked(True)
        
        self.format_group.addButton(self.format_voc, 0)
        self.format_group.addButton(self.format_json, 1)
        
        format_layout.addWidget(self.format_voc)
        format_layout.addWidget(self.format_json)
        format_layout.addStretch()
        
        format_group.setLayout(format_layout)
        main_layout.addWidget(format_group)

        main_layout.addStretch(1)
        scroll.setWidget(content)
        outer.addWidget(scroll, 1)
        
        # Buttons stay pinned at bottom (outside scroll)
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 4, 0, 0)
        button_layout.addStretch()
        cancel_btn = QPushButton(self.get_str('cancelButton'))
        if self.edit_mode:
            create_btn = QPushButton(self.get_str('saveProjectButton'))
        else:
            create_btn = QPushButton(self.get_str('createProjectButton'))
        create_btn.setStyleSheet('font-weight: bold;')
        create_btn.setMinimumWidth(110)
        cancel_btn.setMinimumWidth(90)
        cancel_btn.clicked.connect(self.reject)
        create_btn.clicked.connect(self.accept_project)
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(create_btn)
        
        outer.addLayout(button_layout)
    
    def browse_project_dir(self):
        """Browse for project directory"""
        dir_path = QFileDialog.getExistingDirectory(
            self, self.get_str('selectProjectDirTitle'), '', 
            QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks
        )
        if dir_path:
            self.dir_input.setText(dir_path)
    
    def eventFilter(self, obj, event):
        """Event filter to catch Enter key in label input"""
        from PySide6.QtCore import QEvent
        if obj == self.label_input and event.type() == QEvent.KeyPress:
            from PySide6.QtGui import QKeyEvent
            from PySide6.QtCore import Qt
            key_event = QKeyEvent(event)
            # Check for Enter or Return key (without Shift/Ctrl/Alt)
            if key_event.key() in (Qt.Key_Return, Qt.Key_Enter):
                if not key_event.modifiers() & (Qt.ShiftModifier | Qt.ControlModifier | Qt.AltModifier):
                    self.parse_and_add_labels()
                    return True  # Event handled
        return super().eventFilter(obj, event)
    
    def parse_and_add_labels(self):
        """Parse labels from text input and add them to the list"""
        text = self.label_input.toPlainText().strip()
        if not text:
            return
        
        # Split by newlines, commas, or spaces
        import re
        labels = re.split(r'[\n,，\s]+', text)
        labels = [label.strip() for label in labels if label.strip()]
        
        # Add new labels that don't exist yet
        added_count = 0
        duplicate_count = 0
        for label in labels:
            if label not in self.labels:
                self.labels.append(label)
                self.label_list.addItem(label)
                added_count += 1
            else:
                duplicate_count += 1
        
        # Clear input after adding
        if added_count > 0:
            self.label_input.clear()
            # Show feedback
            if duplicate_count > 0:
                print(f"Added {added_count} labels, skipped {duplicate_count} duplicates")
    
    def add_label(self):
        """Add a label from input dialog"""
        label, ok = QInputDialog.getText(self, self.get_str('addLabelDialogTitle'), self.get_str('addLabelPrompt'))
        if ok and label.strip():
            label = label.strip()
            if label not in self.labels:
                self.labels.append(label)
                self.label_list.addItem(label)
            else:
                QMessageBox.warning(self, self.get_str('warningTitle'), self.get_str('labelExistsWarning').format(label))
    
    def clear_labels(self):
        """Clear all labels"""
        reply = QMessageBox.question(
            self, self.get_str('clearLabelsConfirmTitle'),
            self.get_str('clearLabelsConfirmMsg'),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.labels.clear()
            self.label_list.clear()
    
    def remove_label(self):
        """Remove selected label"""
        current_item = self.label_list.currentItem()
        if current_item:
            label = current_item.text()
            self.labels.remove(label)
            self.label_list.takeItem(self.label_list.row(current_item))
    
    def load_labels_from_file(self):
        """Load labels from text file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, self.get_str('loadLabelsFileTitle'), '', 
            'Text Files (*.txt);;All Files (*)'
        )
        
        if not file_path:
            return
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    label = line.strip()
                    if label and label not in self.labels:
                        self.labels.append(label)
                        self.label_list.addItem(label)
            
            QMessageBox.information(self, self.get_str('successTitle'), self.get_str('labelsLoadedSuccessfully2').format(len(self.labels)))
        except Exception as e:
            QMessageBox.critical(self, self.get_str('errorTitle'), self.get_str('loadLabelsFailedMessage') + str(e))
    
    def _on_task_changed(self, checked=True):
        # Radio toggles fire twice (uncheck + check); only handle the checked side
        sender = self.sender()
        if sender is not None and not checked:
            return

        is_pose = self.task_pose.isChecked()
        self.pose_config_widget.setVisible(is_pose)
        if is_pose:
            # Pose editing is best stored in LabelCraft JSON
            self.format_json.setChecked(True)
        self._fit_dialog_for_task(is_pose)

    def _fit_dialog_for_task(self, is_pose):
        """Only grow when pose fields appear; never auto-shrink (scroll handles overflow)."""
        self.pose_config_widget.updateGeometry()
        if not is_pose:
            return

        cur_w = max(self.width(), 780)
        cur_h = self.height()
        target_h = max(cur_h, self._dialog_pose_height)
        if target_h == cur_h and cur_w == self.width():
            return

        screen = self.screen()
        if screen is not None:
            avail = screen.availableGeometry()
            target_h = min(target_h, max(self.minimumHeight(), int(avail.height() * 0.9)))
            cur_w = min(cur_w, max(self.minimumWidth(), int(avail.width() * 0.95)))

        self.resize(cur_w, target_h)

    def _sync_default_kpt_names(self, count):
        names = [n.strip() for n in self.kpt_names_input.text().split(',') if n.strip()]
        if len(names) == count:
            return
        # Auto-fill generic names when count changes and names don't match
        if not names or names == ['left', 'mid', 'right'] or all(n.startswith('kpt') for n in names):
            if count == 3:
                self.kpt_names_input.setText('left, mid, right')
                self.flip_idx_input.setText('2, 1, 0')
                self.skeleton_input.setText('0-1,1-2')
            else:
                self.kpt_names_input.setText(', '.join(f'kpt{i}' for i in range(count)))
                self.flip_idx_input.setText(', '.join(str(i) for i in range(count)))
                edges = [f'{i}-{i+1}' for i in range(count - 1)]
                self.skeleton_input.setText(','.join(edges))

    def _parse_pose_config(self):
        names = [n.strip() for n in self.kpt_names_input.text().split(',') if n.strip()]
        count = self.kpt_count_spin.value()
        if len(names) != count:
            # Pad or trim
            while len(names) < count:
                names.append(f'kpt{len(names)}')
            names = names[:count]

        flip_parts = [p.strip() for p in self.flip_idx_input.text().split(',') if p.strip()]
        try:
            flip_idx = [int(x) for x in flip_parts] if flip_parts else list(range(count))
        except ValueError:
            flip_idx = list(range(count))
        if len(flip_idx) != count:
            flip_idx = list(range(count))

        skeleton = []
        raw = self.skeleton_input.text().strip()
        if raw:
            for edge in raw.replace(';', ',').split(','):
                edge = edge.strip()
                if not edge:
                    continue
                if '-' in edge:
                    a, b = edge.split('-', 1)
                elif ' ' in edge:
                    a, b = edge.split(None, 1)
                else:
                    continue
                try:
                    skeleton.append([int(a), int(b)])
                except ValueError:
                    continue

        return {
            'kpt_shape': [count, 3],
            'keypoint_names': names,
            'flip_idx': flip_idx,
            'skeleton': skeleton,
        }

    def accept_project(self):
        """Validate and accept the project"""
        # Validate inputs
        if not self.name_input.text().strip():
            QMessageBox.warning(self, self.get_str('validationErrorTitle'), self.get_str('enterProjectNameWarning'))
            return
        
        if not self.dir_input.text():
            QMessageBox.warning(self, self.get_str('validationErrorTitle'), self.get_str('selectProjectDirWarning'))
            return
        
        if len(self.labels) == 0:
            reply = QMessageBox.question(
                self, self.get_str('noLabelsConfirmTitle'), 
                self.get_str('noLabelsWarning'),
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply == QMessageBox.No:
                return

        if self.task_pose.isChecked():
            cfg = self._parse_pose_config()
            if cfg['kpt_shape'][0] < 1:
                QMessageBox.warning(self, self.get_str('validationErrorTitle'),
                                    self.get_str('poseNeedsKeypoints'))
                return
        
        self.accept()
    
    def get_project_data(self):
        """Get the project configuration data"""
        format_map = {
            0: 'PASCAL_VOC',
            1: 'LABELCRAFT_JSON'
        }
        
        format_id = self.format_group.checkedId()
        task = 'pose' if self.task_pose.isChecked() else 'detect'
        data = {
            'name': self.name_input.text().strip(),
            'project_dir': self.dir_input.text(),
            'labels': self.labels.copy(),
            'format': format_map.get(format_id, 'PASCAL_VOC'),
            'task': task,
        }
        if task == 'pose':
            data.update(self._parse_pose_config())
            # Prefer JSON storage for pose fidelity
            if data['format'] != 'LABELCRAFT_JSON':
                data['format'] = 'LABELCRAFT_JSON'
        else:
            data.update({
                'kpt_shape': [0, 3],
                'keypoint_names': [],
                'flip_idx': [],
                'skeleton': [],
            })
        return data

    def apply_pose_fields(self, project):
        """Pre-fill pose fields when editing an existing project."""
        if getattr(project, 'task', 'detect') == 'pose':
            self.task_pose.setChecked(True)
            k = int((project.kpt_shape or [3, 3])[0] or 3)
            self.kpt_count_spin.setValue(k)
            if project.keypoint_names:
                self.kpt_names_input.setText(', '.join(project.keypoint_names))
            if project.flip_idx is not None:
                self.flip_idx_input.setText(', '.join(str(i) for i in project.flip_idx))
            if project.skeleton:
                self.skeleton_input.setText(','.join(f'{a}-{b}' for a, b in project.skeleton))
        else:
            self.task_detect.setChecked(True)
        self._on_task_changed()
    
    def retranslate(self):
        """Retranslate all UI elements when language changes"""
        # Update window title
        self.setWindowTitle(self.get_str('editProjectDialogTitle' if self.edit_mode else 'newProjectDialogTitle'))
        
        # Note: Other widgets were created with get_str() which will automatically use new language
        # when called again. For dynamic updates, we would need to store references to all widgets.
        # For now, the title update demonstrates the mechanism.
