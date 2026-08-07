from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *


class ZoomWidget(QSlider):

    def __init__(self, value=100, title='Zoom'):
        super(ZoomWidget, self).__init__(Qt.Orientation.Horizontal)
        # Use -100 to +100 range, where 0 = 100% (1:1)
        # Left side: -100 to 0 = 10% to 100% (shrink)
        # Right side: 0 to +100 = 100% to 1000% (enlarge)
        self.setRange(-100, 100)
        
        # Store title for tooltip updates
        self.title = title
        
        # Convert percentage to slider position
        slider_value = self.percentage_to_slider(value)
        self.setValue(slider_value)
        
        self.setToolTip(f'{title} (10%-1000%, center=100%)')
        self.setStatusTip(self.toolTip())
        
        # Add a label to show current value
        self.value_label = QLabel(f'{value}%')
        self.value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.value_label.setMinimumWidth(50)
        
        # Connect value change to update label
        self.valueChanged.connect(self._update_label)
    
    def percentage_to_slider(self, percentage):
        """Convert zoom percentage to slider position"""
        if percentage <= 100:
            # Shrink: 10%-100% maps to -100 to 0
            return int((percentage - 100) / 90 * 100)
        else:
            # Enlarge: 100%-1000% maps to 0 to 100
            return int((percentage - 100) / 900 * 100)
    
    def slider_to_percentage(self, slider_value):
        """Convert slider position to zoom percentage"""
        if slider_value <= 0:
            # Shrink: -100 to 0 maps to 10%-100%
            return int(100 + slider_value / 100 * 90)
        else:
            # Enlarge: 0 to 100 maps to 100%-1000%
            return int(100 + slider_value / 100 * 900)
    
    def _update_label(self, slider_value):
        """Update the value label when slider changes"""
        percentage = self.slider_to_percentage(slider_value)
        self.value_label.setText(f'{percentage}%')
    
    def get_zoom_percentage(self):
        """Get current zoom percentage"""
        return self.slider_to_percentage(self.value())
    
    def set_zoom_percentage(self, percentage):
        """Set zoom by percentage"""
        slider_value = self.percentage_to_slider(percentage)
        self.setValue(slider_value)
    
    def update_tooltip(self, title=None):
        """Update tooltip text (for language change)"""
        if title:
            self.title = title
        self.setToolTip(f'{self.title} (10%-1000%, center=100%)')
        self.setStatusTip(self.toolTip())
    
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
        return QSize(200, 20)
