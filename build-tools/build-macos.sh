#!/bin/bash
###############################################################################
# Build LabelCraft for macOS
# Creates a macOS application bundle using py2app
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

# Check if py2app is installed
if ! python3 -m pip show py2app > /dev/null 2>&1; then
    echo "Installing py2app..."
    pip install py2app
fi

# Clean previous builds
echo "Cleaning previous builds..."
rm -rf build dist *.egg-info LabelCraft.spec

# Build with py2app
echo "Building macOS application..."
python3 setup.py py2app

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
