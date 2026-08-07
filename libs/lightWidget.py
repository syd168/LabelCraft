from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *


class LightWidget(QSlider):

    def __init__(self, title, value=50):
        super(LightWidget, self).__init__(Qt.Orientation.Horizontal)
        # Use -50 to +50 range, where 0 = 50% (original brightness)
        # Left side: -50 to 0 = 0% to 50% (darker)
        # Right side: 0 to +50 = 50% to 100% (brighter)
        self.setRange(-50, 50)
        
        # Store title for tooltip updates
        self.title = title
        
        # Convert percentage to slider position
        slider_value = self.percentage_to_slider(value)
        self.setValue(slider_value)
        
        self.setToolTip(f'{title} (0-100%, center=50% original)')
        self.setStatusTip(self.toolTip())
        
        # Add a label to show current value
        self.value_label = QLabel(f'{value}%')
        self.value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.value_label.setMinimumWidth(40)
        
        # Connect value change to update label
        self.valueChanged.connect(self._update_label)
    
    def percentage_to_slider(self, percentage):
        """Convert brightness percentage to slider position"""
        # 0%-100% maps to -50 to +50
        return int((percentage - 50))
    
    def slider_to_percentage(self, slider_value):
        """Convert slider position to brightness percentage"""
        # -50 to +50 maps to 0%-100%
        return int(50 + slider_value)
    
    def _update_label(self, slider_value):
        """Update the value label when slider changes"""
        percentage = self.slider_to_percentage(slider_value)
        self.value_label.setText(f'{percentage}%')
    
    def create_widget_with_label(self):
        """Create a container widget with slider and value label"""
        container = QWidget()
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        layout.addWidget(self)
        layout.addWidget(self.value_label)
        container.setLayout(layout)
        return container

    def create_compact_vertical_widget(self):
        """Narrow vertical slider for icon-only side toolbar."""
        self.setOrientation(Qt.Orientation.Vertical)
        self.setFixedHeight(72)
        self.setFixedWidth(22)
        self.value_label.setMinimumWidth(0)
        self.value_label.setFixedWidth(36)
        self.value_label.setStyleSheet('font-size: 10px;')
        container = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(1)
        layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(self, 0, Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(self.value_label, 0, Qt.AlignmentFlag.AlignHCenter)
        container.setLayout(layout)
        container.setFixedWidth(40)
        container.setToolTip(self.toolTip())
        return container

    def minimumSizeHint(self):
        if self.orientation() == Qt.Orientation.Vertical:
            return QSize(22, 72)
        return QSize(150, 20)

    def get_light_percentage(self):
        """Get current brightness percentage"""
        return self.slider_to_percentage(self.value())
    
    def set_light_percentage(self, percentage):
        """Set brightness by percentage"""
        slider_value = self.percentage_to_slider(percentage)
        self.setValue(slider_value)
    
    def update_tooltip(self, title=None):
        """Update tooltip text (for language change)"""
        if title:
            self.title = title
        self.setToolTip(f'{self.title} (0-100%, center=50% original)')
        self.setStatusTip(self.toolTip())

    def color(self):
        percentage = self.get_light_percentage()
        if percentage == 50:
            return None

        strength = int(percentage / 100 * 255 + 0.5)
        return QColor(strength, strength, strength)
