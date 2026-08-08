#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
LabelCraft Theme Manager
Supports system / light / dark themes on Linux, Windows, and macOS.
"""
from PySide6.QtGui import QPalette, QColor
from PySide6.QtWidgets import QApplication
import platform
import os

THEME_SYSTEM = 'system'
THEME_LIGHT = 'light'
THEME_DARK = 'dark'
VALID_THEMES = (THEME_SYSTEM, THEME_LIGHT, THEME_DARK)


def _create_dark_palette():
    """Create a comprehensive dark theme palette."""
    dark_palette = QPalette()

    dark_bg = QColor(53, 53, 53)
    darker_bg = QColor(25, 25, 25)
    light_text = QColor(255, 255, 255)
    muted_text = QColor(170, 170, 170)  # secondary / tip text on dark bg
    link_color = QColor(42, 130, 218)

    dark_palette.setColor(QPalette.ColorRole.Window, dark_bg)
    dark_palette.setColor(QPalette.ColorRole.Base, darker_bg)
    dark_palette.setColor(QPalette.ColorRole.AlternateBase, dark_bg)

    dark_palette.setColor(QPalette.ColorRole.WindowText, light_text)
    dark_palette.setColor(QPalette.ColorRole.Text, light_text)
    dark_palette.setColor(QPalette.ColorRole.ButtonText, light_text)
    dark_palette.setColor(QPalette.ColorRole.BrightText, QColor(255, 255, 255))

    # 3D / chrome roles — must be dark-theme aware. Leaving Qt defaults here
    # makes stylesheet `palette(mid)` resolve to a near-black color → invisible tips.
    dark_palette.setColor(QPalette.ColorRole.Light, QColor(80, 80, 80))
    dark_palette.setColor(QPalette.ColorRole.Midlight, QColor(66, 66, 66))
    dark_palette.setColor(QPalette.ColorRole.Mid, muted_text)
    dark_palette.setColor(QPalette.ColorRole.Dark, QColor(35, 35, 35))

    dark_palette.setColor(QPalette.ColorRole.Button, dark_bg)
    dark_palette.setColor(QPalette.ColorRole.Shadow, QColor(20, 20, 20))
    dark_palette.setColor(QPalette.ColorRole.Highlight, link_color)
    dark_palette.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))

    dark_palette.setColor(QPalette.ColorRole.Link, link_color)

    dark_palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(45, 45, 45))
    dark_palette.setColor(QPalette.ColorRole.ToolTipText, light_text)

    dark_palette.setColor(QPalette.ColorRole.PlaceholderText, muted_text)

    dark_palette.setColor(
        QPalette.ColorGroup.Disabled, QPalette.ColorRole.WindowText, QColor(128, 128, 128))
    dark_palette.setColor(
        QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, QColor(128, 128, 128))
    dark_palette.setColor(
        QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, QColor(128, 128, 128))
    dark_palette.setColor(
        QPalette.ColorGroup.Disabled, QPalette.ColorRole.PlaceholderText, QColor(100, 100, 100))

    return dark_palette


def _create_light_palette():
    """Create a light theme palette (Qt default light)."""
    return QPalette()


def _detect_windows_dark_mode():
    try:
        import winreg
        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r'Software\Microsoft\Windows\CurrentVersion\Themes\Personalize'
            )
            value, _regtype = winreg.QueryValueEx(key, 'AppsUseLightTheme')
            winreg.CloseKey(key)
            return value == 0
        except Exception:
            return False
    except ImportError:
        return False
    except Exception:
        return False


def _detect_linux_dark_mode():
    try:
        import subprocess
        result = subprocess.run(
            ['dconf', 'read', '/org/gnome/desktop/interface/gtk-theme'],
            capture_output=True, text=True, timeout=2)
        if result.returncode == 0:
            theme_name = result.stdout.strip().strip("'\"")
            if 'dark' in theme_name.lower():
                return True
    except (FileNotFoundError, subprocess.TimeoutExpired, Exception):
        pass

    try:
        import subprocess
        result = subprocess.run(
            ['gsettings', 'get', 'org.gnome.desktop.interface',
             'gtk-application-prefer-dark-theme'],
            capture_output=True, text=True, timeout=2)
        if result.returncode == 0:
            return 'true' in result.stdout.lower()
    except (FileNotFoundError, subprocess.TimeoutExpired, Exception):
        pass

    # GNOME 42+ color-scheme
    try:
        import subprocess
        result = subprocess.run(
            ['gsettings', 'get', 'org.gnome.desktop.interface', 'color-scheme'],
            capture_output=True, text=True, timeout=2)
        if result.returncode == 0 and 'prefer-dark' in result.stdout.lower():
            return True
    except (FileNotFoundError, subprocess.TimeoutExpired, Exception):
        pass

    if os.environ.get('GTK_THEME', '').lower().endswith('-dark') or \
            'dark' in os.environ.get('GTK_THEME', '').lower():
        return True

    if 'dark' in os.environ.get('QT_STYLE_OVERRIDE', '').lower():
        return True

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
    try:
        import subprocess
        result = subprocess.run(
            ['defaults', 'read', '-g', 'AppleInterfaceStyle'],
            capture_output=True, text=True, timeout=2)
        if result.returncode != 0:
            return False
        return 'dark' in result.stdout.strip().lower()
    except (FileNotFoundError, subprocess.TimeoutExpired, Exception):
        return False


def _detect_system_dark_mode():
    system = platform.system()
    if system == 'Windows':
        return _detect_windows_dark_mode()
    if system == 'Linux':
        return _detect_linux_dark_mode()
    if system == 'Darwin':
        return _detect_macos_dark_mode()
    return False


def is_system_dark_mode():
    """Return True if the OS prefers dark mode."""
    return _detect_system_dark_mode()


def normalize_theme(theme):
    """Return a valid theme id; default system."""
    if theme in VALID_THEMES:
        return theme
    return THEME_SYSTEM


def apply_theme(app, theme=THEME_SYSTEM):
    """
    Apply theme to QApplication.

    Args:
        app: QApplication instance
        theme: 'system' | 'light' | 'dark'

    Returns:
        dict with theme, is_dark_mode, palette
    """
    if app is None:
        app = QApplication.instance()
    if app is None:
        raise RuntimeError('No QApplication instance')

    theme = normalize_theme(theme)
    app.setStyle('Fusion')

    if theme == THEME_DARK:
        is_dark = True
    elif theme == THEME_LIGHT:
        is_dark = False
    else:
        is_dark = _detect_system_dark_mode()

    if is_dark:
        app.setPalette(_create_dark_palette())
    else:
        app.setPalette(_create_light_palette())

    return {
        'theme': theme,
        'is_dark_mode': is_dark,
        'palette': app.palette(),
    }


def apply_system_theme(app):
    """Backward-compatible wrapper: follow system light/dark preference."""
    return apply_theme(app, THEME_SYSTEM)
