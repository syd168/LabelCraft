#!/bin/bash

# LabelCraft Quick Start Script (Linux/macOS)
# This script will automatically create a virtual environment, install dependencies, and launch the application
# Usage:
#   ./start.sh           # Normal start
#   ./start.sh --rebuild # Force rebuild resource files

set -e  # Exit on error

echo "======================================"
echo "  LabelCraft - Image Annotation Tool"
echo "======================================"
echo ""

# Color definitions
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if force rebuild is requested
FORCE_REBUILD=false
if [[ "$1" == "--rebuild" || "$1" == "-r" ]]; then
    FORCE_REBUILD=true
    echo -e "${YELLOW}⚠ Force rebuild mode${NC}"
    rm -f libs/resources.py venv/.installed
fi

# Check if Python is installed
echo -e "${YELLOW}[1/5]${NC} Checking Python environment..."
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python3 not found${NC}"
    echo "Please install Python 3.8 or higher"
    echo "Download: https://www.python.org/downloads/"
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo -e "${GREEN}✓${NC} Python version: $PYTHON_VERSION"

# Check if Python version meets requirements
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 8 ]); then
    echo -e "${RED}Error: Python 3.8 or higher required${NC}"
    echo "Current version: $PYTHON_VERSION"
    exit 1
fi

# Check venv module
echo -e "${YELLOW}[2/5]${NC} Checking virtual environment module..."
if ! python3 -m venv --help &> /dev/null; then
    echo -e "${RED}Error: venv module not available${NC}"
    echo "Please install python3-venv package:"
    echo "  Ubuntu/Debian: sudo apt install python3-venv"
    echo "  CentOS/RHEL: sudo yum install python3-venv"
    echo "  macOS: Usually included in Python installer"
    exit 1
fi
echo -e "${GREEN}✓${NC} venv module available"

# Create virtual environment
VENV_DIR="venv"
if [ ! -d "$VENV_DIR" ]; then
    echo -e "${YELLOW}[3/5]${NC} Creating virtual environment..."
    python3 -m venv $VENV_DIR
    echo -e "${GREEN}✓${NC} Virtual environment created"
else
    echo -e "${GREEN}✓${NC} Virtual environment already exists"
fi

# Activate virtual environment
echo -e "${YELLOW}[4/5]${NC} Activating virtual environment and installing dependencies..."
source $VENV_DIR/bin/activate

# Upgrade pip
pip install --upgrade pip -q

# Install dependencies
if [ ! -f "$VENV_DIR/.installed" ] || [ "requirements.txt" -nt "$VENV_DIR/.installed" ]; then
    echo "Installing Python dependencies..."
    pip install -r requirements.txt -q
    touch $VENV_DIR/.installed
    echo -e "${GREEN}✓${NC} Dependencies installed"
else
    echo -e "${GREEN}✓${NC} Dependencies already installed (skipped)"
fi

# Compile resource files
if [ ! -f "libs/resources.py" ] || [ "resources.qrc" -nt "libs/resources.py" ]; then
    echo "Compiling Qt resource files..."
    if command -v pyside6-rcc &> /dev/null; then
        pyside6-rcc -o libs/resources.py resources.qrc
        echo -e "${GREEN}✓${NC} Resource files compiled"
    else
        echo -e "${RED}Error: pyside6-rcc command not found${NC}"
        echo "Attempting to reinstall PySide6..."
        pip install --force-reinstall pyside6 -q
        pyside6-rcc -o libs/resources.py resources.qrc
        echo -e "${GREEN}✓${NC} Resource files compiled"
    fi
else
    echo -e "${GREEN}✓${NC} Resource files are up to date (skipped)"
fi

# Launch LabelCraft
echo -e "${YELLOW}[5/5]${NC} Launching LabelCraft..."
echo ""
echo -e "${GREEN}======================================"
echo "  Environment ready!"
echo "======================================${NC}"
echo ""
echo "Tips:"
echo "  - Use 'source venv/bin/activate' to activate virtual environment"
echo "  - Use 'deactivate' to exit virtual environment"
echo "  - Run './start.sh' for quick start"
echo ""
echo "Starting LabelCraft..."
echo ""

# Remove --rebuild or -r parameter, don't pass to main.py
LABELCRAFT=()
for arg in "$@"; do
    if [[ "$arg" != "--rebuild" && "$arg" != "-r" ]]; then
        LABELCRAFT+=("$arg")
    fi
done

python main.py "${LABELCRAFT[@]}"
