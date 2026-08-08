from math import sqrt
from libs.ustr import ustr
import hashlib
import os
import re
import sys

from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *


def filter_platform_argv(argv):
    """
    Remove OS-injected launch arguments that break argparse.

    macOS Finder/Dock injects -psn_* when launching GUI apps from .app bundles.
    """
    if not argv:
        return argv
    filtered = [argv[0]]
    for arg in argv[1:]:
        if arg.startswith('-psn_'):
            continue
        filtered.append(arg)
    return filtered


def _disabled_icon_pixmap(pix):
    """Same drawing as enabled, but gray + translucent so unavailable tools read clearly."""
    if pix is None or pix.isNull():
        return pix
    img = pix.toImage().convertToFormat(QImage.Format.Format_ARGB32)
    for y in range(img.height()):
        for x in range(img.width()):
            c = img.pixelColor(x, y)
            a = c.alpha()
            if a == 0:
                continue
            # Luma grayscale, then soften
            g = int(0.299 * c.red() + 0.587 * c.green() + 0.114 * c.blue())
            img.setPixelColor(x, y, QColor(g, g, g, max(0, int(a * 0.45))))
    return QPixmap.fromImage(img)


def new_icon(icon):
    """Load toolbar/menu icon.

    Normal/Active/Selected share one pixmap so hover does not swap artwork.
    Disabled uses a gray translucent variant so unavailable tools look inactive.
    """
    path = ':/' + icon
    base = QIcon(path)
    # Prefer a crisp size close to toolbar buttons; fall back to native.
    pix = base.pixmap(QSize(128, 128))
    if pix.isNull():
        pix = base.pixmap(QSize(48, 48))
    if pix.isNull():
        return base
    disabled = _disabled_icon_pixmap(pix)
    out = QIcon()
    for mode, p in (
        (QIcon.Mode.Normal, pix),
        (QIcon.Mode.Active, pix),
        (QIcon.Mode.Selected, pix),
        (QIcon.Mode.Disabled, disabled),
    ):
        out.addPixmap(p, mode, QIcon.State.Off)
        out.addPixmap(p, mode, QIcon.State.On)
    return out


def app_icon_file_path():
    """Filesystem path to app.png when present (source tree or packaged data)."""
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(root, 'resources', 'icons', 'app.png')


def load_app_pixmap():
    """
    Load app icon pixmap.

    Works for both source checkout (resources/icons/app.png) and pip installs
    (Qt resource :/app from libs/resources.py).
    """
    path = app_icon_file_path()
    if os.path.isfile(path):
        pix = QPixmap(path)
        if not pix.isNull():
            return pix
    pix = QPixmap(':/app')
    if not pix.isNull():
        return pix
    return QPixmap()


def app_icon():
    """
    Application icon with multiple sizes for taskbar / dock.

    Qt resource :/app alone is often a single huge pixmap; panels prefer
    16–256px entries. Also fall back to the on-disk PNG when available.
    """
    icon = QIcon()
    pix = load_app_pixmap()
    if pix.isNull():
        return new_icon('app')

    for size in (16, 24, 32, 48, 64, 128, 256):
        icon.addPixmap(_square_pixmap(pix, size))
    icon.addPixmap(pix)
    return icon


def _square_pixmap(pix, size):
    """Scale to an exact square size (taskbars expect N×N pixmaps)."""
    return pix.scaled(
        size, size,
        Qt.AspectRatioMode.IgnoreAspectRatio,
        Qt.TransformationMode.SmoothTransformation,
    )


def _linux_main_script_path():
    """Resolve LabelCraft/main.py for desktop Exec= entries (source tree)."""
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(root, 'main.py')


def _linux_exec_line():
    """
    Desktop Exec= for source runs and pip installs.

    Prefer the installed `labelcraft` script; otherwise fall back to
    `python main.py` in a source checkout.
    """
    import shutil

    which = shutil.which('labelcraft')
    if which:
        return f'"{which}" %F'

    # gui_scripts / direct launch: argv[0] may already be the wrapper
    argv0 = os.path.abspath(sys.argv[0]) if sys.argv else ''
    base = os.path.basename(argv0).lower()
    if argv0 and os.path.isfile(argv0) and base in ('labelcraft', 'labelcraft.exe'):
        return f'"{argv0}" %F'

    main_py = _linux_main_script_path()
    if os.path.isfile(main_py):
        return f'{sys.executable} "{main_py}" %F'

    # pip layout without a PATH entry (rare): invoke package entry point
    return f'{sys.executable} -c "from libs.cli import main; raise SystemExit(main())" %F'


def ensure_linux_desktop_integration(app_name='LabelCraft'):
    """
    Install a user-local .desktop + hicolor icons so Wayland/X11 docks can
    match the running window (via StartupWMClass / desktop-file-name) to
    LabelCraft's icon instead of a generic Python icon.

    Icon pixels come from disk PNG or embedded Qt resource :/app, so this
    also works after `pip install LabelCraft`.
    """
    if not sys.platform.startswith('linux'):
        return

    try:
        home = os.path.expanduser('~')
        apps_dir = os.path.join(home, '.local', 'share', 'applications')
        icons_root = os.path.join(home, '.local', 'share', 'icons', 'hicolor')
        desktop_path = os.path.join(apps_dir, 'labelcraft.desktop')

        os.makedirs(apps_dir, exist_ok=True)

        pix = load_app_pixmap()
        if pix.isNull():
            return

        icon_src = app_icon_file_path()
        for size in (16, 24, 32, 48, 64, 128, 256):
            size_dir = os.path.join(icons_root, f'{size}x{size}', 'apps')
            os.makedirs(size_dir, exist_ok=True)
            out = os.path.join(size_dir, 'labelcraft.png')
            refresh = not os.path.isfile(out)
            if not refresh and os.path.isfile(icon_src):
                refresh = os.path.getmtime(icon_src) > os.path.getmtime(out)
            if refresh:
                _square_pixmap(pix, size).save(out, 'PNG')

        exec_line = _linux_exec_line()
        desktop = (
            '[Desktop Entry]\n'
            'Type=Application\n'
            'Version=1.0\n'
            f'Name={app_name}\n'
            'GenericName=Image Annotation\n'
            'Comment=Graphical image annotation for object detection and pose\n'
            f'Exec={exec_line}\n'
            'Icon=labelcraft\n'
            'Terminal=false\n'
            'Categories=Graphics;Education;Science;\n'
            'StartupNotify=true\n'
            f'StartupWMClass={app_name}\n'
            'Keywords=annotation;yolo;pose;label;dataset;\n'
        )
        # Rewrite when Exec/path changed (e.g. different venv)
        need_write = True
        if os.path.isfile(desktop_path):
            try:
                with open(desktop_path, 'r', encoding='utf-8') as f:
                    need_write = f.read() != desktop
            except OSError:
                need_write = True
        if need_write:
            with open(desktop_path, 'w', encoding='utf-8') as f:
                f.write(desktop)
    except Exception as e:
        print(f'Warning: Linux desktop icon setup failed: {e}')


def configure_app_identity(app, app_name='LabelCraft'):
    """
    Set application identity so Linux/Windows taskbars show the real icon
    instead of a generic / Python icon.
    """
    app.setApplicationName(app_name)
    app.setApplicationDisplayName(app_name)
    app.setOrganizationName(app_name)
    # Matches labelcraft.desktop (basename without .desktop)
    try:
        app.setDesktopFileName('labelcraft')
    except Exception:
        pass

    icon = app_icon()
    app.setWindowIcon(icon)

    # Windows: without an AppUserModelID, explorer groups the process under
    # python.exe and shows the Python icon in the taskbar.
    if sys.platform.startswith('win'):
        try:
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
                f'{app_name}.App.1.0'
            )
        except Exception as e:
            print(f'Warning: failed to set AppUserModelID: {e}')
    elif sys.platform.startswith('linux'):
        ensure_linux_desktop_integration(app_name)

    return icon


def new_button(text, icon=None, slot=None):
    b = QPushButton(text)
    if icon is not None:
        b.setIcon(new_icon(icon))
    if slot is not None:
        b.clicked.connect(slot)
    return b


def new_action(parent, text, slot=None, shortcut=None, icon=None,
               tip=None, checkable=False, enabled=True):
    """Create a new action and assign callbacks, shortcuts, etc."""
    a = QAction(text, parent)
    if icon is not None:
        a.setIcon(new_icon(icon))
    if shortcut is not None:
        if isinstance(shortcut, (list, tuple)):
            a.setShortcuts(shortcut)
        else:
            a.setShortcut(shortcut)
    if tip is not None:
        a.setToolTip(tip)
        a.setStatusTip(tip)
    if slot is not None:
        a.triggered.connect(slot)
    if checkable:
        a.setCheckable(True)
    a.setEnabled(enabled)
    return a


def add_actions(widget, actions):
    for action in actions:
        if action is None:
            widget.addSeparator()
        elif isinstance(action, QMenu):
            widget.addMenu(action)
        else:
            widget.addAction(action)


def label_validator():
    from PySide6.QtGui import QRegularExpressionValidator
    from PySide6.QtCore import QRegularExpression
    return QRegularExpressionValidator(QRegularExpression(r'^[^ \t].+'), None)


class Struct(object):

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


def distance(p):
    return sqrt(p.x() * p.x() + p.y() * p.y())


def format_shortcut(text):
    mod, key = text.split('+', 1)
    return '<b>%s</b>+<b>%s</b>' % (mod, key)


def generate_color_by_text(text):
    s = ustr(text)
    hash_code = int(hashlib.sha256(s.encode('utf-8')).hexdigest(), 16)
    r = int((hash_code / 255) % 255)
    g = int((hash_code / 65025) % 255)
    b = int((hash_code / 16581375) % 255)
    return QColor(r, g, b, 40)


def have_qstring():
    """p3/qt5 get rid of QString wrapper as py3 has native unicode str type"""
    return False


def util_qt_strlistclass():
    return list


def natural_sort(list, key=lambda s:s):
    """
    Sort the list into natural alphanumeric order.
    """
    def get_alphanum_key_func(key):
        convert = lambda text: int(text) if text.isdigit() else text
        return lambda s: [convert(c) for c in re.split('([0-9]+)', key(s))]
    sort_key = get_alphanum_key_func(key)
    list.sort(key=sort_key)


# QT5/PySide6 uses strip method
def trimmed(text):
    return text.strip()
