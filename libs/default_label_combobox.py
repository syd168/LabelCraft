import sys
from PySide6.QtWidgets import QWidget, QHBoxLayout, QComboBox


class DefaultLabelComboBox(QWidget):
    def __init__(self, parent=None, items=[]):
        super(DefaultLabelComboBox, self).__init__(parent)

        layout = QHBoxLayout()
        self.cb = QComboBox()
        self.items = items
        self.cb.addItems(self.items)

        self.cb.currentIndexChanged.connect(parent.default_label_combo_selection_changed)

        layout.addWidget(self.cb)
        self.setLayout(layout)
    
    def update_items(self, items):
        """Update the combo box items"""
        self.items = items
        self.cb.clear()
        self.cb.addItems(self.items)
