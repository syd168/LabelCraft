#!/bin/bash
###############################################################################
# Build LabelCraft for macOS
# Creates a macOS application bundle using PyInstaller
###############################################################################

set -e  # Exit on error

echo "========================================="
echo "Building LabelCraft for macOS"
echo "========================================="

# Get the project root directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

# Check if running on macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo "Warning: This script is designed for macOS."
    echo "You are running on: $OSTYPE"
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Check if PyInstaller is installed
if ! command -v pyinstaller &> /dev/null; then
    echo "PyInstaller not found. Installing..."
    pip install pyinstaller
fi

# Clean previous builds
echo "Cleaning previous builds..."
rm -rf build dist *.egg-info LabelCraft.spec

# Build with PyInstaller
echo "Building macOS application..."
pyinstaller --name=LabelCraft \
    --onedir \
    --windowed \
    --add-data="resources:resources" \
    --add-data="data:data" \
    --add-data="libs:libs" \
    --hidden-import=PySide6 \
    --hidden-import=PySide6.QtCore \
    --hidden-import=PySide6.QtGui \
    --hidden-import=PySide6.QtWidgets \
    --hidden-import=lxml \
    --hidden-import=lxml.etree \
    --hidden-import=xml.etree \
    --hidden-import=xml.etree.ElementTree \
    --hidden-import=json \
    --hidden-import=csv \
    --hidden-import=io \
    --hidden-import=codecs \
    --collect-submodules=xml \
    --icon=resources/icons/app.icns \
    main.py

# Create distribution package
VERSION=$(python3 -c "from libs import __version__; print(__version__)" 2>/dev/null || echo "latest")
DIST_DIR="dist/macOS_LabelCraft_${VERSION}"

echo "Creating distribution package..."
mkdir -p "$DIST_DIR"
cp -r dist/LabelCraft.app "$DIST_DIR/" 2>/dev/null || true
cp README.md "$DIST_DIR/" 2>/dev/null || true

# Create DMG (optional)
if command -v hdiutil &> /dev/null; then
    echo "Creating DMG file..."
    hdiutil create -volname "LabelCraft" \
        -srcfolder "$DIST_DIR" \
        -ov -format UDZO \
        "dist/macOS_LabelCraft_${VERSION}.dmg"
fi

# Create zip archive
cd dist
zip -r "macOS_LabelCraft_${VERSION}.zip" "macOS_LabelCraft_${VERSION}" 2>/dev/null || true
cd ..

echo "========================================="
echo "Build completed successfully!"
echo "Application: dist/LabelCraft.app"
echo "Package: dist/macOS_LabelCraft_${VERSION}.zip"
if [ -f "dist/macOS_LabelCraft_${VERSION}.dmg" ]; then
    echo "DMG: dist/macOS_LabelCraft_${VERSION}.dmg"
fi
echo "========================================="
