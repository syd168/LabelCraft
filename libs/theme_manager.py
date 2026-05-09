#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
LabelCraft Theme Manager
Provides automatic system theme detection and application.
Supports light/dark mode following system settings on:
- Linux (GNOME, KDE, Ubuntu)
- Windows (Windows 10, Windows 11)
- macOS
"""
from PySide6.QtGui import QPalette, QColor
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
import platform
import os


def _create_dark_palette():
    """
    Create a comprehensive dark theme palette.
    
    Returns:
        QPalette: Configured dark palette
    """
    dark_palette = QPalette()
    
    # Base colors for dark theme
    dark_bg = QColor(53, 53, 53)
    darker_bg = QColor(25, 25, 25)
    light_text = QColor(255, 255, 255)
    link_color = QColor(42, 130, 218)
    
    # Window and base colors
    dark_palette.setColor(QPalette.ColorRole.Window, dark_bg)
    dark_palette.setColor(QPalette.ColorRole.Base, darker_bg)
    dark_palette.setColor(QPalette.ColorRole.AlternateBase, dark_bg)
    
    # Text colors
    dark_palette.setColor(QPalette.ColorRole.WindowText, light_text)
    dark_palette.setColor(QPalette.ColorRole.Text, light_text)
    dark_palette.setColor(QPalette.ColorRole.ButtonText, light_text)
    
    # Button and control colors
    dark_palette.setColor(QPalette.ColorRole.Button, dark_bg)
    dark_palette.setColor(QPalette.ColorRole.Shadow, QColor(20, 20, 20))
    dark_palette.setColor(QPalette.ColorRole.Highlight, link_color)
    dark_palette.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))
    
    # Link colors
    dark_palette.setColor(QPalette.ColorRole.Link, link_color)
    
    # Tooltips
    dark_palette.setColor(QPalette.ColorRole.ToolTipBase, light_text)
    dark_palette.setColor(QPalette.ColorRole.ToolTipText, dark_bg)
    
    # Placeholder text (input hint text)
    dark_palette.setColor(QPalette.ColorRole.PlaceholderText, QColor(150, 150, 150))
    
    # Disabled state
    dark_palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.WindowText, QColor(128, 128, 128))
    dark_palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, QColor(128, 128, 128))
    dark_palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, QColor(128, 128, 128))
    dark_palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.PlaceholderText, QColor(80, 80, 80))
    
    return dark_palette


def _create_light_palette():
    """
    Create a comprehensive light theme palette.
    
    Returns:
        QPalette: Configured light palette
    """
    light_palette = QPalette()
    
    # Use system default light colors
    # Light palette is typically the default, so we return a new instance
    return light_palette


def _detect_windows_dark_mode():
    """
    Detect if Windows 11/10 is using dark mode.
    
    Checks the Windows Registry:
    HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Themes\Personalize
    AppsUseLightTheme = 0 means dark mode
    
    Returns:
        bool: True if dark mode detected, False otherwise
    """
    try:
        import winreg
        try:
            # Try to open the registry key
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r'Software\Microsoft\Windows\CurrentVersion\Themes\Personalize'
            )
            # Read AppsUseLightTheme value
            # 0 = dark mode, 1 = light mode
            value, regtype = winreg.QueryValueEx(key, 'AppsUseLightTheme')
            winreg.CloseKey(key)
            return value == 0
        except Exception:
            # Key or value not found - assume light mode
            return False
    except ImportError:
        # winreg not available (not on Windows)
        return False
    except Exception:
        # Any other error - assume light mode
        return False


def _detect_linux_dark_mode():
    """
    Detect if Linux desktop environment is using dark mode.
    
    Supports:
    - GNOME/Ubuntu (via dconf)
    - KDE Plasma (via kdeglobals)
    
    Returns:
        bool: True if dark mode detected, False otherwise
    """
    # Method 1: Check GNOME/Ubuntu GTK theme via dconf
    try:
        import subprocess
        result = subprocess.run(
            ['dconf', 'read', '/org/gnome/desktop/interface/gtk-theme'],
            capture_output=True,
            text=True,
            timeout=2
        )
        if result.returncode == 0:
            theme_name = result.stdout.strip().strip("'\"")
            if 'dark' in theme_name.lower():
                return True
    except (FileNotFoundError, subprocess.TimeoutExpired, Exception):
        pass
    
    # Method 2: Check GNOME settings (alternative method)
    try:
        import subprocess
        result = subprocess.run(
            ['gsettings', 'get', 'org.gnome.desktop.interface', 'gtk-application-prefer-dark-theme'],
            capture_output=True,
            text=True,
            timeout=2
        )
        if result.returncode == 0:
            return 'true' in result.stdout.lower()
    except (FileNotFoundError, subprocess.TimeoutExpired, Exception):
        pass
    
    # Method 3: Check environment variables
    if os.environ.get('GTK_THEME', '').lower().endswith('-dark') or 'dark' in os.environ.get('GTK_THEME', '').lower():
        return True
    
    if 'dark' in os.environ.get('QT_STYLE_OVERRIDE', '').lower():
        return True
    
    # Method 4: Check Plasma/KDE settings
    try:
        config_path = os.path.expanduser('~/.config/kdeglobals')
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                content = f.read()
                if '[General]' in content and 'ColorScheme=' in content:
                    for line in content.split('\n'):
                        if 'ColorScheme=' in line and 'dark' in line.lower():
                            return True
    except Exception:
        pass
    
    return False


def _detect_macos_dark_mode():
    """
    Detect if macOS is using dark mode.
    
    Uses `defaults read` to check the system appearance setting.
    
    Returns:
        bool: True if dark mode detected, False otherwise
    """
    try:
        import subprocess
        result = subprocess.run(
            ['defaults', 'read', '-g', 'AppleInterfaceStyle'],
            capture_output=True,
            text=True,
            timeout=2
        )
        # If the command returns 'Dark', dark mode is enabled
        return 'Dark' in result.stdout or result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired, Exception):
        # If the command fails, assume light mode (default on macOS)
        return False


def _detect_system_dark_mode():
    """
    Detect if the system is using dark mode.
    
    Tries multiple methods based on the operating system:
    - Windows: Registry check (AppsUseLightTheme)
    - Linux: dconf, gsettings, or environment variables
    - macOS: defaults read
    
    Returns:
        bool: True if dark mode detected, False otherwise
    """
    system = platform.system()
    
    if system == 'Windows':
        return _detect_windows_dark_mode()
    elif system == 'Linux':
        return _detect_linux_dark_mode()
    elif system == 'Darwin':  # macOS
        return _detect_macos_dark_mode()
    else:
        # Unknown system - assume light mode
        return False


def apply_system_theme(app):
    """
    Apply system theme (light/dark mode) to the application.
    
    This function detects the system's current theme preference
    and applies it to the QApplication. The application will
    automatically use the correct colors and styles based on
    the system's light/dark mode setting.
    
    Args:
        app (QApplication): The Qt application instance
    """
    # Use Fusion style for better cross-platform theme support
    app.setStyle('Fusion')
    
    # Detect if system is in dark mode
    is_dark = _detect_system_dark_mode()
    
    # Apply the appropriate palette
    if is_dark:
        dark_palette = _create_dark_palette()
        app.setPalette(dark_palette)
    else:
        # Light mode uses default palette
        light_palette = _create_light_palette()
        app.setPalette(light_palette)
    
    # Return theme info
    return {
        'is_dark_mode': is_dark,
        'palette': app.palette()
    }


def is_system_dark_mode():
    """
    Detect if the system is using dark mode.
    
    Returns:
        bool: True if dark mode is detected, False for light mode
    """
    return _detect_system_dark_mode()
