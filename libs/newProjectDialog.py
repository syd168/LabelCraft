"""
New Project Dialog for LabelCraft
Guides users through creating a new annotation project
"""
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                                QLineEdit, QPushButton, QFileDialog, 
                                QListWidget, QListWidgetItem, QMessageBox,
                                QGroupBox, QRadioButton, QButtonGroup)
from PySide6.QtCore import Qt


class NewProjectDialog(QDialog):
    """Dialog for creating a new annotation project"""
    
    def __init__(self, parent=None, edit_mode=False):
        super(NewProjectDialog, self).__init__(parent)
        self.edit_mode = edit_mode
        self.parent_window = parent
        
        # Load string bundle for i18n
        self.string_bundle = None
        if parent and hasattr(parent, 'string_bundle'):
            self.string_bundle = parent.string_bundle
        
        get_str = lambda str_id: self.string_bundle.get_string(str_id) if self.string_bundle else str_id
        
        if edit_mode:
            self.setWindowTitle(get_str('editProjectDialogTitle'))
        else:
            self.setWindowTitle(get_str('newProjectDialogTitle'))
        self.setMinimumSize(600, 500)
        
        self.labels = []
        self.setup_ui()
        
    def setup_ui(self):
        get_str = lambda str_id: self.string_bundle.get_string(str_id) if self.string_bundle else str_id
        
        main_layout = QVBoxLayout()
        main_layout.setSpacing(15)
        
        # Project Name
        name_group = QGroupBox(get_str('projectInfoGroup'))
        name_layout = QVBoxLayout()
        
        name_input_layout = QHBoxLayout()
        name_label = QLabel(get_str('projectNameLabel'))
        name_label.setMinimumWidth(100)
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText(get_str('projectNamePlaceholder'))
        name_input_layout.addWidget(name_label)
        name_input_layout.addWidget(self.name_input)
        name_layout.addLayout(name_input_layout)
        
        # Project directory
        dir_input_layout = QHBoxLayout()
        dir_label = QLabel(get_str('projectDirLabel'))
        dir_label.setMinimumWidth(100)
        self.dir_input = QLineEdit()
        self.dir_input.setPlaceholderText(get_str('projectDirPlaceholder'))
        self.dir_input.setReadOnly(True)
        dir_browse_btn = QPushButton(get_str('browseButton'))
        dir_browse_btn.setMaximumWidth(40)
        dir_browse_btn.clicked.connect(self.browse_project_dir)
        dir_input_layout.addWidget(dir_label)
        dir_input_layout.addWidget(self.dir_input)
        dir_input_layout.addWidget(dir_browse_btn)
        name_layout.addLayout(dir_input_layout)
        
        name_group.setLayout(name_layout)
        main_layout.addWidget(name_group)
        
        # Labels
        label_group = QGroupBox(get_str('labelsGroup'))
        label_layout = QVBoxLayout()
        
        label_info = QLabel(get_str('labelInfoText'))
        label_info.setStyleSheet('font-size: 11px;')
        label_layout.addWidget(label_info)
        
        self.label_list = QListWidget()
        self.label_list.setMinimumHeight(100)
        label_layout.addWidget(self.label_list)
        
        label_btn_layout = QHBoxLayout()
        add_label_btn = QPushButton(get_str('addLabel'))
        add_label_btn.clicked.connect(self.add_label)
        remove_label_btn = QPushButton(get_str('removeLabel'))
        remove_label_btn.clicked.connect(self.remove_label)
        load_labels_btn = QPushButton(get_str('loadLabelsFromFile'))
        load_labels_btn.clicked.connect(self.load_labels_from_file)
        label_btn_layout.addWidget(add_label_btn)
        label_btn_layout.addWidget(remove_label_btn)
        label_btn_layout.addStretch()
        label_btn_layout.addWidget(load_labels_btn)
        label_layout.addLayout(label_btn_layout)
        
        label_group.setLayout(label_layout)
        main_layout.addWidget(label_group)
        
        # Format selection
        format_group = QGroupBox(get_str('formatGroup'))
        format_layout = QHBoxLayout()
        
        self.format_group = QButtonGroup()
        self.format_voc = QRadioButton('PASCAL VOC (XML)')
        self.format_yolo = QRadioButton('YOLO (TXT)')
        self.format_createml = QRadioButton('CreateML (JSON)')
        
        self.format_voc.setChecked(True)
        
        self.format_group.addButton(self.format_voc, 0)
        self.format_group.addButton(self.format_yolo, 1)
        self.format_group.addButton(self.format_createml, 2)
        
        format_layout.addWidget(self.format_voc)
        format_layout.addWidget(self.format_yolo)
        format_layout.addWidget(self.format_createml)
        format_layout.addStretch()
        
        format_group.setLayout(format_layout)
        main_layout.addWidget(format_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        cancel_btn = QPushButton(get_str('cancelButton'))
        if self.edit_mode:
            create_btn = QPushButton(get_str('saveProjectButton'))
        else:
            create_btn = QPushButton(get_str('createProjectButton'))
        create_btn.setStyleSheet('font-weight: bold;')
        cancel_btn.clicked.connect(self.reject)
        create_btn.clicked.connect(self.accept_project)
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(create_btn)
        
        main_layout.addLayout(button_layout)
        
        self.setLayout(main_layout)
    
    def browse_project_dir(self):
        """Browse for project directory"""
        get_str = lambda str_id: self.string_bundle.get_string(str_id) if self.string_bundle else str_id
        dir_path = QFileDialog.getExistingDirectory(
            self, get_str('selectProjectDirTitle'), '', 
            QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks
        )
        if dir_path:
            self.dir_input.setText(dir_path)
    
    def add_label(self):
        """Add a label from input dialog"""
        from PySide6.QtWidgets import QInputDialog
        get_str = lambda str_id: self.string_bundle.get_string(str_id) if self.string_bundle else str_id
        label, ok = QInputDialog.getText(self, get_str('addLabelDialogTitle'), get_str('addLabelPrompt'))
        if ok and label.strip():
            label = label.strip()
            if label not in self.labels:
                self.labels.append(label)
                self.label_list.addItem(label)
            else:
                QMessageBox.warning(self, get_str('warningTitle'), get_str('labelExistsWarning').format(label))
    
    def remove_label(self):
        """Remove selected label"""
        current_item = self.label_list.currentItem()
        if current_item:
            label = current_item.text()
            self.labels.remove(label)
            self.label_list.takeItem(self.label_list.row(current_item))
    
    def load_labels_from_file(self):
        """Load labels from text file"""
        get_str = lambda str_id: self.string_bundle.get_string(str_id) if self.string_bundle else str_id
        file_path, _ = QFileDialog.getOpenFileName(
            self, get_str('loadLabelsFileTitle'), '', 
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
            
            QMessageBox.information(self, get_str('successTitle'), get_str('labelsLoadedSuccessfully2').format(len(self.labels)))
        except Exception as e:
            QMessageBox.critical(self, get_str('errorTitle'), get_str('loadLabelsFailedMessage') + str(e))
    
    def accept_project(self):
        """Validate and accept the project"""
        get_str = lambda str_id: self.string_bundle.get_string(str_id) if self.string_bundle else str_id
        
        # Validate inputs
        if not self.name_input.text().strip():
            QMessageBox.warning(self, get_str('validationErrorTitle'), get_str('enterProjectNameWarning'))
            return
        
        if not self.dir_input.text():
            QMessageBox.warning(self, get_str('validationErrorTitle'), get_str('selectProjectDirWarning'))
            return
        
        if len(self.labels) == 0:
            reply = QMessageBox.question(
                self, get_str('noLabelsConfirmTitle'), 
                get_str('noLabelsWarning'),
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply == QMessageBox.No:
                return
        
        self.accept()
    
    def get_project_data(self):
        """Get the project configuration data"""
        format_map = {
            0: 'PASCAL_VOC',
            1: 'YOLO',
            2: 'CREATE_ML'
        }
        
        format_id = self.format_group.checkedId()
        
        return {
            'name': self.name_input.text().strip(),
            'project_dir': self.dir_input.text(),
            'labels': self.labels.copy(),
            'format': format_map.get(format_id, 'PASCAL_VOC')
        }
