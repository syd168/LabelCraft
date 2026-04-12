#!/bin/bash
###############################################################################
# Build LabelCraft for Linux
# Creates a standalone executable using PyInstaller
###############################################################################

set -e  # Exit on error

echo "========================================="
echo "Building LabelCraft for Linux"
echo "========================================="

# Get the project root directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

# Check if PyInstaller is installed
if ! command -v pyinstaller &> /dev/null; then
    echo "PyInstaller not found. Installing..."
    pip install pyinstaller
fi

# Check for libbrotli issue and provide workaround
echo "Checking system libraries..."
if ldconfig -p | grep -q libbrotlidec; then
    BROTLI_VERSION=$(ldconfig -p | grep libbrotlidec | head -n1 | awk '{print $NF}')
    echo "Found libbrotlidec: $BROTLI_VERSION"
    
    # Test if the library works
    if ! python3 -c "from PySide6 import QtNetwork" 2>/dev/null; then
        echo "WARNING: libbrotlidec library issue detected!"
        echo "This is a known issue with PySide6 and older libbrotli versions."
        echo ""
        echo "Solutions:"
        echo "1. Update libbrotli: sudo apt-get install --reinstall libbrotli1"
        echo "2. Use conda: conda install -c conda-forge brotli"
        echo "3. Continue with QtNetwork excluded (recommended for LabelCraft)"
        echo ""
        echo "Continuing build with QtNetwork excluded..."
    fi
fi

# Clean previous builds
echo "Cleaning previous builds..."
rm -rf build dist LabelCraft.spec

# Build with PyInstaller
echo "Building executable..."
pyinstaller --name=LabelCraft \
    --onefile \
    --windowed \
    --add-data="resources:resources" \
    --add-data="data:data" \
    --add-data="libs:libs" \
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
    --collect-submodules=xml \
    --icon=resources/icons/app.png \
    main.py

# Create distribution package
VERSION=$(python3 -c "from libs import __version__; print(__version__)" 2>/dev/null || echo "latest")
DIST_DIR="dist/linux_LabelCraft_${VERSION}"

echo "Creating distribution package..."
mkdir -p "$DIST_DIR"
cp dist/LabelCraft "$DIST_DIR/"
cp -r data "$DIST_DIR/" 2>/dev/null || true
cp README.md "$DIST_DIR/" 2>/dev/null || true

# Create a launcher script
cat > "$DIST_DIR/LabelCraft.sh" << 'EOF'
#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec "$SCRIPT_DIR/LabelCraft" "$@"
EOF
chmod +x "$DIST_DIR/LabelCraft.sh"

# Create archive
cd dist
tar czf "linux_LabelCraft_${VERSION}.tar.gz" "linux_LabelCraft_${VERSION}"
cd ..

echo "========================================="
echo "Build completed successfully!"
echo "Executable: dist/LabelCraft"
echo "Package: dist/linux_LabelCraft_${VERSION}.tar.gz"
echo "========================================="
