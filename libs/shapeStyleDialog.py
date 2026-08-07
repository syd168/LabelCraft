# Copyright (c) 2024-2026 LabelCraft
"""Dialog to edit selected annotation box style (line / fill)."""

from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QColor, QPainter, QPen, QBrush
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel, QPushButton,
    QSpinBox, QSlider, QDialogButtonBox, QColorDialog, QGroupBox, QWidget,
    QCheckBox,
)

from libs.shape import DEFAULT_LINE_COLOR, DEFAULT_FILL_COLOR


class _StylePreview(QWidget):
    """Mini preview of line + translucent fill."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.line_color = QColor(DEFAULT_LINE_COLOR)
        self.fill_color = QColor(DEFAULT_FILL_COLOR)
        self.line_width = 2
        self.setMinimumHeight(72)
        self.setMinimumWidth(220)

    def set_style(self, line_color, fill_color, line_width):
        self.line_color = QColor(line_color)
        self.fill_color = QColor(fill_color)
        self.line_width = max(1, int(line_width))
        self.update()

    def paintEvent(self, _event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.fillRect(self.rect(), QColor(60, 60, 60))
        margin = 14
        rect = self.rect().adjusted(margin, margin, -margin, -margin)
        p.setBrush(QBrush(self.fill_color))
        pen = QPen(self.line_color)
        pen.setWidth(self.line_width)
        p.setPen(pen)
        p.drawRect(rect)
        p.end()


class ShapeStyleDialog(QDialog):
    """Edit line color/width and fill color/opacity for the selected shape.

    Created as a top-level window (no transient parent) so dragging it does
    not move the main LabelCraft window. Optional on_preview for live canvas update.
    """

    def __init__(self, parent=None, line_color=None, fill_color=None, line_width=2,
                 on_preview=None):
        # parent=None → independent top-level window (avoids WM moving main window)
        super().__init__(None)
        self.parent_window = parent
        self.on_preview = on_preview
        self._line_color = QColor(line_color or DEFAULT_LINE_COLOR)
        self._fill_color = QColor(fill_color or DEFAULT_FILL_COLOR)
        if self._fill_color.alpha() <= 0:
            self._fill_color.setAlpha(28)
        self._line_width = max(1, int(line_width or 2))

        self.setWindowTitle(self._tr('shapeStyle', '选取样式'))
        self.setWindowFlags(
            Qt.WindowType.Dialog
            | Qt.WindowType.WindowTitleHint
            | Qt.WindowType.WindowCloseButtonHint
            | Qt.WindowType.WindowStaysOnTopHint
        )
        # Window-modal only vs parent_window conceptually; no transient attach
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setModal(True)

        self._build_ui()
        self._refresh_preview()
        self._place_near_parent()

    def _tr(self, key, default):
        if self.parent_window and hasattr(self.parent_window, 'get_str'):
            text = self.parent_window.get_str(key)
            if text and text != key:
                return text
        return default

    def _place_near_parent(self):
        """Show beside the main window so the selection stays visible."""
        self.adjustSize()
        if not self.parent_window:
            return
        geo = self.parent_window.frameGeometry()
        dlg = self.frameGeometry()
        # Prefer right side of main window; fall back to left if off-screen
        x = geo.right() - dlg.width() - 24
        y = geo.top() + 80
        screen = self.parent_window.screen()
        if screen is not None:
            avail = screen.availableGeometry()
            if x + dlg.width() > avail.right():
                x = geo.left() + 24
            x = max(avail.left(), min(x, avail.right() - dlg.width()))
            y = max(avail.top(), min(y, avail.bottom() - dlg.height()))
        self.move(QPoint(x, y))

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setSpacing(10)

        form_box = QGroupBox(self._tr('shapeStyleBox', '标注框样式'))
        form = QFormLayout(form_box)

        line_row = QHBoxLayout()
        self.line_swatch = QLabel()
        self.line_swatch.setFixedSize(36, 22)
        self._paint_swatch(self.line_swatch, self._line_color)
        btn_line = QPushButton(self._tr('chooseColor', '选择颜色…'))
        btn_line.clicked.connect(self._pick_line_color)
        line_row.addWidget(self.line_swatch)
        line_row.addWidget(btn_line, 1)
        form.addRow(self._tr('shapeStyleLineColor', '线条颜色'), line_row)

        self.width_spin = QSpinBox()
        self.width_spin.setRange(1, 12)
        self.width_spin.setValue(self._line_width)
        self.width_spin.setSuffix(' px')
        self.width_spin.valueChanged.connect(self._on_width_changed)
        form.addRow(self._tr('shapeStyleLineWidth', '线条粗细'), self.width_spin)

        fill_row = QHBoxLayout()
        self.fill_swatch = QLabel()
        self.fill_swatch.setFixedSize(36, 22)
        self._paint_swatch(self.fill_swatch, self._fill_color)
        btn_fill = QPushButton(self._tr('chooseColor', '选择颜色…'))
        btn_fill.clicked.connect(self._pick_fill_color)
        fill_row.addWidget(self.fill_swatch)
        fill_row.addWidget(btn_fill, 1)
        form.addRow(self._tr('shapeStyleFillColor', '背景填充色'), fill_row)

        opacity_row = QHBoxLayout()
        self.opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self.opacity_slider.setRange(0, 100)
        self.opacity_slider.setValue(int(round(self._fill_color.alpha() * 100 / 255)))
        self.opacity_label = QLabel(f'{self.opacity_slider.value()}%')
        self.opacity_label.setMinimumWidth(40)
        self.opacity_slider.valueChanged.connect(self._on_opacity_changed)
        opacity_row.addWidget(self.opacity_slider, 1)
        opacity_row.addWidget(self.opacity_label)
        form.addRow(self._tr('shapeStyleOpacity', '填充不透明度'), opacity_row)

        root.addWidget(form_box)

        prev_box = QGroupBox(self._tr('shapeStylePreview', '预览'))
        prev_layout = QVBoxLayout(prev_box)
        self.preview = _StylePreview()
        prev_layout.addWidget(self.preview)
        tip = QLabel(self._tr(
            'shapeStyleTip',
            '默认只改当前选中框。各框样式可不同；勾选下方选项可统一本图全部标注。'))
        tip.setWordWrap(True)
        tip.setStyleSheet('color: gray;')
        prev_layout.addWidget(tip)
        root.addWidget(prev_box)

        self.apply_all_check = QCheckBox(self._tr(
            'shapeStyleApplyAll',
            '应用到本图全部标注'))
        self.apply_all_check.setToolTip(self._tr(
            'shapeStyleApplyAllTip',
            '确定后，将当前线条/填充/粗细应用到本张图像上的所有标注框。'))
        root.addWidget(self.apply_all_check)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)

    @staticmethod
    def _paint_swatch(label, color):
        label.setStyleSheet(
            f'background-color: rgba({color.red()},{color.green()},{color.blue()},{color.alpha()});'
            f'border: 1px solid #888; border-radius: 3px;'
        )

    def _emit_preview(self):
        if callable(self.on_preview):
            self.on_preview(
                QColor(self._line_color),
                QColor(self._fill_color),
                int(self._line_width),
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
        rgb = QColor(self._fill_color.red(), self._fill_color.green(), self._fill_color.blue())
        dlg = QColorDialog(rgb, self)
        dlg.setOption(QColorDialog.ColorDialogOption.ShowAlphaChannel, False)
        dlg.setOption(QColorDialog.ColorDialogOption.DontUseNativeDialog, True)
        if dlg.exec():
            c = dlg.currentColor()
            if c.isValid():
                self._fill_color = QColor(c.red(), c.green(), c.blue(), self._fill_color.alpha())
                self._paint_swatch(self.fill_swatch, self._fill_color)
                self._refresh_preview()

    def _on_width_changed(self, value):
        self._line_width = int(value)
        self._refresh_preview()

    def _on_opacity_changed(self, value):
        self.opacity_label.setText(f'{value}%')
        alpha = int(round(value * 255 / 100))
        self._fill_color.setAlpha(alpha)
        self._paint_swatch(self.fill_swatch, self._fill_color)
        self._refresh_preview()

    def _refresh_preview(self):
        self.preview.set_style(self._line_color, self._fill_color, self._line_width)
        self._emit_preview()

    def result_style(self):
        """Return (line_color, fill_color, line_width)."""
        return QColor(self._line_color), QColor(self._fill_color), int(self._line_width)

    def apply_to_all(self):
        """True if user asked to apply style to every shape on the image."""
        return bool(self.apply_all_check.isChecked())
