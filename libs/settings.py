# Copyright (c) 2024-2026 LabelCraft
"""
Portable application settings (JSON).

Storage (first match wins):
1. $LABELCRAFT_CONFIG_DIR/settings.json
2. Portable mode: <app>/config/settings.json
   (LABELCRAFT_PORTABLE=1 or a `portable` marker file next to the app)
3. Platform config dir:
   - Linux:   ~/.config/labelcraft/settings.json  ($XDG_CONFIG_HOME)
   - macOS:   ~/Library/Application Support/LabelCraft/settings.json
   - Windows: %APPDATA%/LabelCraft/settings.json

Legacy ~/.labelcraftSettings.pkl is migrated once into the JSON file.
"""
from __future__ import annotations

import base64
import json
import os
import pickle
import platform
import sys
from enum import Enum

from PySide6.QtCore import QByteArray, QPoint, QSize
from PySide6.QtGui import QColor

from libs.constants import (
    SETTING_ADVANCE_MODE,
    SETTING_AUTO_SAVE,
    SETTING_DRAW_SQUARE,
    SETTING_FILENAME,
    SETTING_FILL_COLOR,
    SETTING_FIXED_STYLE,
    SETTING_LAST_OPEN_DIR,
    SETTING_LINE_COLOR,
    SETTING_LINE_WIDTH,
    SETTING_PAINT_LABEL,
    SETTING_RECENT_FILES,
    SETTING_SAVE_DIR,
    SETTING_SINGLE_CLASS,
    SETTING_THEME,
    THEME_SYSTEM,
)

SETTINGS_VERSION = 1
SETTINGS_FILENAME = 'settings.json'
LEGACY_PICKLE_NAME = '.labelcraftSettings.pkl'


def _app_base_dir():
    """Directory that contains the app / frozen executable."""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(os.path.abspath(sys.executable))
    # libs/settings.py → repo LabelCraft/
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _is_portable_mode():
    flag = os.environ.get('LABELCRAFT_PORTABLE', '').strip().lower()
    if flag in ('1', 'true', 'yes', 'on'):
        return True
    marker = os.path.join(_app_base_dir(), 'portable')
    return os.path.exists(marker)


def platform_config_dir():
    """OS-standard config directory (ignores portable / env overrides)."""
    system = platform.system()
    if system == 'Windows':
        base = os.environ.get('APPDATA') or os.path.expanduser('~')
        return os.path.join(base, 'LabelCraft')
    if system == 'Darwin':
        return os.path.expanduser('~/Library/Application Support/LabelCraft')

    xdg = os.environ.get('XDG_CONFIG_HOME', '').strip()
    if not xdg:
        xdg = os.path.expanduser('~/.config')
    return os.path.join(xdg, 'labelcraft')


def default_config_dir():
    """Return the directory that should hold settings.json (portable-aware)."""
    override = os.environ.get('LABELCRAFT_CONFIG_DIR', '').strip()
    if override:
        return os.path.abspath(os.path.expanduser(override))

    if _is_portable_mode():
        return os.path.join(_app_base_dir(), 'config')

    return platform_config_dir()


def default_settings_path():
    return os.path.join(default_config_dir(), SETTINGS_FILENAME)


def platform_settings_path():
    return os.path.join(platform_config_dir(), SETTINGS_FILENAME)


def legacy_pickle_path():
    return os.path.join(os.path.expanduser('~'), LEGACY_PICKLE_NAME)


def default_settings_data():
    """Built-in defaults used when no config file exists yet."""
    from libs.shape import DEFAULT_FILL_COLOR, DEFAULT_LINE_COLOR

    return {
        SETTING_THEME: THEME_SYSTEM,
        SETTING_AUTO_SAVE: False,
        SETTING_SINGLE_CLASS: False,
        SETTING_PAINT_LABEL: False,
        SETTING_DRAW_SQUARE: False,
        SETTING_FIXED_STYLE: False,
        SETTING_ADVANCE_MODE: False,
        SETTING_LINE_WIDTH: 2.5,
        SETTING_FILENAME: '',
        SETTING_SAVE_DIR: '',
        SETTING_LAST_OPEN_DIR: '',
        SETTING_RECENT_FILES: [],
        # Colors as QColor so callers can use them immediately after load()
        SETTING_LINE_COLOR: QColor(DEFAULT_LINE_COLOR),
        SETTING_FILL_COLOR: QColor(DEFAULT_FILL_COLOR),
    }


class Settings(object):
    def __init__(self, path=None):
        self.data = {}
        self.path = path or default_settings_path()
        self._legacy_pickle = legacy_pickle_path()

    def __setitem__(self, key, value):
        self.data[key] = value

    def __getitem__(self, key):
        return self.data[key]

    def get(self, key, default=None):
        if key in self.data:
            return self.data[key]
        return default

    # ----- encode / decode (JSON-portable) -----

    @classmethod
    def _encode_value(cls, value):
        if isinstance(value, QColor):
            return {
                '__type__': 'QColor',
                'rgba': [value.red(), value.green(), value.blue(), value.alpha()],
            }
        if isinstance(value, QSize):
            return {
                '__type__': 'QSize',
                'width': int(value.width()),
                'height': int(value.height()),
            }
        if isinstance(value, QPoint):
            return {
                '__type__': 'QPoint',
                'x': int(value.x()),
                'y': int(value.y()),
            }
        if isinstance(value, QByteArray):
            b64 = bytes(value.toBase64()).decode('ascii')
            return {'__type__': 'QByteArray', 'base64': b64}
        if isinstance(value, Enum):
            return {
                '__type__': 'Enum',
                'class': value.__class__.__name__,
                'name': value.name,
            }
        if isinstance(value, (list, tuple)):
            return [cls._encode_value(v) for v in value]
        if isinstance(value, dict):
            # Plain dicts only — typed payloads use __type__
            return {str(k): cls._encode_value(v) for k, v in value.items()}
        if isinstance(value, (str, int, float, bool)) or value is None:
            return value
        # Last resort: keep something readable rather than crashing save()
        return str(value)

    @classmethod
    def _decode_value(cls, value):
        if isinstance(value, list):
            return [cls._decode_value(v) for v in value]
        if not isinstance(value, dict):
            return value

        type_name = value.get('__type__')
        if type_name == 'QColor':
            rgba = value.get('rgba') or [0, 0, 0, 255]
            while len(rgba) < 4:
                rgba.append(255 if len(rgba) == 3 else 0)
            return QColor(int(rgba[0]), int(rgba[1]), int(rgba[2]), int(rgba[3]))
        if type_name == 'QSize':
            return QSize(int(value.get('width', 0)), int(value.get('height', 0)))
        if type_name == 'QPoint':
            return QPoint(int(value.get('x', 0)), int(value.get('y', 0)))
        if type_name == 'QByteArray':
            raw = base64.b64decode(value.get('base64', '') or '')
            return QByteArray(raw)
        if type_name == 'Enum':
            return cls._decode_enum(value.get('class'), value.get('name'))

        # Untyped object → decode nested values
        return {k: cls._decode_value(v) for k, v in value.items()}

    @staticmethod
    def _decode_enum(class_name, member_name):
        if not class_name or not member_name:
            return member_name
        if class_name == 'LabelFileFormat':
            try:
                from libs.labelFile import LabelFileFormat
                return LabelFileFormat[member_name]
            except Exception:
                return member_name
        return member_name

    def _encode_tree(self, data):
        return {str(k): self._encode_value(v) for k, v in data.items()}

    def _decode_tree(self, data):
        if not isinstance(data, dict):
            return {}
        return {k: self._decode_value(v) for k, v in data.items()}

    # ----- normalize values coming from legacy pickle -----

    def _normalize_loaded(self, data):
        """Ensure pickle/legacy values become JSON-roundtrippable natives."""
        if not isinstance(data, dict):
            return {}
        out = {}
        for key, value in data.items():
            # Re-encode/decode cleans Qt / Enum objects from pickle
            try:
                out[key] = self._decode_value(self._encode_value(value))
            except Exception:
                out[key] = value
        return out

    # ----- persistence -----

    def save(self):
        if not self.path:
            return False
        try:
            directory = os.path.dirname(self.path)
            if directory:
                os.makedirs(directory, exist_ok=True)
            payload = {
                'version': SETTINGS_VERSION,
                'settings': self._encode_tree(self.data),
            }
            tmp_path = self.path + '.tmp'
            with open(tmp_path, 'w', encoding='utf-8') as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)
                f.write('\n')
            os.replace(tmp_path, self.path)
            return True
        except Exception as exc:
            print(f'Saving settings failed: {exc}')
            try:
                if os.path.exists(self.path + '.tmp'):
                    os.remove(self.path + '.tmp')
            except OSError:
                pass
            return False

    def _load_json_file(self, path):
        with open(path, 'r', encoding='utf-8') as f:
            payload = json.load(f)
        if isinstance(payload, dict) and 'settings' in payload:
            raw = payload.get('settings') or {}
        elif isinstance(payload, dict):
            # Flat file without wrapper
            raw = {k: v for k, v in payload.items() if k != 'version'}
        else:
            raw = {}
        return self._decode_tree(raw)

    def _load_pickle_file(self, path):
        with open(path, 'rb') as f:
            data = pickle.load(f)
        return self._normalize_loaded(data if isinstance(data, dict) else {})

    def _write_defaults(self):
        self.data = self._default_data_copy()
        self.save()
        print(f'Created default settings: {self.path}')
        return True

    @staticmethod
    def _default_data_copy():
        # deepcopy cannot clone QColor in some Qt builds — rebuild explicitly
        data = default_settings_data()
        out = {}
        for k, v in data.items():
            if isinstance(v, QColor):
                out[k] = QColor(v)
            elif isinstance(v, list):
                out[k] = list(v)
            else:
                out[k] = v
        return out

    def load(self):
        """
        Load settings.

        Order:
        1. JSON at self.path
        2. Migrate legacy pickle → JSON
        3. Create & load defaults
        """
        try:
            if self.path and os.path.isfile(self.path):
                loaded = self._load_json_file(self.path)
                self.data = self._default_data_copy()
                self.data.update(loaded)
                return True

            # Migrate ~/.labelcraftSettings.pkl only into the OS-standard
            # config path — never for portable / LABELCRAFT_CONFIG_DIR / tests.
            if (self.path == platform_settings_path()
                    and os.path.isfile(self._legacy_pickle)):
                print(f'Migrating legacy settings: {self._legacy_pickle}')
                loaded = self._load_pickle_file(self._legacy_pickle)
                self.data = self._default_data_copy()
                self.data.update(loaded)
                if self.save():
                    bak = self._legacy_pickle + '.bak'
                    try:
                        os.replace(self._legacy_pickle, bak)
                        print(f'Legacy pickle moved to: {bak}')
                    except OSError:
                        # Keep original if rename fails; JSON is already written
                        pass
                return True

            return self._write_defaults()
        except Exception as exc:
            print(f'Loading settings failed: {exc}')
            try:
                return self._write_defaults()
            except Exception as exc2:
                print(f'Creating default settings failed: {exc2}')
                self.data = self._default_data_copy()
                return False

    def reset(self):
        """Remove the settings file and restore in-memory defaults."""
        try:
            if self.path and os.path.isfile(self.path):
                os.remove(self.path)
                print(f'Removed settings file: {self.path}')
        except OSError as exc:
            print(f'Failed to remove settings file: {exc}')
        self.data = self._default_data_copy()
        self.save()
