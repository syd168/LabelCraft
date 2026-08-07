#!/usr/bin/python
# -*- coding: utf-8 -*-


from PySide6.QtGui import *
from PySide6.QtCore import *

from libs.utils import distance
import sys

DEFAULT_LINE_COLOR = QColor(0, 255, 0, 128)
DEFAULT_FILL_COLOR = QColor(255, 0, 0, 28)
DEFAULT_SELECT_LINE_COLOR = QColor(255, 255, 255)
# Light selection tint — visible box, still see image underneath
DEFAULT_SELECT_FILL_COLOR = QColor(0, 160, 255, 32)
POSE_SELECT_FILL_ALPHA = 80
FILL_ALPHA_MAX = 36
# BBox corner handles: cyan squares (distinct from pose keypoints)
DEFAULT_VERTEX_FILL_COLOR = QColor(0, 200, 255, 255)
DEFAULT_HVERTEX_FILL_COLOR = QColor(255, 80, 80, 255)

# First 8 keypoints use this fixed palette (order 0..7).
# Index >= 8: keypoint_color() auto-generates more hues (not limited to 8).
KPT_PALETTE = [
    QColor(255, 64, 64, 230),    # 0 red
    QColor(255, 200, 0, 230),    # 1 yellow
    QColor(180, 80, 255, 230),   # 2 purple
    QColor(255, 128, 0, 230),    # 3 orange
    QColor(0, 220, 180, 230),    # 4 teal
    QColor(255, 100, 180, 230),  # 5 pink
    QColor(100, 140, 255, 230),  # 6 blue
    QColor(200, 255, 80, 230),   # 7 lime
]
# Visibility overlays (YOLO: 0=unlabeled, 1=occluded, 2=visible)
KPT_COLOR_V0 = QColor(120, 120, 120, 180)
KPT_COLOR_V1_RING = QColor(255, 165, 0, 255)
KPT_SKELETON_COLOR = QColor(0, 200, 255, 180)


def keypoint_color(index, visibility=2):
    """Color for pose keypoint by order index and visibility.

    Supports any keypoint count: 0..7 from KPT_PALETTE; beyond that,
    hues are generated so colors keep distinguishing without hard-capping at 8.
    """
    if int(visibility) == 0:
        return KPT_COLOR_V0
    idx = int(index)
    if 0 <= idx < len(KPT_PALETTE):
        base = KPT_PALETTE[idx]
    else:
        # Spread hues with a prime step so later points stay distinct
        hue = (idx * 47) % 360
        base = QColor.fromHsv(hue, 220, 255, 230)
    if int(visibility) == 1:
        # Occluded: slightly transparent version of the same hue
        return QColor(base.red(), base.green(), base.blue(), 150)
    return base


class Shape(object):
    P_SQUARE, P_ROUND = range(2)

    MOVE_VERTEX, NEAR_VERTEX = range(2)

    # The following class variables influence the drawing
    # of _all_ shape objects.
    line_color = DEFAULT_LINE_COLOR
    fill_color = DEFAULT_FILL_COLOR
    select_line_color = DEFAULT_SELECT_LINE_COLOR
    select_fill_color = DEFAULT_SELECT_FILL_COLOR
    vertex_fill_color = DEFAULT_VERTEX_FILL_COLOR
    h_vertex_fill_color = DEFAULT_HVERTEX_FILL_COLOR
    point_type = P_ROUND
    point_size = 16
    scale = 1.0
    label_font_size = 8
    default_line_width = 2.5

    def __init__(self, label=None, line_color=None, difficult=False, paint_label=False,
                 shape_type='rectangle'):
        self.label = label
        self.points = []
        self.fill = False
        self.selected = False
        self.difficult = difficult
        self.paint_label = paint_label
        self.shape_type = shape_type  # 'rectangle' | 'pose' | 'polygon' | 'ellipse' | 'circle'
        # Pose keypoints: list of {'x': float, 'y': float, 'v': int}
        self.keypoints = []
        self.keypoint_names = []
        self.skeleton = []  # list of [i, j] edges
        self._highlight_kpt = None
        # Per-shape stroke width in image pixels (scaled when painting)
        self.line_width = float(self.default_line_width)

        self._highlight_index = None
        self._highlight_mode = self.NEAR_VERTEX
        self._highlight_settings = {
            self.NEAR_VERTEX: (4, self.P_ROUND),
            self.MOVE_VERTEX: (1.5, self.P_SQUARE),
        }

        self._closed = False

        if line_color is not None:
            # Override the class line_color attribute
            # with an object attribute. Currently this
            # is used for drawing the pending line a different color.
            self.line_color = line_color

    def close(self):
        self._closed = True

    def reach_max_points(self):
        # Polygons are click-to-add vertices (no fixed corner count)
        if self.shape_type == 'polygon':
            return False
        if len(self.points) >= 4:
            return True
        return False

    def add_point(self, point):
        if self.shape_type == 'polygon' or not self.reach_max_points():
            self.points.append(point)

    def add_keypoint(self, x, y, v=2):
        """Append a pose keypoint in pixel coordinates."""
        self.keypoints.append({'x': float(x), 'y': float(y), 'v': int(v)})
        self.shape_type = 'pose'

    def set_keypoints_from_list(self, keypoints):
        """Load keypoints from list of (x,y,v) or dicts."""
        self.keypoints = []
        for kp in keypoints or []:
            if isinstance(kp, dict):
                self.keypoints.append({
                    'x': float(kp.get('x', 0)),
                    'y': float(kp.get('y', 0)),
                    'v': int(kp.get('v', 0)),
                })
            else:
                self.keypoints.append({
                    'x': float(kp[0]),
                    'y': float(kp[1]),
                    'v': int(kp[2]) if len(kp) > 2 else 2,
                })
        if self.keypoints:
            self.shape_type = 'pose'

    def cycle_keypoint_visibility(self, index):
        """Cycle v: 2 -> 1 -> 0 -> 2 for keypoint at index."""
        if 0 <= index < len(self.keypoints):
            cur = int(self.keypoints[index].get('v', 2))
            self.keypoints[index]['v'] = {2: 1, 1: 0, 0: 2}.get(cur, 2)
            return self.keypoints[index]['v']
        return None

    def clear_keypoint(self, index):
        """
        Clear one keypoint while keeping slot order (YOLO-Pose needs fixed K).
        Sets position to (0,0) and visibility to 0 (unlabeled).
        """
        if 0 <= index < len(self.keypoints):
            self.keypoints[index] = {'x': 0.0, 'y': 0.0, 'v': 0}
            return True
        return False

    def remove_last_keypoint(self):
        """Pop the last keypoint (used while placing). Returns removed dict or None."""
        if self.keypoints:
            return self.keypoints.pop()
        return None

    def pop_point(self):
        if self.points:
            return self.points.pop()
        return None

    def is_closed(self):
        return self._closed

    def set_open(self):
        self._closed = False

    def is_ellipse_like(self):
        return self.shape_type in ('ellipse', 'circle')

    def axis_aligned_rect(self):
        """Bounding rect from points (used by ellipse/circle/bbox shapes)."""
        if not self.points:
            return QRectF()
        xs = [p.x() for p in self.points]
        ys = [p.y() for p in self.points]
        return QRectF(QPointF(min(xs), min(ys)), QPointF(max(xs), max(ys)))

    def paint(self, painter):
        if self.points:
            # Always honor per-shape line_color (Shape Line Color button).
            # When selected, brighten slightly instead of forcing white.
            color = self.line_color if self.line_color else DEFAULT_LINE_COLOR
            if self.selected:
                color = QColor(
                    min(255, color.red() + 40),
                    min(255, color.green() + 40),
                    min(255, color.blue() + 40),
                    color.alpha(),
                )
            # Critical: drawPath uses the current brush. Keypoint painting leaves a
            # solid colored brush; without clearing it, the whole bbox gets filled
            # with the last keypoint color (e.g. purple #3).
            painter.setBrush(Qt.BrushStyle.NoBrush)

            line_path = self.make_path()
            vertex_path = QPainterPath()
            for i, _p in enumerate(self.points):
                self.draw_vertex(vertex_path, i)

            lw = float(getattr(self, 'line_width', None) or self.default_line_width)
            # White under-stroke so the box stays readable on dark/busy backgrounds
            under = QPen(QColor(255, 255, 255, 180))
            under.setWidth(max(2, int(round((lw + 1.5) / self.scale))))
            painter.setPen(under)
            painter.drawPath(line_path)
            pen = QPen(color)
            pen.setWidth(max(1, int(round(lw / self.scale))))
            painter.setPen(pen)
            painter.drawPath(line_path)
            # BBox corners: filled squares in cyan (not the same as pose keypoints)
            corner_color = self.h_vertex_fill_color if self._highlight_index is not None \
                else DEFAULT_VERTEX_FILL_COLOR
            painter.drawPath(vertex_path)
            painter.fillPath(vertex_path, corner_color)

            # Draw text at the top-left with outline for better visibility
            if self.paint_label:
                min_x = sys.maxsize
                min_y = sys.maxsize
                min_y_label = int(1.25 * self.label_font_size)
                for point in self.points:
                    min_x = min(min_x, point.x())
                    min_y = min(min_y, point.y())
                if min_x != sys.maxsize and min_y != sys.maxsize:
                    font = QFont()
                    font.setPointSize(self.label_font_size)
                    font.setBold(True)
                    painter.setFont(font)
                    if self.label is None:
                        self.label = ""
                    if min_y < min_y_label:
                        min_y += min_y_label
                    
                    # Draw text with white outline for better visibility
                    text_path = QPainterPath()
                    text_path.addText(int(min_x), int(min_y), font, self.label)
                    
                    # Draw outline (stroke) first - white color
                    outline_pen = QPen(QColor(255, 255, 255, 200))
                    outline_pen.setWidth(2)
                    outline_pen.setJoinStyle(Qt.RoundJoin)
                    painter.setPen(outline_pen)
                    painter.drawPath(text_path)
                    
                    # Draw fill - black color
                    painter.fillPath(text_path, QColor(0, 0, 0, 200))

            # Honor per-shape fill_color / alpha from 选取样式 dialog
            if self.fill:
                base = self.fill_color if self.fill_color else DEFAULT_FILL_COLOR
                alpha = int(base.alpha()) if base.alpha() > 0 else POSE_SELECT_FILL_ALPHA
                # Soft cap only for accidentally opaque (255) colors from old data
                if alpha >= 250:
                    alpha = FILL_ALPHA_MAX
                color = QColor(base.red(), base.green(), base.blue(), alpha)
                painter.fillPath(line_path, color)

        if self.keypoints:
            self.paint_keypoints(painter)

    def paint_keypoints(self, painter):
        """Draw skeleton edges and ordered keypoint markers (circles + #index)."""
        # Skeleton
        if self.skeleton:
            pen = QPen(KPT_SKELETON_COLOR)
            pen.setWidth(max(1, int(round(2.0 / self.scale))))
            painter.setPen(pen)
            for edge in self.skeleton:
                if len(edge) < 2:
                    continue
                i, j = int(edge[0]), int(edge[1])
                if i < len(self.keypoints) and j < len(self.keypoints):
                    a, b = self.keypoints[i], self.keypoints[j]
                    if int(a.get('v', 0)) == 0 or int(b.get('v', 0)) == 0:
                        continue
                    painter.drawLine(
                        QPointF(a['x'], a['y']),
                        QPointF(b['x'], b['y']),
                    )

        d = self.point_size / self.scale
        font = QFont()
        font.setPointSize(max(8, int(self.label_font_size)))
        font.setBold(True)
        painter.setFont(font)

        for i, kp in enumerate(self.keypoints):
            v = int(kp.get('v', 2))
            color = keypoint_color(i, v)

            radius = d / 2.0 * 1.15
            if self._highlight_kpt == i:
                radius *= 1.5

            center = QPointF(kp['x'], kp['y'])
            # White outline then filled circle (order color)
            painter.setBrush(QBrush(color))
            pen_w = max(2, int(round(2.0 / self.scale)))
            if v == 1:
                painter.setPen(QPen(KPT_COLOR_V1_RING, pen_w))
            else:
                painter.setPen(QPen(QColor(255, 255, 255, 230), pen_w))
            painter.drawEllipse(center, radius, radius)

            # Order badge: "#1 name"
            name = ''
            if self.keypoint_names and i < len(self.keypoint_names):
                name = str(self.keypoint_names[i])
            label = f'#{i + 1}' + (f' {name}' if name else '')

            text_pos = QPointF(kp['x'] + radius + 3, kp['y'] - 2)
            # Text outline for readability
            for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                painter.setPen(QPen(QColor(255, 255, 255, 220)))
                painter.drawText(QPointF(text_pos.x() + dx, text_pos.y() + dy), label)
            painter.setPen(QPen(QColor(20, 20, 20, 240)))
            painter.drawText(text_pos, label)

        # Do not leave keypoint brush active for subsequent shape.drawPath calls
        painter.setBrush(Qt.BrushStyle.NoBrush)

    def draw_vertex(self, path, i):
        # BBox corners as squares; polygon vertices as circles
        d = self.point_size / self.scale
        point = self.points[i]
        if i == self._highlight_index:
            size, _mode_shape = self._highlight_settings[self._highlight_mode]
            d *= size
        if self.shape_type == 'polygon':
            path.addEllipse(point, d / 2.0, d / 2.0)
        else:
            path.addRect(point.x() - d / 2, point.y() - d / 2, d, d)

    def nearest_vertex(self, point, epsilon):
        index = None
        for i, p in enumerate(self.points):
            dist = distance(p - point)
            if dist <= epsilon:
                index = i
                epsilon = dist
        return index

    def nearest_keypoint(self, point, epsilon):
        """Return index of nearest keypoint within epsilon, or None."""
        index = None
        best = epsilon
        for i, kp in enumerate(self.keypoints):
            dist = distance(QPointF(kp['x'], kp['y']) - point)
            if dist <= best:
                index = i
                best = dist
        return index

    def move_keypoint_to(self, index, pos):
        if 0 <= index < len(self.keypoints):
            self.keypoints[index]['x'] = float(pos.x())
            self.keypoints[index]['y'] = float(pos.y())

    def highlight_keypoint(self, index):
        self._highlight_kpt = index

    def highlight_keypoint_clear(self):
        self._highlight_kpt = None

    def contains_point(self, point):
        if self.is_ellipse_like() and len(self.points) >= 2:
            rect = self.axis_aligned_rect()
            if rect.width() <= 0 or rect.height() <= 0:
                return False
            # Normalize to unit circle: ((x-cx)/rx)^2 + ((y-cy)/ry)^2 <= 1
            cx = rect.center().x()
            cy = rect.center().y()
            rx = rect.width() / 2.0
            ry = rect.height() / 2.0
            if rx <= 0 or ry <= 0:
                return False
            nx = (point.x() - cx) / rx
            ny = (point.y() - cy) / ry
            return (nx * nx + ny * ny) <= 1.0
        return self.make_path().contains(point)

    def make_path(self):
        path = QPainterPath()
        if not self.points:
            return path
        if self.is_ellipse_like() and len(self.points) >= 2:
            path.addEllipse(self.axis_aligned_rect())
            return path
        path.moveTo(self.points[0])
        for p in self.points[1:]:
            path.lineTo(p)
        if self.is_closed():
            path.lineTo(self.points[0])
        return path

    def bounding_rect(self):
        if self.is_ellipse_like():
            return self.axis_aligned_rect()
        return self.make_path().boundingRect()

    def move_by(self, offset):
        self.points = [p + offset for p in self.points]
        for kp in self.keypoints:
            kp['x'] += offset.x()
            kp['y'] += offset.y()

    def move_vertex_by(self, i, offset):
        self.points[i] = self.points[i] + offset

    def highlight_vertex(self, i, action):
        self._highlight_index = i
        self._highlight_mode = action

    def highlight_clear(self):
        self._highlight_index = None
        self._highlight_kpt = None

    def copy(self):
        shape = Shape("%s" % self.label, shape_type=self.shape_type)
        shape.points = [p for p in self.points]
        shape.fill = self.fill
        shape.selected = self.selected
        shape._closed = self._closed
        if self.line_color != Shape.line_color:
            shape.line_color = self.line_color
        if self.fill_color != Shape.fill_color:
            shape.fill_color = self.fill_color
        shape.line_width = float(getattr(self, 'line_width', self.default_line_width))
        shape.difficult = self.difficult
        shape.keypoints = [dict(k) for k in self.keypoints]
        shape.keypoint_names = list(self.keypoint_names)
        shape.skeleton = [list(e) for e in self.skeleton]
        return shape

    def __len__(self):
        return len(self.points)

    def __getitem__(self, key):
        return self.points[key]

    def __setitem__(self, key, value):
        self.points[key] = value
