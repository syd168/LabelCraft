#!/bin/bash
###############################################################################
# Build LabelCraft for PyPI
# Creates source distribution and wheel packages
###############################################################################

set -e  # Exit on error

echo "========================================="
echo "Building LabelCraft for PyPI"
echo "========================================="

# Get the project root directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

# Check required tools
for tool in python3 pip twine; do
    if ! command -v $tool &> /dev/null; then
        echo "Error: $tool is not installed."
        exit 1
    fi
done

# Install build dependencies
echo "Installing build dependencies..."
pip install --upgrade build twine wheel

# Clean previous builds
echo "Cleaning previous builds..."
rm -rf build dist *.egg-info

# Build source distribution and wheel
echo "Building packages..."
python3 -m build

# List created packages
echo ""
echo "Created packages:"
ls -lh dist/

# Optional: Upload to PyPI
echo ""
read -p "Do you want to upload to PyPI? (y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Uploading to PyPI..."
    twine upload dist/*
    echo "Upload completed!"
else
    echo "Packages created successfully. To upload manually:"
    echo "  twine upload dist/*"
fi

echo "========================================="
echo "Build completed successfully!"
echo "========================================="
