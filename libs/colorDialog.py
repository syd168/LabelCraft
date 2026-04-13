from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import QColorDialog, QDialogButtonBox

BB = QDialogButtonBox


class ColorDialog(QColorDialog):

    def __init__(self, parent=None):
        super(ColorDialog, self).__init__(parent)
        self.setOption(QColorDialog.ShowAlphaChannel)
        # The Mac native dialog does not support our restore button.
        self.setOption(QColorDialog.DontUseNativeDialog)
        # Add a restore defaults button.
        # The default is set at invocation time, so that it
        # works across dialogs for different elements.
        self.default = None
        self.bb = self.layout().itemAt(1).widget()
        self.bb.addButton(BB.RestoreDefaults)
        self.bb.clicked.connect(self.check_restore)
        
        # Store parent reference for i18n
        self.parent_window = parent
        
        # Connect to language change signal if parent has i18n engine
        if parent and hasattr(parent, 'i18n'):
            parent.i18n.language_changed.connect(self.retranslate)
    
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
        # Qt's QColorDialog uses system translations, but we can update custom elements
        print(f"✓ ColorDialog retranslated")

    def getColor(self, value=None, title=None, default=None):
        self.default = default
        if title:
            # Use translated title if provided
            self.setWindowTitle(title)
        else:
            # Default title based on context
            self.setWindowTitle(self.get_str('colorDialogTitle'))
        if value:
            self.setCurrentColor(value)
        return self.currentColor() if self.exec() else None

    def check_restore(self, button):
        # In PySide6/Qt6, buttonRole returns an enum, need to use .value for bitwise operation
        role = self.bb.buttonRole(button)
        role_value = role.value if hasattr(role, 'value') else role
        reset_role_value = BB.ResetRole.value if hasattr(BB.ResetRole, 'value') else BB.ResetRole
        
        if role_value & reset_role_value and self.default:
            self.setCurrentColor(self.default)
