from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *


class ToolBar(QToolBar):

    def __init__(self, title):
        super(ToolBar, self).__init__(title)
        layout = self.layout()
        m = (0, 0, 0, 0)
        layout.setSpacing(0)
        layout.setContentsMargins(*m)
        self.setContentsMargins(*m)
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.FramelessWindowHint)
        # Compact icon-only toolbar by default
        self.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
        self.setIconSize(QSize(24, 24))

    def addAction(self, action):
        if isinstance(action, QWidgetAction):
            return super(ToolBar, self).addAction(action)
        btn = ToolButton()
        btn.setDefaultAction(action)
        btn.setToolButtonStyle(self.toolButtonStyle())
        btn.setAutoRaise(True)
        # Prefer detailed tip; fall back to action text
        tip = action.toolTip() or action.text()
        if tip:
            btn.setToolTip(tip)
            action.setToolTip(tip)
        self.addWidget(btn)


class ToolButton(QToolButton):
    """Compact square tool button for icon-only toolbars."""
    minSize = (32, 32)

    def __init__(self, parent=None):
        super(ToolButton, self).__init__(parent)
        self.setAutoRaise(True)
        self.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)

    def minimumSizeHint(self):
        ms = super(ToolButton, self).minimumSizeHint()
        w1, h1 = ms.width(), ms.height()
        w2, h2 = self.minSize
        # Cap growth so Chinese text labels don't force a huge rail
        ToolButton.minSize = min(max(w1, w2), 40), min(max(h1, h2), 40)
        return QSize(*ToolButton.minSize)
