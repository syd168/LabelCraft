#!/bin/bash
###############################################################################
# Build LabelCraft for Windows (from Linux using Wine)
# This script uses Wine to run Windows Python and PyInstaller
###############################################################################

set -e  # Exit on error

echo "========================================="
echo "Building LabelCraft for Windows (via Wine)"
echo "========================================="

# Get the project root directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

# Check if Wine is installed
if ! command -v wine &> /dev/null; then
    echo "Error: Wine is not installed."
    echo "Please install Wine:"
    echo "  Ubuntu/Debian: sudo apt install wine64"
    echo "  Fedora: sudo dnf install wine"
    exit 1
fi

# Check if Windows Python is installed in Wine
WINE_PYTHON="$HOME/.wine/drive_c/Python311/python.exe"
if [ ! -f "$WINE_PYTHON" ]; then
    echo "Windows Python not found in Wine."
    echo "Please install Python 3.11 for Windows in Wine:"
    echo "  1. Download from https://www.python.org/downloads/"
    echo "  2. Run: wine python-3.11.x-amd64.exe"
    echo "  3. Install to default location (C:\Python311)"
    exit 1
fi

# Install PyInstaller in Wine if not present
echo "Checking PyInstaller in Wine..."
wine "$WINE_PYTHON" -m pip show pyinstaller > /dev/null 2>&1 || {
    echo "Installing PyInstaller in Wine..."
    wine "$WINE_PYTHON" -m pip install pyinstaller
}

# Install dependencies in Wine
echo "Installing dependencies in Wine..."
wine "$WINE_PYTHON" -m pip install PySide6 lxml

# Clean previous builds
echo "Cleaning previous builds..."
rm -rf build dist LabelCraft.spec

# Build with PyInstaller in Wine
echo "Building Windows executable..."
wine "$WINE_PYTHON" -m PyInstaller --name=LabelCraft \
    --onefile \
    --windowed \
    --add-data="resources;resources" \
    --add-data="data;data" \
    --add-data="libs;libs" \
    --hidden-import=PySide6 \
    --hidden-import=PySide6.QtCore \
    --hidden-import=PySide6.QtGui \
    --hidden-import=PySide6.QtWidgets \
    --exclude-module=PySide6.QtNetwork \
    --exclude-module=PySide6.QtWebEngineCore \
    --exclude-module=PySide6.QtWebEngineWidgets \
    --hidden-import=lxml \
    --hidden-import=lxml.etree \
    --hidden-import=xml.etree \
    --hidden-import=xml.etree.ElementTree \
    --hidden-import=json \
    --hidden-import=csv \
    --hidden-import=io \
    --hidden-import=codecs \
    --collect-submodules=xml \
    --icon=resources/icons/app.ico \
    main.py

# Create distribution package
VERSION=$(python3 -c "from libs import __version__; print(__version__)" 2>/dev/null || echo "latest")
DIST_DIR="dist/windows_LabelCraft_${VERSION}"

echo "Creating distribution package..."
mkdir -p "$DIST_DIR"
cp dist/LabelCraft.exe "$DIST_DIR/"
cp -r data "$DIST_DIR/" 2>/dev/null || true
cp README.md "$DIST_DIR/" 2>/dev/null || true

# Create archive
cd dist
zip -r "windows_LabelCraft_${VERSION}.zip" "windows_LabelCraft_${VERSION}"
cd ..

echo "========================================="
echo "Build completed successfully!"
echo "Executable: dist/LabelCraft.exe"
echo "Package: dist/windows_LabelCraft_${VERSION}.zip"
echo "========================================="
