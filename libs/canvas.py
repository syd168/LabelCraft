
from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *

from libs.shape import Shape
from libs.utils import distance

# In PySide6/Qt6, use Qt.CursorShape enum
CURSOR_DEFAULT = Qt.CursorShape.ArrowCursor
CURSOR_POINT = Qt.CursorShape.PointingHandCursor
CURSOR_DRAW = Qt.CursorShape.CrossCursor
CURSOR_MOVE = Qt.CursorShape.ClosedHandCursor
CURSOR_GRAB = Qt.CursorShape.OpenHandCursor

# class Canvas(QGLWidget):


class Canvas(QWidget):
    def _tr(self, key, default=None, *format_args):
        """Translate via main window i18n when available."""
        try:
            win = self.parent().window() if self.parent() else None
            if win is not None and hasattr(win, 'get_str'):
                text = win.get_str(key)
                if format_args:
                    try:
                        return text.format(*format_args)
                    except Exception:
                        return text
                return text
        except Exception:
            pass
        if default is None:
            return key
        if format_args:
            try:
                return default.format(*format_args)
            except Exception:
                return default
        return default

    zoomRequest = Signal(int)
    lightRequest = Signal(int)
    scrollRequest = Signal(int, int)
    newShape = Signal()
    selectionChanged = Signal(bool)
    shapeMoved = Signal()
    drawingPolygon = Signal(bool)
    shapeDoubleClicked = Signal()  # Signal emitted when a shape is double-clicked
    # Pose keypoint placement: (current_index_0based, total, name)
    keypointPlacementProgress = Signal(int, int, str)
    keypointPlacementFinished = Signal()
    # Undo helpers: about to edit geometry; gesture finished (mouse release)
    editAboutToBegin = Signal()
    editGestureFinished = Signal()

    CREATE, EDIT = list(range(2))

    epsilon = 24.0

    def __init__(self, *args, **kwargs):
        super(Canvas, self).__init__(*args, **kwargs)
        # Initialise local state.
        self.mode = self.EDIT
        self.shapes = []
        self.current = None
        self.selected_shape = None  # save the selected shape here
        self.selected_shape_copy = None
        self.drawing_line_color = QColor(0, 0, 255)
        self.drawing_rect_color = QColor(0, 0, 255)
        self.line = Shape(line_color=self.drawing_line_color)
        self.prev_point = QPointF()
        self.offsets = QPointF(), QPointF()
        self.scale = 1.0
        self.overlay_color = None
        self.label_font_size = 8
        self.pixmap = QPixmap()
        self.visible = {}
        self._hide_background = False
        self.hide_background = False
        self.h_shape = None
        self.h_vertex = None
        self.h_keypoint = None  # int index when hovering a pose keypoint
        self._painter = QPainter()
        self._cursor = CURSOR_DEFAULT
        # Menus:
        self.menus = (QMenu(), QMenu())
        # Set widget options.
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.FocusPolicy.WheelFocus)
        self.verified = False
        self.draw_square = False

        # Pose keypoint placement state (after drawing bbox)
        self.placing_keypoints = False
        self.pose_target_shape = None
        self.expected_kpt_count = 0
        self.pose_keypoint_names = []
        # One undo snapshot per drag gesture
        self._gesture_undo_emitted = False
        # What CREATE mode draws:
        # 'rectangle' | 'pose' | 'polygon' | 'ellipse' | 'circle'
        # ellipse/circle are separate tools (type fixed at create time)
        self.create_shape_type = 'rectangle'
        # Ellipse/circle edit anchors (fixed for one corner-drag gesture)
        self._ellipse_edit_center = None
        self._ellipse_edit_opp = None
        self._last_edit_pos = None

        # initialisation for panning
        self.pan_initial_pos = QPoint()

    def is_polygon_drawing(self):
        return self.drawing() and self.create_shape_type == 'polygon'

    def is_ellipse_drawing(self):
        """True while drag-drawing either the ellipse or circle tool."""
        return self.drawing() and self.create_shape_type in ('ellipse', 'circle')

    def _oval_from_center(self, ev=None, shape=None):
        """Shift = from center — circle only (ellipse has no Shift behavior)."""
        if shape is not None:
            is_circle = getattr(shape, 'shape_type', None) == 'circle'
        else:
            is_circle = self.create_shape_type == 'circle'
        if not is_circle:
            return False
        mods = ev.modifiers() if ev is not None else QApplication.keyboardModifiers()
        return bool(mods & Qt.KeyboardModifier.ShiftModifier)

    def _oval_force_circle(self, shape=None):
        """Circle tool / circle shapes always stay circular; ellipse never becomes circle."""
        if shape is not None:
            return getattr(shape, 'shape_type', None) == 'circle'
        return self.create_shape_type == 'circle'

    def hit_epsilon(self):
        """Vertex hit radius in image coords (~constant on screen when zooming)."""
        return max(10.0, 20.0 / max(float(self.scale), 0.05))

    def _clear_ellipse_edit_anchors(self):
        self._ellipse_edit_center = None
        self._ellipse_edit_opp = None

    def _drag_rect_corners(self, p0, p1, force_circle=False, from_center=False):
        """Build TL/TR/BR/BL corners from drag anchors (optionally circle / from center)."""
        if from_center:
            dx = abs(p1.x() - p0.x())
            dy = abs(p1.y() - p0.y())
            if force_circle:
                r = max(dx, dy)
                dx = dy = r
            min_x, max_x = p0.x() - dx, p0.x() + dx
            min_y, max_y = p0.y() - dy, p0.y() + dy
        else:
            if force_circle:
                side = min(abs(p1.x() - p0.x()), abs(p1.y() - p0.y()))
                sx = 1 if p1.x() >= p0.x() else -1
                sy = 1 if p1.y() >= p0.y() else -1
                x1 = p0.x() + sx * side
                y1 = p0.y() + sy * side
                min_x, max_x = min(p0.x(), x1), max(p0.x(), x1)
                min_y, max_y = min(p0.y(), y1), max(p0.y(), y1)
            else:
                min_x, max_x = min(p0.x(), p1.x()), max(p0.x(), p1.x())
                min_y, max_y = min(p0.y(), p1.y()), max(p0.y(), p1.y())

        if self.pixmap:
            min_x = max(0.0, min(min_x, float(self.pixmap.width())))
            max_x = max(0.0, min(max_x, float(self.pixmap.width())))
            min_y = max(0.0, min(min_y, float(self.pixmap.height())))
            max_y = max(0.0, min(max_y, float(self.pixmap.height())))
            if max_x < min_x:
                min_x, max_x = max_x, min_x
            if max_y < min_y:
                min_y, max_y = max_y, min_y

        return [
            QPointF(min_x, min_y),
            QPointF(max_x, min_y),
            QPointF(max_x, max_y),
            QPointF(min_x, max_y),
        ]

    def begin_keypoint_placement(self, shape, count, names=None, skeleton=None):
        """Enter mode to click keypoints in order for a pose shape."""
        self.placing_keypoints = True
        self.pose_target_shape = shape
        self.expected_kpt_count = int(count)
        self.pose_keypoint_names = list(names or [])
        shape.shape_type = 'pose'
        shape.keypoints = []
        shape.keypoint_names = list(names or [])
        if skeleton is not None:
            shape.skeleton = [list(e) for e in skeleton]
        # Leave rectangle-create state so subsequent clicks place keypoints
        self.drawingPolygon.emit(False)
        self.mode = self.EDIT
        self.current = None
        self.select_shape(shape)
        name = self.pose_keypoint_names[0] if self.pose_keypoint_names else '0'
        self.keypointPlacementProgress.emit(0, self.expected_kpt_count, name)
        self.override_cursor(CURSOR_DRAW)
        self.update()

    def cancel_keypoint_placement(self):
        self.placing_keypoints = False
        self.pose_target_shape = None
        self.expected_kpt_count = 0
        self.pose_keypoint_names = []
        self.restore_cursor()
        self.update()

    def selected_keypoint(self):
        return self.h_keypoint is not None

    def set_drawing_color(self, qcolor):
        self.drawing_line_color = qcolor
        self.drawing_rect_color = qcolor

    def enterEvent(self, ev):
        self.override_cursor(self._cursor)

    def leaveEvent(self, ev):
        self.restore_cursor()

    def focusOutEvent(self, ev):
        self.restore_cursor()

    def isVisible(self, shape):
        return self.visible.get(shape, True)

    def drawing(self):
        return self.mode == self.CREATE

    def editing(self):
        return self.mode == self.EDIT

    def set_editing(self, value=True):
        self.mode = self.EDIT if value else self.CREATE
        if not value:  # Create
            self.un_highlight()
            self.de_select_shape()
        self.prev_point = QPointF()
        self.repaint()

    def un_highlight(self, shape=None):
        if shape == None or shape == self.h_shape:
            if self.h_shape:
                self.h_shape.highlight_clear()
            self.h_vertex = self.h_shape = None
            self.h_keypoint = None

    def selected_vertex(self):
        return self.h_vertex is not None

    def mouseMoveEvent(self, ev):
        """Update line with last point and current coordinates."""
        pos = self.transform_pos(ev.pos())

        # Update coordinates in status bar if image is opened
        window = self.parent().window()
        if window.file_path is not None:
            self.parent().window().label_coordinates.setText(
                window.format_coordinates(x=pos.x(), y=pos.y()))

        if self.placing_keypoints:
            self.override_cursor(CURSOR_DRAW)
            self.prev_point = pos
            self.repaint()
            return

        # CREATE-mode drawing (rectangle drag or polygon vertices).
        if self.drawing():
            self.override_cursor(CURSOR_DRAW)
            if self.current:
                color = self.drawing_line_color
                if self.out_of_pixmap(pos):
                    size = self.pixmap.size()
                    clipped_x = min(max(0, pos.x()), size.width())
                    clipped_y = min(max(0, pos.y()), size.height())
                    pos = QPointF(clipped_x, clipped_y)
                elif (self.is_polygon_drawing() and len(self.current) > 1
                      and self.close_enough(pos, self.current[0])):
                    # Snap to first vertex to close the polygon
                    pos = self.current[0]
                    color = self.current.line_color
                    self.override_cursor(CURSOR_POINT)
                    self.current.highlight_vertex(0, Shape.NEAR_VERTEX)

                if self.is_polygon_drawing():
                    self.line.points = [self.current[-1], pos]
                    self.parent().window().label_coordinates.setText(
                        window.format_coordinates(x=pos.x(), y=pos.y())
                        + '  |  '
                        + self._tr(
                            'canvasPolyTip',
                            'poly verts={0} (Enter/dbl-click/first-pt to close)',
                            len(self.current),
                        )
                    )
                elif self.is_ellipse_drawing():
                    force_circle = self._oval_force_circle()
                    from_center = self._oval_from_center(ev)
                    corners = self._drag_rect_corners(
                        self.current[0], pos, force_circle, from_center)
                    self.line.points = [corners[0], corners[2]]
                    mode = 'circle' if force_circle else 'ellipse'
                    origin = 'center' if from_center else 'corner'
                    br_w = abs(corners[2].x() - corners[0].x())
                    br_h = abs(corners[2].y() - corners[0].y())
                    tip = window.format_coordinates(
                        width=br_w, height=br_h, x=pos.x(), y=pos.y())
                    tip += f'  |  {mode}/{origin}'
                    if force_circle:
                        tip += '  (' + self._tr(
                            'canvasShiftFromCenter', 'Shift=from center') + ')'
                    self.parent().window().label_coordinates.setText(tip)
                else:
                    current_width = abs(self.current[0].x() - pos.x())
                    current_height = abs(self.current[0].y() - pos.y())
                    self.parent().window().label_coordinates.setText(
                        window.format_coordinates(
                            width=current_width, height=current_height,
                            x=pos.x(), y=pos.y()))
                    if self.draw_square:
                        init_pos = self.current[0]
                        min_x = init_pos.x()
                        min_y = init_pos.y()
                        min_size = min(abs(pos.x() - min_x), abs(pos.y() - min_y))
                        direction_x = -1 if pos.x() - min_x < 0 else 1
                        direction_y = -1 if pos.y() - min_y < 0 else 1
                        self.line[1] = QPointF(
                            min_x + direction_x * min_size,
                            min_y + direction_y * min_size)
                    else:
                        self.line[1] = pos

                self.line.line_color = color
                self.prev_point = QPointF()
                if not (self.is_polygon_drawing() and len(self.current) > 1
                        and self.close_enough(pos, self.current[0])):
                    self.current.highlight_clear()
            else:
                self.prev_point = pos
            self.repaint()
            return

        # Polygon copy moving.
        if Qt.MouseButton.RightButton & ev.buttons():
            if self.selected_shape_copy and self.prev_point:
                self.override_cursor(CURSOR_MOVE)
                self.bounded_move_shape(self.selected_shape_copy, pos)
                self.repaint()
            elif self.selected_shape:
                self.selected_shape_copy = self.selected_shape.copy()
                self.repaint()
            return

        # Polygon/Vertex/Keypoint moving.
        if Qt.MouseButton.LeftButton & ev.buttons():
            if self.selected_keypoint() and self.h_shape is not None:
                if self.out_of_pixmap(pos):
                    size = self.pixmap.size()
                    pos = QPointF(
                        min(max(0, pos.x()), size.width()),
                        min(max(0, pos.y()), size.height()),
                    )
                self._emit_edit_about_to_begin_once()
                self.h_shape.move_keypoint_to(self.h_keypoint, pos)
                self.shapeMoved.emit()
                self.repaint()
                return
            if self.selected_vertex():
                self._emit_edit_about_to_begin_once()
                self._last_edit_pos = pos
                self.bounded_move_vertex(pos)
                self.shapeMoved.emit()
                self.repaint()

                # Display annotation width and height while moving vertex
                br = self.h_shape.bounding_rect()
                tip = window.format_coordinates(
                    width=br.width(), height=br.height(),
                    x=pos.x(), y=pos.y())
                if getattr(self.h_shape, 'shape_type', None) == 'circle':
                    tip += '  |  ' + self._tr(
                        'canvasShiftFromCenter', 'Shift=from center')
                self.parent().window().label_coordinates.setText(tip)
            elif self.selected_shape and self.prev_point:
                self._emit_edit_about_to_begin_once()
                self.override_cursor(CURSOR_MOVE)
                self.bounded_move_shape(self.selected_shape, pos)
                self.shapeMoved.emit()
                self.repaint()

                # Display annotation width and height while moving shape
                point1 = self.selected_shape[1]
                point3 = self.selected_shape[3]
                current_width = abs(point1.x() - point3.x())
                current_height = abs(point1.y() - point3.y())
                self.parent().window().label_coordinates.setText(
                        window.format_coordinates(width=current_width, height=current_height, x=pos.x(), y=pos.y()))
            else:
                # pan
                delta = ev.pos() - self.pan_initial_pos
                self.scrollRequest.emit(delta.x(), Qt.Orientation.Horizontal.value)
                self.scrollRequest.emit(delta.y(), Qt.Orientation.Vertical.value)
                self.update()
                return

        # Just hovering over the canvas:
        # - Highlight keypoints / vertices / shapes
        self.setToolTip(self._tr('canvasTipImage', 'Image'))
        priority_list = self.shapes + ([self.selected_shape] if self.selected_shape else [])
        for shape in reversed([s for s in priority_list if self.isVisible(s)]):
            kpt_index = shape.nearest_keypoint(pos, self.epsilon) if shape.keypoints else None
            if kpt_index is not None:
                if self.h_shape:
                    self.h_shape.highlight_clear()
                self.h_keypoint, self.h_vertex, self.h_shape = kpt_index, None, shape
                shape.highlight_keypoint(kpt_index)
                self.override_cursor(CURSOR_POINT)
                kname = ''
                if shape.keypoint_names and kpt_index < len(shape.keypoint_names):
                    kname = shape.keypoint_names[kpt_index]
                self.setToolTip(self._tr(
                    'canvasTipKeypoint',
                    "Keypoint {0} — drag to move | H: visibility | Delete: clear point",
                    kname or ('#%d' % (kpt_index + 1)),
                ))
                self.setStatusTip(self.toolTip())
                self.update()
                break

            # Ellipse/circle corners sit outside the curve — use larger hit radius
            v_eps = self.hit_epsilon()
            if getattr(shape, 'is_ellipse_like', lambda: False)():
                v_eps = max(v_eps, self.hit_epsilon() * 1.35)
            index = shape.nearest_vertex(pos, v_eps)
            if index is not None:
                if self.h_shape:
                    self.h_shape.highlight_clear()
                self.h_vertex, self.h_shape = index, shape
                self.h_keypoint = None
                shape.highlight_vertex(index, shape.MOVE_VERTEX)
                self.override_cursor(CURSOR_POINT)
                self.setToolTip(self._tr('canvasTipResize', 'Click & drag to resize'))
                self.setStatusTip(self.toolTip())
                self.update()
                break
            elif shape.contains_point(pos):
                if self.h_shape:
                    self.h_shape.highlight_clear()
                self.h_vertex, self.h_shape = None, shape
                self.h_keypoint = None
                self.setToolTip(self._tr(
                    'canvasTipMoveShape',
                    "Click & drag to move shape '{0}'",
                    shape.label,
                ))
                self.setStatusTip(self.toolTip())
                self.override_cursor(CURSOR_GRAB)
                self.update()

                # Display annotation width and height while hovering inside
                br = self.h_shape.bounding_rect()
                self.parent().window().label_coordinates.setText(
                    window.format_coordinates(
                        width=br.width(), height=br.height(),
                        x=pos.x(), y=pos.y()))
                break
        else:  # Nothing found, clear highlights, reset state.
            if self.h_shape:
                self.h_shape.highlight_clear()
                self.update()
            self.h_vertex, self.h_shape = None, None
            self.h_keypoint = None
            self.override_cursor(CURSOR_DEFAULT)

    def mousePressEvent(self, ev):
        pos = self.transform_pos(ev.pos())

        if ev.button() == Qt.MouseButton.LeftButton:
            if self.placing_keypoints:
                self.editAboutToBegin.emit()
                self._place_keypoint_at(pos)
            elif self.drawing():
                self.handle_drawing(pos)
            else:
                selection = self.select_shape_point(pos)
                self.prev_point = pos

                if selection is None:
                    # pan
                    QApplication.setOverrideCursor(QCursor(Qt.CursorShape.OpenHandCursor))
                    self.pan_initial_pos = ev.pos()

        elif ev.button() == Qt.MouseButton.RightButton and self.editing():
            if self.placing_keypoints:
                # Right-click while placing: cycle visibility of last placed point
                shape = self.pose_target_shape
                if shape and shape.keypoints:
                    self.editAboutToBegin.emit()
                    shape.cycle_keypoint_visibility(len(shape.keypoints) - 1)
                    self.shapeMoved.emit()
            else:
                self.select_shape_point(pos)
                self.prev_point = pos
        self.update()

    def _emit_edit_about_to_begin_once(self):
        if not self._gesture_undo_emitted:
            self.editAboutToBegin.emit()
            self._gesture_undo_emitted = True

    def _place_keypoint_at(self, pos):
        if not self.placing_keypoints or not self.pose_target_shape:
            return
        if self.out_of_pixmap(pos):
            size = self.pixmap.size()
            pos = QPointF(
                min(max(0, pos.x()), size.width()),
                min(max(0, pos.y()), size.height()),
            )
        self.pose_target_shape.add_keypoint(pos.x(), pos.y(), v=2)
        placed = len(self.pose_target_shape.keypoints)
        if placed >= self.expected_kpt_count:
            self.placing_keypoints = False
            self.pose_target_shape = None
            self.expected_kpt_count = 0
            self.pose_keypoint_names = []
            self.restore_cursor()
            self.keypointPlacementFinished.emit()
        else:
            name = (self.pose_keypoint_names[placed]
                    if placed < len(self.pose_keypoint_names) else str(placed))
            self.keypointPlacementProgress.emit(placed, self.expected_kpt_count, name)
        self.shapeMoved.emit()
        self.update()

    def mouseReleaseEvent(self, ev):
        if ev.button() == Qt.MouseButton.RightButton:
            menu = self.menus[bool(self.selected_shape_copy)]
            self.restore_cursor()
            # In PySide6/Qt6, use exec() instead of exec_()
            if not menu.exec(self.mapToGlobal(ev.pos()))\
               and self.selected_shape_copy:
                # Cancel the move by deleting the shadow copy.
                self.selected_shape_copy = None
                self.repaint()
            self._gesture_undo_emitted = False
            self._clear_ellipse_edit_anchors()
            self.editGestureFinished.emit()
        elif ev.button() == Qt.MouseButton.LeftButton and self.selected_shape:
            if self.selected_vertex():
                self.override_cursor(CURSOR_POINT)
            else:
                self.override_cursor(CURSOR_GRAB)
            self._gesture_undo_emitted = False
            self._clear_ellipse_edit_anchors()
            self.editGestureFinished.emit()
        elif ev.button() == Qt.MouseButton.LeftButton:
            pos = self.transform_pos(ev.pos())
            # Rectangle/pose finish on mouse release; polygon adds on press only
            if self.drawing() and not self.is_polygon_drawing():
                self.handle_drawing(pos)
            else:
                # pan
                QApplication.restoreOverrideCursor()
            self._gesture_undo_emitted = False
            self._clear_ellipse_edit_anchors()
            self.editGestureFinished.emit()

    def end_move(self, copy=False):
        assert self.selected_shape and self.selected_shape_copy
        shape = self.selected_shape_copy
        # del shape.fill_color
        # del shape.line_color
        if copy:
            self.shapes.append(shape)
            self.selected_shape.selected = False
            self.selected_shape = shape
            self.repaint()
        else:
            self.selected_shape.points = [p for p in shape.points]
            self.selected_shape.keypoints = [dict(k) for k in shape.keypoints]
        self.selected_shape_copy = None

    def hide_background_shapes(self, value):
        self.hide_background = value
        if self.selected_shape:
            # Only hide other shapes if there is a current selection.
            # Otherwise the user will not be able to select a shape.
            self.set_hiding(True)
            self.repaint()

    def handle_drawing(self, pos):
        if self.is_polygon_drawing() or (
                self.current and getattr(self.current, 'shape_type', None) == 'polygon'):
            self._handle_polygon_drawing(pos)
            return

        if self.is_ellipse_drawing() or (
                self.current and getattr(self.current, 'shape_type', None) in (
                    'ellipse', 'circle')):
            self._handle_ellipse_drawing(pos)
            return

        if self.current and self.current.reach_max_points() is False:
            init_pos = self.current[0]
            min_x = init_pos.x()
            min_y = init_pos.y()
            target_pos = self.line[1]
            max_x = target_pos.x()
            max_y = target_pos.y()
            self.current.add_point(QPointF(max_x, min_y))
            self.current.add_point(target_pos)
            self.current.add_point(QPointF(min_x, max_y))
            self.finalise()
        elif not self.out_of_pixmap(pos):
            self.current = Shape()
            self.current.add_point(pos)
            self.line.points = [pos, pos]
            self.set_hiding()
            self.drawingPolygon.emit(True)
            self.update()

    def _handle_ellipse_drawing(self, pos):
        """Drag-to-draw ellipse or circle tool (type fixed by create_shape_type)."""
        if self.out_of_pixmap(pos) and self.current is None:
            return
        if self.out_of_pixmap(pos):
            size = self.pixmap.size()
            pos = QPointF(
                min(max(0, pos.x()), size.width()),
                min(max(0, pos.y()), size.height()),
            )

        oval_type = 'circle' if self.create_shape_type == 'circle' else 'ellipse'
        if self.current and self.current.reach_max_points() is False:
            force_circle = self._oval_force_circle()
            from_center = self._oval_from_center()
            corners = self._drag_rect_corners(
                self.current[0], pos, force_circle, from_center)
            # Reject near-degenerate shapes
            if (abs(corners[2].x() - corners[0].x()) < 1.5
                    or abs(corners[2].y() - corners[0].y()) < 1.5):
                self.current = None
                self.drawingPolygon.emit(False)
                self.update()
                return
            self.current.points = list(corners)
            self.current.shape_type = oval_type
            self.finalise()
        else:
            self.current = Shape(shape_type=oval_type)
            self.current.add_point(pos)
            self.line.points = [pos, pos]
            self.set_hiding()
            self.drawingPolygon.emit(True)
            self.update()

    def _handle_polygon_drawing(self, pos):
        """Click-to-add vertices; close by first-vertex / Enter / double-click."""
        if self.out_of_pixmap(pos):
            size = self.pixmap.size()
            pos = QPointF(
                min(max(0, pos.x()), size.width()),
                min(max(0, pos.y()), size.height()),
            )

        if self.current is None:
            self.current = Shape(shape_type='polygon')
            self.current.add_point(pos)
            self.line.points = [pos, pos]
            self.set_hiding()
            self.drawingPolygon.emit(True)
            self.update()
            return

        # Close when clicking near the first vertex (≥3 verts)
        if len(self.current) >= 3 and self.close_enough(pos, self.current[0]):
            self.finalise()
            return

        # Ignore accidental duplicate click on last vertex
        if self.close_enough(pos, self.current[-1]):
            return

        self.current.add_point(pos)
        self.line.points = [self.current[-1], pos]
        self.update()

    def set_hiding(self, enable=True):
        self._hide_background = self.hide_background if enable else False

    def can_close_shape(self):
        return self.drawing() and self.current and len(self.current) > 2

    def mouseDoubleClickEvent(self, ev):
        # Check if double-clicked on an existing shape
        pos = self.transform_pos(ev.pos())
        if not self.drawing():
            for shape in reversed(self.shapes):
                if self.isVisible(shape) and shape.contains_point(pos):
                    # Double-clicked on a shape, emit signal to edit label
                    self.select_shape(shape)
                    self.shapeDoubleClicked.emit()
                    return

        # Polygon: mousePress already added a point for the first click of the
        # double-click — drop it, then close if we have ≥3 vertices.
        if self.is_polygon_drawing() and self.current is not None:
            if len(self.current) > 2:
                self.current.pop_point()
            if len(self.current) >= 3:
                self.finalise()
            return

        # Legacy path (non-polygon): need ≥4 because press adds one first
        if self.can_close_shape() and len(self.current) > 3:
            self.current.pop_point()
            self.finalise()

    def select_shape(self, shape):
        self.de_select_shape()
        shape.selected = True
        self.selected_shape = shape
        self.set_hiding()
        self.selectionChanged.emit(True)
        self.update()

    def select_shape_point(self, point):
        """Select the first shape created which contains this point."""
        self.de_select_shape()
        if self.selected_keypoint():  # A pose keypoint is marked for selection.
            index, shape = self.h_keypoint, self.h_shape
            shape.highlight_keypoint(index)
            self.select_shape(shape)
            return self.h_keypoint
        if self.selected_vertex():  # A vertex is marked for selection.
            index, shape = self.h_vertex, self.h_shape
            shape.highlight_vertex(index, shape.MOVE_VERTEX)
            self.select_shape(shape)
            return self.h_vertex
        # Prefer ellipse/circle bbox corners over body-move (corners are outside curve)
        for shape in reversed(self.shapes):
            if not self.isVisible(shape):
                continue
            if getattr(shape, 'is_ellipse_like', lambda: False)():
                index = shape.nearest_vertex(point, max(self.hit_epsilon() * 1.35, 16.0))
                if index is not None:
                    self.h_vertex, self.h_shape = index, shape
                    self.h_keypoint = None
                    shape.highlight_vertex(index, shape.MOVE_VERTEX)
                    self.select_shape(shape)
                    return self.h_vertex
        for shape in reversed(self.shapes):
            if self.isVisible(shape) and shape.contains_point(point):
                self.select_shape(shape)
                self.calculate_offsets(shape, point)
                return self.selected_shape
        return None

    def calculate_offsets(self, shape, point):
        rect = shape.bounding_rect()
        x1 = rect.x() - point.x()
        y1 = rect.y() - point.y()
        x2 = (rect.x() + rect.width()) - point.x()
        y2 = (rect.y() + rect.height()) - point.y()
        self.offsets = QPointF(x1, y1), QPointF(x2, y2)

    def snap_point_to_canvas(self, x, y):
        """
        Moves a point x,y to within the boundaries of the canvas.
        :return: (x,y,snapped) where snapped is True if x or y were changed, False if not.
        """
        if x < 0 or x > self.pixmap.width() or y < 0 or y > self.pixmap.height():
            x = max(x, 0)
            y = max(y, 0)
            x = min(x, self.pixmap.width())
            y = min(y, self.pixmap.height())
            return x, y, True

        return x, y, False

    def bounded_move_vertex(self, pos):
        index, shape = self.h_vertex, self.h_shape
        point = shape[index]
        if self.out_of_pixmap(pos):
            size = self.pixmap.size()
            clipped_x = min(max(0, pos.x()), size.width())
            clipped_y = min(max(0, pos.y()), size.height())
            pos = QPointF(clipped_x, clipped_y)

        # Ellipse/circle edit: type stays fixed; Shift=from-center only for circle
        if (getattr(shape, 'is_ellipse_like', lambda: False)()
                and len(shape.points) == 4):
            force_circle = self._oval_force_circle(shape)
            from_center = self._oval_from_center(shape=shape)
            if self._ellipse_edit_center is None or self._ellipse_edit_opp is None:
                br = shape.axis_aligned_rect()
                self._ellipse_edit_center = QPointF(br.center())
                # Opposite corner of the grabbed handle (stable for the gesture)
                self._ellipse_edit_opp = QPointF(shape.points[(index + 2) % 4])
                self._ellipse_edit_index = index
            anchor = self._ellipse_edit_center if from_center else self._ellipse_edit_opp
            shape.points = self._drag_rect_corners(
                anchor, pos, force_circle, from_center)
            # Never convert ellipse↔circle while editing
            # Keep highlight on the corner nearest the cursor after reorder
            near = shape.nearest_vertex(pos, 1e9)
            if near is not None:
                self.h_vertex = near
                shape.highlight_vertex(near, shape.MOVE_VERTEX)
            return

        if self.draw_square:
            opposite_point_index = (index + 2) % 4
            opposite_point = shape[opposite_point_index]

            min_size = min(abs(pos.x() - opposite_point.x()), abs(pos.y() - opposite_point.y()))
            direction_x = -1 if pos.x() - opposite_point.x() < 0 else 1
            direction_y = -1 if pos.y() - opposite_point.y() < 0 else 1
            shift_pos = QPointF(opposite_point.x() + direction_x * min_size - point.x(),
                                opposite_point.y() + direction_y * min_size - point.y())
        else:
            shift_pos = pos - point

        shape.move_vertex_by(index, shift_pos)

        # Axis-aligned bbox coupling only for 4-corner rectangle/pose boxes
        if (getattr(shape, 'shape_type', 'rectangle') == 'polygon'
                or len(shape.points) != 4):
            return

        left_index = (index + 1) % 4
        right_index = (index + 3) % 4
        if index % 2 == 0:
            right_shift = QPointF(shift_pos.x(), 0)
            left_shift = QPointF(0, shift_pos.y())
        else:
            left_shift = QPointF(shift_pos.x(), 0)
            right_shift = QPointF(0, shift_pos.y())
        shape.move_vertex_by(right_index, right_shift)
        shape.move_vertex_by(left_index, left_shift)

    def bounded_move_shape(self, shape, pos):
        if self.out_of_pixmap(pos):
            return False  # No need to move
        o1 = QPointF(pos.x() + self.offsets[0].x(), pos.y() + self.offsets[0].y())
        if self.out_of_pixmap(o1):
            pos = QPointF(pos.x() - min(0, o1.x()), pos.y() - min(0, o1.y()))
        o2 = QPointF(pos.x() + self.offsets[1].x(), pos.y() + self.offsets[1].y())
        if self.out_of_pixmap(o2):
            pos = QPointF(pos.x() + min(0, self.pixmap.width() - o2.x()),
                         pos.y() + min(0, self.pixmap.height() - o2.y()))
        # The next line tracks the new position of the cursor
        # relative to the shape, but also results in making it
        # a bit "shaky" when nearing the border and allows it to
        # go outside of the shape's area for some reason. XXX
        # self.calculateOffsets(self.selectedShape, pos)
        dp = QPointF(pos.x() - self.prev_point.x(), pos.y() - self.prev_point.y())
        if dp.x() != 0 or dp.y() != 0:
            shape.move_by(dp)
            self.prev_point = pos
            return True
        return False

    def de_select_shape(self):
        if self.selected_shape:
            self.selected_shape.selected = False
            self.selected_shape = None
            self.set_hiding(False)
            self.selectionChanged.emit(False)
            self.update()

    def delete_selected(self):
        if self.selected_shape:
            shape = self.selected_shape
            self.un_highlight(shape)
            self.shapes.remove(self.selected_shape)
            self.selected_shape = None
            self.update()
            return shape

    def copy_selected_shape(self):
        if self.selected_shape:
            shape = self.selected_shape.copy()
            self.de_select_shape()
            self.shapes.append(shape)
            shape.selected = True
            self.selected_shape = shape
            self.bounded_shift_shape(shape)
            return shape

    def bounded_shift_shape(self, shape):
        # Try to move in one direction, and if it fails in another.
        # Give up if both fail.
        point = shape[0]
        offset = QPointF(2.0, 2.0)
        self.calculate_offsets(shape, point)
        self.prev_point = point
        # In PySide6/Qt6, use explicit coordinate arithmetic
        pos_minus = QPointF(point.x() - offset.x(), point.y() - offset.y())
        pos_plus = QPointF(point.x() + offset.x(), point.y() + offset.y())
        if not self.bounded_move_shape(shape, pos_minus):
            self.bounded_move_shape(shape, pos_plus)

    def paintEvent(self, event):
        if not self.pixmap:
            return super(Canvas, self).paintEvent(event)

        p = self._painter
        p.begin(self)
        p.setRenderHint(QPainter.Antialiasing)
        # In Qt6/PySide6, HighQualityAntialiasing is removed, Antialiasing is sufficient
        # p.setRenderHint(QPainter.HighQualityAntialiasing)
        p.setRenderHint(QPainter.SmoothPixmapTransform)

        p.scale(self.scale, self.scale)
        p.translate(self.offset_to_center())

        temp = self.pixmap
        if self.overlay_color:
            temp = QPixmap(self.pixmap)
            painter = QPainter(temp)
            # In PySide6/Qt6, CompositionMode enum uses nested naming
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Overlay)
            painter.fillRect(temp.rect(), self.overlay_color)
            painter.end()

        p.drawPixmap(0, 0, temp)
        Shape.scale = self.scale
        Shape.label_font_size = self.label_font_size
        for shape in self.shapes:
            if (shape.selected or not self._hide_background) and self.isVisible(shape):
                # While placing pose keypoints, never fill the active box
                if self.placing_keypoints and shape is self.pose_target_shape:
                    shape.fill = False
                else:
                    shape.fill = shape.selected or shape == self.h_shape
                shape.paint(p)
        if self.current and not self.is_ellipse_drawing():
            # Never fill while dragging a new box — outline only
            # Ellipse uses dedicated preview (skip diagonal rubber-band)
            self.current.fill = False
            self.line.fill = False
            self.current.paint(p)
            self.line.paint(p)
        if self.selected_shape_copy:
            self.selected_shape_copy.paint(p)

        # Rect / ellipse preview while drag-drawing; polygon uses polyline
        if (self.current is not None and len(self.line) == 2
                and not self.is_polygon_drawing()):
            left_top = self.line[0]
            right_bottom = self.line[1]
            rect_width = right_bottom.x() - left_top.x()
            rect_height = right_bottom.y() - left_top.y()
            under = QPen(QColor(255, 255, 255, 180))
            under.setWidth(max(3, int(round(4.0 / self.scale))))
            p.setPen(under)
            p.setBrush(Qt.BrushStyle.NoBrush)
            draw = p.drawEllipse if self.is_ellipse_drawing() else p.drawRect
            draw(int(left_top.x()), int(left_top.y()), int(rect_width), int(rect_height))
            pen = QPen(self.drawing_rect_color)
            pen.setWidth(max(2, int(round(2.5 / self.scale))))
            p.setPen(pen)
            fill = QColor(self.drawing_rect_color)
            fill.setAlpha(28)
            p.setBrush(QBrush(fill))
            draw(int(left_top.x()), int(left_top.y()), int(rect_width), int(rect_height))
        elif self.is_polygon_drawing() and self.current is not None and len(self.current) >= 2:
            # Soft fill preview for in-progress polygon
            path = self.current.make_path()
            if len(self.line) == 2:
                path.lineTo(self.line[1])
            fill = QColor(self.drawing_rect_color)
            fill.setAlpha(28)
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QBrush(fill))
            p.drawPath(path)

        if (self.drawing() or self.placing_keypoints) and not self.prev_point.isNull() \
                and not self.out_of_pixmap(self.prev_point):
            p.setPen(QColor(0, 0, 0))
            p.drawLine(int(self.prev_point.x()), 0, int(self.prev_point.x()), int(self.pixmap.height()))
            p.drawLine(0, int(self.prev_point.y()), int(self.pixmap.width()), int(self.prev_point.y()))

        self.setAutoFillBackground(True)
        if self.verified:
            pal = self.palette()
            pal.setColor(self.backgroundRole(), QColor(184, 239, 38, 128))
            self.setPalette(pal)
        else:
            pal = self.palette()
            pal.setColor(self.backgroundRole(), QColor(232, 232, 232, 255))
            self.setPalette(pal)

        p.end()

    def transform_pos(self, point):
        """Convert from widget-logical coordinates to painter-logical coordinates."""
        # In PySide6/Qt6, QPoint/QPointF arithmetic operations work differently
        offset = self.offset_to_center()
        return QPointF(point.x() / self.scale - offset.x(), 
                      point.y() / self.scale - offset.y())

    def offset_to_center(self):
        s = self.scale
        area = super(Canvas, self).size()
        if not self.pixmap:
            return QPointF(0, 0)
        w, h = self.pixmap.width() * s, self.pixmap.height() * s
        aw, ah = area.width(), area.height()
        x = (aw - w) / (2 * s) if aw > w else 0
        y = (ah - h) / (2 * s) if ah > h else 0
        return QPointF(x, y)

    def out_of_pixmap(self, p):
        if not self.pixmap:
            return True
        w, h = self.pixmap.width(), self.pixmap.height()
        return not (0 <= p.x() <= w and 0 <= p.y() <= h)

    def finalise(self):
        assert self.current
        if self.current.points[0] == self.current.points[-1]:
            self.current = None
            self.drawingPolygon.emit(False)
            self.update()
            return

        self.current.close()
        self.shapes.append(self.current)
        self.current = None
        self.set_hiding(False)
        self.drawingPolygon.emit(False)
        self.newShape.emit()
        self.update()

    def close_enough(self, p1, p2):
        # d = distance(p1 - p2)
        # m = (p1-p2).manhattanLength()
        # print "d %.2f, m %d, %.2f" % (d, m, d - m)
        # In PySide6/Qt6, use explicit coordinate arithmetic
        diff = QPointF(p1.x() - p2.x(), p1.y() - p2.y())
        return distance(diff) < self.epsilon

    # These two, along with a call to adjustSize are required for the
    # scroll area.
    def sizeHint(self):
        return self.minimumSizeHint()

    def minimumSizeHint(self):
        if self.pixmap:
            return self.scale * self.pixmap.size()
        return super(Canvas, self).minimumSizeHint()

    def wheelEvent(self, ev):
        qt_version = 4 if hasattr(ev, "delta") else 5
        if qt_version == 4:
            # In PySide6/Qt6, use Qt.Orientation enum
            if ev.orientation() == Qt.Orientation.Vertical:
                v_delta = ev.delta()
                h_delta = 0
            else:
                h_delta = ev.delta()
                v_delta = 0
        else:
            delta = ev.angleDelta()
            h_delta = delta.x()
            v_delta = delta.y()

        mods = ev.modifiers()
        # In PySide6/Qt6, use .value to get int from enum, and & for bit check
        if (mods & Qt.KeyboardModifier.ControlModifier) and (mods & Qt.KeyboardModifier.ShiftModifier) and v_delta:
            self.lightRequest.emit(v_delta)
        elif (mods & Qt.KeyboardModifier.ControlModifier) and v_delta:
            self.zoomRequest.emit(v_delta)
        else:
            v_delta and self.scrollRequest.emit(v_delta, Qt.Orientation.Vertical.value)
            h_delta and self.scrollRequest.emit(h_delta, Qt.Orientation.Horizontal.value)
        ev.accept()

    def keyPressEvent(self, ev):
        key = ev.key()
        if key == Qt.Key_Escape and self.placing_keypoints:
            # Stop keypoint placement but keep bbox / already placed points
            self.cancel_keypoint_placement()
            self.keypointPlacementFinished.emit()
            self.shapeMoved.emit()
            self.update()
        elif key == Qt.Key_Escape and self.current:
            print('ESC press')
            self.current = None
            self.drawingPolygon.emit(False)
            self.update()
        elif key == Qt.Key_Shift:
            # Live-update circle from-center preview/edit only
            if (self.is_ellipse_drawing() and self.create_shape_type == 'circle'
                    and self.current is not None):
                self.update()
            elif (self.selected_vertex() and self.h_shape
                  and getattr(self.h_shape, 'shape_type', None) == 'circle'
                  and self._last_edit_pos is not None):
                self.bounded_move_vertex(self._last_edit_pos)
                self.shapeMoved.emit()
                self.update()
        elif (key in (Qt.Key_Backspace, Qt.Key_Delete)
              and self.is_polygon_drawing() and self.current is not None):
            # Undo last polygon vertex while drawing
            if len(self.current) > 1:
                self.current.pop_point()
                cursor = self.line[1] if len(self.line) > 1 else self.current[-1]
                self.line.points = [self.current[-1], cursor]
            else:
                self.current = None
                self.drawingPolygon.emit(False)
            self.update()
        elif key in (Qt.Key_Backspace, Qt.Key_Delete) and self.placing_keypoints:
            # Undo last placed keypoint while annotating
            shape = self.pose_target_shape
            if shape and shape.keypoints:
                self.editAboutToBegin.emit()
                if shape.remove_last_keypoint() is not None:
                    placed = len(shape.keypoints)
                    name = (self.pose_keypoint_names[placed]
                            if placed < len(self.pose_keypoint_names) else str(placed))
                    self.keypointPlacementProgress.emit(placed, self.expected_kpt_count, name)
                    self.shapeMoved.emit()
                    self.update()
        elif key in (Qt.Key_Backspace, Qt.Key_Delete) and self.selected_keypoint() and self.h_shape:
            # Clear selected keypoint slot (keep order; v=0 for YOLO-Pose)
            self.editAboutToBegin.emit()
            if self.h_shape.clear_keypoint(self.h_keypoint):
                self.shapeMoved.emit()
                self.update()
        elif key == Qt.Key_H and self.selected_shape and self.selected_keypoint():
            # H = hide/visibility cycle (V is reserved for Verify Image)
            self.editAboutToBegin.emit()
            self.selected_shape.cycle_keypoint_visibility(self.h_keypoint)
            self.shapeMoved.emit()
            self.update()
        elif key == Qt.Key_H and self.placing_keypoints and self.pose_target_shape \
                and self.pose_target_shape.keypoints:
            # While placing: cycle visibility of the last placed keypoint
            self.editAboutToBegin.emit()
            idx = len(self.pose_target_shape.keypoints) - 1
            self.pose_target_shape.cycle_keypoint_visibility(idx)
            self.shapeMoved.emit()
            self.update()
        elif key == Qt.Key_Return and self.can_close_shape():
            self.finalise()
        elif key == Qt.Key_Left and self.selected_shape:
            self.move_one_pixel('Left')
        elif key == Qt.Key_Right and self.selected_shape:
            self.move_one_pixel('Right')
        elif key == Qt.Key_Up and self.selected_shape:
            self.move_one_pixel('Up')
        elif key == Qt.Key_Down and self.selected_shape:
            self.move_one_pixel('Down')

    def keyReleaseEvent(self, ev):
        if ev.key() in (Qt.Key_Left, Qt.Key_Right, Qt.Key_Up, Qt.Key_Down):
            self._gesture_undo_emitted = False
            self.editGestureFinished.emit()
        # Refresh circle from-center preview/edit when Shift released
        if ev.key() == Qt.Key_Shift:
            if (self.is_ellipse_drawing() and self.create_shape_type == 'circle'
                    and self.current is not None):
                self.update()
            elif (self.selected_vertex() and self.h_shape
                  and getattr(self.h_shape, 'shape_type', None) == 'circle'
                  and self._last_edit_pos is not None):
                self.bounded_move_vertex(self._last_edit_pos)
                self.shapeMoved.emit()
                self.update()
        super(Canvas, self).keyReleaseEvent(ev)

    def move_one_pixel(self, direction):
        step = {
            'Left': QPointF(-1.0, 0),
            'Right': QPointF(1.0, 0),
            'Up': QPointF(0, -1.0),
            'Down': QPointF(0, 1.0),
        }.get(direction)
        if step is None or self.move_out_of_bound(step):
            return
        self._emit_edit_about_to_begin_once()
        self.selected_shape.move_by(step)
        self.shapeMoved.emit()
        self.repaint()

    def move_out_of_bound(self, step):
        points = [
            QPointF(p.x() + step.x(), p.y() + step.y())
            for p in self.selected_shape.points
        ]
        return True in map(self.out_of_pixmap, points)

    def set_last_label(self, text, line_color=None, fill_color=None):
        assert text
        self.shapes[-1].label = text
        if line_color:
            self.shapes[-1].line_color = line_color

        if fill_color:
            self.shapes[-1].fill_color = fill_color

        return self.shapes[-1]

    def undo_last_line(self):
        assert self.shapes
        self.current = self.shapes.pop()
        self.current.set_open()
        self.line.points = [self.current[-1], self.current[0]]
        self.drawingPolygon.emit(True)

    def reset_all_lines(self):
        assert self.shapes
        self.current = self.shapes.pop()
        self.current.set_open()
        self.line.points = [self.current[-1], self.current[0]]
        self.drawingPolygon.emit(True)
        self.current = None
        self.drawingPolygon.emit(False)
        self.update()

    def load_pixmap(self, pixmap):
        self.pixmap = pixmap
        self.shapes = []
        self.repaint()

    def load_shapes(self, shapes):
        self.shapes = list(shapes)
        self.current = None
        self.repaint()

    def set_shape_visible(self, shape, value):
        self.visible[shape] = value
        self.repaint()

    def current_cursor(self):
        cursor = QApplication.overrideCursor()
        if cursor is not None:
            cursor = cursor.shape()
        return cursor

    def override_cursor(self, cursor):
        self._cursor = cursor
        if self.current_cursor() is None:
            QApplication.setOverrideCursor(cursor)
        else:
            QApplication.changeOverrideCursor(cursor)

    def restore_cursor(self):
        QApplication.restoreOverrideCursor()

    def reset_state(self):
        self.de_select_shape()
        self.un_highlight()
        self.selected_shape_copy = None

        self.restore_cursor()
        self.pixmap = None
        self.update()

    def set_drawing_shape_to_square(self, status):
        self.draw_square = status
