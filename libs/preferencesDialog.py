# Copyright (c) 2024-2026 LabelCraft
"""Application Preferences dialog (language, theme, annotation, default style)."""

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPainter, QPen, QBrush
from PySide6.QtWidgets import (
    QCheckBox, QColorDialog, QComboBox, QDialog, QDialogButtonBox,
    QFormLayout, QGridLayout, QGroupBox, QHBoxLayout, QLabel, QPushButton,
    QSlider, QSpinBox, QVBoxLayout, QWidget,
)

from libs.constants import THEME_DARK, THEME_LIGHT, THEME_SYSTEM
from libs.shape import DEFAULT_FILL_COLOR, DEFAULT_LINE_COLOR
from libs.theme_manager import VALID_THEMES, normalize_theme


class _StylePreview(QWidget):
    """Compact preview of line + translucent fill."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.line_color = QColor(DEFAULT_LINE_COLOR)
        self.fill_color = QColor(DEFAULT_FILL_COLOR)
        self.line_width = 2
        self.setFixedSize(120, 88)

    def set_style(self, line_color, fill_color, line_width):
        self.line_color = QColor(line_color)
        self.fill_color = QColor(fill_color)
        self.line_width = max(1, int(line_width))
        self.update()

    def paintEvent(self, _event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.fillRect(self.rect(), QColor(60, 60, 60))
        margin = 10
        rect = self.rect().adjusted(margin, margin, -margin, -margin)
        p.setBrush(QBrush(self.fill_color))
        pen = QPen(self.line_color)
        pen.setWidth(self.line_width)
        p.setPen(pen)
        p.drawRect(rect)
        p.end()


class PreferencesDialog(QDialog):
    """Edit app-global preferences (compact two-column layout)."""

    def __init__(self, parent=None, languages=None, values=None, tr=None):
        super().__init__(parent)
        self._tr = tr or (lambda k, d=None: d if d is not None else k)
        self._languages = languages or {'en': 'English'}
        self._values = dict(values or {})

        self.setWindowTitle(self._t('preferencesTitle', 'Preferences'))
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setMinimumWidth(640)

        self._line_color = QColor(self._values.get('line_color', DEFAULT_LINE_COLOR))
        self._fill_color = QColor(self._values.get('fill_color', DEFAULT_FILL_COLOR))
        if self._fill_color.alpha() <= 0:
            self._fill_color.setAlpha(28)
        self._line_width = max(1, int(round(float(
            self._values.get('line_width', 2) or 2))))

        self._build_ui()
        self._load_values()
        self.adjustSize()

    def _t(self, key, default):
        return self._tr(key, default)

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(14, 12, 14, 12)
        root.setSpacing(10)

        tip = QLabel(self._t(
            'preferencesIntro',
            'These options apply to the whole application and are remembered after restart.'))
        tip.setWordWrap(True)
        tip.setStyleSheet('color: palette(placeholder-text);')
        root.addWidget(tip)

        # —— General: language + theme on one row ——
        general = QGroupBox(self._t('preferencesGeneral', 'General'))
        gen_row = QHBoxLayout(general)
        gen_row.setSpacing(16)

        lang_box = QVBoxLayout()
        lang_box.setSpacing(4)
        lang_label = QLabel(self._t('preferencesLanguage', 'Language'))
        self.lang_combo = QComboBox()
        for code, name in sorted(self._languages.items(), key=lambda x: x[1]):
            self.lang_combo.addItem(name, code)
        self.lang_combo.setToolTip(self._t(
            'preferencesLanguageTip',
            'Interface language. Saved and restored on next launch.'))
        lang_box.addWidget(lang_label)
        lang_box.addWidget(self.lang_combo)
        gen_row.addLayout(lang_box, 1)

        theme_box = QVBoxLayout()
        theme_box.setSpacing(4)
        theme_label = QLabel(self._t('preferencesTheme', 'Theme'))
        self.theme_combo = QComboBox()
        for code, name in (
            (THEME_SYSTEM, self._t('themeSystem', 'Follow system')),
            (THEME_LIGHT, self._t('themeLight', 'Light')),
            (THEME_DARK, self._t('themeDark', 'Dark')),
        ):
            self.theme_combo.addItem(name, code)
        self.theme_combo.setToolTip(self._t(
            'preferencesThemeTip',
            'Application appearance. “Follow system” tracks OS light/dark mode.'))
        theme_box.addWidget(theme_label)
        theme_box.addWidget(self.theme_combo)
        gen_row.addLayout(theme_box, 1)
        root.addWidget(general)

        # —— Annotation | Style side by side ——
        columns = QHBoxLayout()
        columns.setSpacing(10)

        annot = QGroupBox(self._t('preferencesAnnotation', 'Annotation'))
        annot_grid = QGridLayout(annot)
        annot_grid.setHorizontalSpacing(12)
        annot_grid.setVerticalSpacing(8)

        self.auto_save_cb = QCheckBox(self._t('autoSaveMode', 'Auto Save mode'))
        self.auto_save_cb.setToolTip(self._t(
            'preferencesAutoSaveTip',
            'Automatically save when switching to the next / previous image.'))

        self.single_class_cb = QCheckBox(self._t('singleClsMode', 'Single Class Mode'))
        self.single_class_cb.setToolTip(self._t(
            'preferencesSingleClassTip',
            'Reuse the previous label for new boxes without asking each time.'))

        self.paint_label_cb = QCheckBox(self._t('displayLabel', 'Display Labels'))
        self.paint_label_cb.setToolTip(self._t(
            'preferencesDisplayLabelTip',
            'Show class names on top of annotation boxes.'))

        self.draw_square_cb = QCheckBox(self._t(
            'preferencesDrawSquare', 'Force square drawing'))
        self.draw_square_cb.setToolTip(self._t(
            'preferencesDrawSquareTip',
            'When enabled, new rectangles are constrained to squares while drawing '
            '(Ctrl can still toggle temporarily).'))

        annot_grid.addWidget(self.auto_save_cb, 0, 0)
        annot_grid.addWidget(self.single_class_cb, 0, 1)
        annot_grid.addWidget(self.paint_label_cb, 1, 0)
        annot_grid.addWidget(self.draw_square_cb, 1, 1)
        annot_grid.setColumnStretch(0, 1)
        annot_grid.setColumnStretch(1, 1)
        annot_grid.setRowStretch(2, 1)
        columns.addWidget(annot, 2)

        style = QGroupBox(self._t('preferencesDefaultStyle', 'Default box style'))
        style_outer = QHBoxLayout(style)
        style_outer.setSpacing(12)

        style_form = QFormLayout()
        style_form.setContentsMargins(0, 0, 0, 0)
        style_form.setHorizontalSpacing(10)
        style_form.setVerticalSpacing(6)
        style_form.setLabelAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        self.fixed_style_cb = QCheckBox(self._t(
            'preferencesFixedStyle',
            'Use fixed colors for new boxes'))
        self.fixed_style_cb.setToolTip(self._t(
            'preferencesFixedStyleTip',
            'When off, new boxes are colored by label name (current default). '
            'When on, new boxes use the line/fill colors below.'))
        style_form.addRow(self.fixed_style_cb)

        line_row = QHBoxLayout()
        self.line_swatch = QLabel()
        self.line_swatch.setFixedSize(28, 18)
        btn_line = QPushButton(self._t('chooseColor', 'Choose color…'))
        btn_line.setMaximumWidth(120)
        btn_line.clicked.connect(self._pick_line_color)
        line_row.addWidget(self.line_swatch)
        line_row.addWidget(btn_line, 1)
        style_form.addRow(
            self._t('shapeStyleLineColor', 'Line color'), line_row)

        self.width_spin = QSpinBox()
        self.width_spin.setRange(1, 12)
        self.width_spin.setSuffix(' px')
        self.width_spin.setMaximumWidth(90)
        self.width_spin.valueChanged.connect(self._refresh_preview)
        style_form.addRow(
            self._t('shapeStyleLineWidth', 'Line width'), self.width_spin)

        fill_row = QHBoxLayout()
        self.fill_swatch = QLabel()
        self.fill_swatch.setFixedSize(28, 18)
        btn_fill = QPushButton(self._t('chooseColor', 'Choose color…'))
        btn_fill.setMaximumWidth(120)
        btn_fill.clicked.connect(self._pick_fill_color)
        fill_row.addWidget(self.fill_swatch)
        fill_row.addWidget(btn_fill, 1)
        style_form.addRow(
            self._t('shapeStyleFillColor', 'Fill color'), fill_row)

        opacity_row = QHBoxLayout()
        self.opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self.opacity_slider.setRange(0, 100)
        self.opacity_slider.setMaximumWidth(140)
        self.opacity_label = QLabel('0%')
        self.opacity_label.setMinimumWidth(36)
        self.opacity_slider.valueChanged.connect(self._on_opacity_changed)
        opacity_row.addWidget(self.opacity_slider, 1)
        opacity_row.addWidget(self.opacity_label)
        style_form.addRow(
            self._t('shapeStyleOpacity', 'Fill opacity'), opacity_row)

        style_outer.addLayout(style_form, 1)

        preview_col = QVBoxLayout()
        preview_col.setSpacing(4)
        preview_col.addWidget(QLabel(self._t('shapeStylePreview', 'Preview')))
        self.preview = _StylePreview()
        preview_col.addWidget(self.preview, 0, Qt.AlignmentFlag.AlignTop)
        preview_col.addStretch(1)
        style_outer.addLayout(preview_col)

        columns.addWidget(style, 3)
        root.addLayout(columns)

        style_tip = QLabel(self._t(
            'preferencesStyleTip',
            'Line width always applies to new boxes. Colors apply to the drawing '
            'preview; enable “fixed colors” to also use them when a box is created.'))
        style_tip.setWordWrap(True)
        style_tip.setStyleSheet('color: palette(placeholder-text); font-size: 12px;')
        root.addWidget(style_tip)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)

        self._paint_swatch(self.line_swatch, self._line_color)
        self._paint_swatch(self.fill_swatch, self._fill_color)

    def _load_values(self):
        v = self._values
        lang = str(v.get('language', 'en') or 'en').replace('_', '-')
        idx = self.lang_combo.findData(lang)
        if idx >= 0:
            self.lang_combo.setCurrentIndex(idx)

        theme = normalize_theme(v.get('theme', THEME_SYSTEM))
        tidx = self.theme_combo.findData(theme)
        if tidx < 0:
            tidx = self.theme_combo.findData(THEME_SYSTEM)
        if tidx >= 0:
            self.theme_combo.setCurrentIndex(tidx)

        self.auto_save_cb.setChecked(bool(v.get('auto_save', False)))
        self.single_class_cb.setChecked(bool(v.get('single_class', False)))
        self.paint_label_cb.setChecked(bool(v.get('paint_label', False)))
        self.draw_square_cb.setChecked(bool(v.get('draw_square', False)))
        self.fixed_style_cb.setChecked(bool(v.get('fixed_style', False)))

        self.width_spin.setValue(self._line_width)
        self.opacity_slider.blockSignals(True)
        self.opacity_slider.setValue(int(round(self._fill_color.alpha() * 100 / 255)))
        self.opacity_label.setText(f'{self.opacity_slider.value()}%')
        self.opacity_slider.blockSignals(False)
        self._refresh_preview()

    @staticmethod
    def _paint_swatch(label, color):
        label.setStyleSheet(
            f'background-color: rgba({color.red()},{color.green()},'
            f'{color.blue()},{color.alpha()});'
            f'border: 1px solid #888; border-radius: 3px;'
        )

    def _pick_line_color(self):
        dlg = QColorDialog(self._line_color, self)
        dlg.setOption(QColorDialog.ColorDialogOption.ShowAlphaChannel, False)
        dlg.setOption(QColorDialog.ColorDialogOption.DontUseNativeDialog, True)
        if dlg.exec():
            c = dlg.currentColor()
            if c.isValid():
                self._line_color = QColor(c.red(), c.green(), c.blue(), 255)
                self._paint_swatch(self.line_swatch, self._line_color)
                self._refresh_preview()

    def _pick_fill_color(self):
        rgb = QColor(
            self._fill_color.red(), self._fill_color.green(), self._fill_color.blue())
        dlg = QColorDialog(rgb, self)
        dlg.setOption(QColorDialog.ColorDialogOption.ShowAlphaChannel, False)
        dlg.setOption(QColorDialog.ColorDialogOption.DontUseNativeDialog, True)
        if dlg.exec():
            c = dlg.currentColor()
            if c.isValid():
                self._fill_color = QColor(
                    c.red(), c.green(), c.blue(), self._fill_color.alpha())
                self._paint_swatch(self.fill_swatch, self._fill_color)
                self._refresh_preview()

    def _on_opacity_changed(self, value):
        self.opacity_label.setText(f'{value}%')
        self._fill_color.setAlpha(int(round(value * 255 / 100)))
        self._paint_swatch(self.fill_swatch, self._fill_color)
        self._refresh_preview()

    def _refresh_preview(self, *_args):
        self.preview.set_style(
            self._line_color, self._fill_color, self.width_spin.value())

    def result_values(self):
        """Return a dict of selected preference values."""
        theme = self.theme_combo.currentData()
        return {
            'language': self.lang_combo.currentData(),
            'theme': theme if theme in VALID_THEMES else THEME_SYSTEM,
            'auto_save': self.auto_save_cb.isChecked(),
            'single_class': self.single_class_cb.isChecked(),
            'paint_label': self.paint_label_cb.isChecked(),
            'draw_square': self.draw_square_cb.isChecked(),
            'fixed_style': self.fixed_style_cb.isChecked(),
            'line_color': QColor(self._line_color),
            'fill_color': QColor(self._fill_color),
            'line_width': float(self.width_spin.value()),
        }

    def selected_language(self):
        return self.result_values()['language']

    def selected_theme(self):
        return self.result_values()['theme']
