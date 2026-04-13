#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Modern I18n Engine for LabelCraft

Features:
- Dynamic language switching without restart
- Rich text (HTML) support
- Parameter interpolation: {name}, {count}
- Nested key structure: menu.file.open
- Signal-based UI update
- Fallback mechanism
"""
import json
import os
from pathlib import Path
from typing import Dict, Optional

from PySide6.QtCore import QObject, Signal, QLocale


class I18nEngine(QObject):
    """
    Modern internationalization engine with dynamic switching support.
    """
    
    # Signal emitted when language changes
    language_changed = Signal(str)  # emits new language code
    
    def __init__(self, locales_dir: str = None):
        super().__init__()
        
        if locales_dir is None:
            # Default to project's locales directory
            locales_dir = os.path.join(
                os.path.dirname(os.path.dirname(__file__)), 
                'locales'
            )
        
        self.locales_dir = Path(locales_dir)
        self.translations: Dict[str, Dict] = {}  # lang -> translation dict
        self.current_language: str = 'en'
        self.fallback_language: str = 'en'
        
        # Load all available translations
        self._load_all_translations()
        
        # Auto-detect system language
        self._auto_detect_language()
    
    def _load_all_translations(self):
        """Load all translation files from locales directory."""
        if not self.locales_dir.exists():
            print(f"Warning: Locales directory not found: {self.locales_dir}")
            return
        
        for lang_file in self.locales_dir.glob('*.json'):
            lang_code = lang_file.stem  # e.g., "zh-CN" from "zh-CN.json"
            try:
                with open(lang_file, 'r', encoding='utf-8') as f:
                    self.translations[lang_code] = json.load(f)
                print(f"✓ Loaded translation: {lang_code}")
            except Exception as e:
                print(f"✗ Failed to load {lang_code}: {e}")
    
    def _auto_detect_language(self):
        """Auto-detect system language and set it."""
        system_locale = QLocale.system().name()  # e.g., "zh_CN"
        lang_code = system_locale.replace('_', '-')  # Convert to "zh-CN"
        
        # Try exact match first
        if lang_code in self.translations:
            self.set_language(lang_code)
            return
        
        # Try language-only match (e.g., "zh" for "zh-CN")
        lang_only = lang_code.split('-')[0]
        for available_lang in self.translations.keys():
            if available_lang.startswith(lang_only):
                self.set_language(available_lang)
                return
        
        # Fallback to English
        self.set_language(self.fallback_language)
    
    def set_language(self, lang_code: str):
        """
        Switch language dynamically.
        
        Args:
            lang_code: Language code (e.g., "zh-CN", "en", "de-DE")
        """
        if lang_code not in self.translations:
            print(f"Warning: Language '{lang_code}' not available, using fallback")
            lang_code = self.fallback_language
        
        if lang_code == self.current_language:
            return  # No change needed
        
        old_lang = self.current_language
        self.current_language = lang_code
        print(f"🌐 Language switched: {old_lang} → {lang_code}")
        
        # Emit signal to notify all UI components
        self.language_changed.emit(lang_code)
    
    def get_available_languages(self) -> Dict[str, str]:
        """
        Get list of available languages.
        
        Returns:
            Dict mapping lang_code to display name
        """
        lang_names = {
            'en': 'English',
            'zh-CN': '简体中文',
            'zh-TW': '繁體中文',
            'de-DE': 'Deutsch',
            'fr-FR': 'Français',
            'ja-JP': '日本語',
        }
        
        available = {}
        for lang_code in self.translations.keys():
            available[lang_code] = lang_names.get(lang_code, lang_code)
        
        return available
    
    def tr(self, key: str, **kwargs) -> str:
        """
        Translate a string with parameter interpolation.
        
        Usage:
            i18n.tr('menu.file.open')
            i18n.tr('message.welcome', name='John', count=5)
            i18n.tr('html.rich_text')  # Returns HTML formatted text
        
        Args:
            key: Translation key (dot-separated, e.g., "menu.file.open")
            **kwargs: Parameters for interpolation
        
        Returns:
            Translated string
        """
        # Get translation from current language
        text = self._get_translation(key, self.current_language)
        
        # Fallback to English if not found
        if text is None and self.current_language != self.fallback_language:
            text = self._get_translation(key, self.fallback_language)
        
        # If still not found, return the key itself
        if text is None:
            return f"[MISSING: {key}]"
        
        # Parameter interpolation: {name} -> value
        if kwargs:
            text = self._interpolate(text, **kwargs)
        
        return text
    
    def _get_translation(self, key: str, lang_code: str) -> Optional[str]:
        """
        Get translation by key from specified language.
        
        Supports nested keys: "menu.file.open" -> translations['menu']['file']['open']
        """
        if lang_code not in self.translations:
            return None
        
        keys = key.split('.')
        value = self.translations[lang_code]
        
        try:
            for k in keys:
                value = value[k]
            return value if isinstance(value, str) else None
        except (KeyError, TypeError):
            return None
    
    def _interpolate(self, text: str, **kwargs) -> str:
        """
        Interpolate parameters into text.
        
        Examples:
            "Hello {name}" + name="World" -> "Hello World"
            "{count} items" + count=5 -> "5 items"
        """
        try:
            return text.format(**kwargs)
        except KeyError as e:
            print(f"Warning: Missing parameter {e} in translation: {text}")
            return text
    
    def tr_html(self, key: str, **kwargs) -> str:
        """
        Translate and return HTML-formatted rich text.
        
        Usage:
            i18n.tr_html('help.tutorial', link='<a href="...">click here</a>')
        
        The translation file should contain HTML tags:
            "tutorial": "<p>Read our <b>{link}</b> for details.</p>"
        """
        return self.tr(key, **kwargs)
    
    def tr_plural(self, key: str, count: int, **kwargs) -> str:
        """
        Handle pluralization.
        
        Translation file structure:
            "items": {
                "zero": "No items",
                "one": "{count} item",
                "other": "{count} items"
            }
        
        Usage:
            i18n.tr_plural('message.items', count=0)  -> "No items"
            i18n.tr_plural('message.items', count=1)  -> "1 item"
            i18n.tr_plural('message.items', count=5)  -> "5 items"
        """
        if count == 0:
            plural_key = f"{key}.zero"
        elif count == 1:
            plural_key = f"{key}.one"
        else:
            plural_key = f"{key}.other"
        
        return self.tr(plural_key, count=count, **kwargs)
