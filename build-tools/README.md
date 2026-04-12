# Build Tools for LabelCraft

Modern build scripts for packaging LabelCraft across different platforms.

> **Note**: This project is based on [labelImg](https://github.com/tzutalin/labelImg).

## Prerequisites

- Python 3.8 or higher
- PySide6
- lxml

## Quick Start

### Build for Linux

```bash
cd build-tools
chmod +x build-linux.sh
./build-linux.sh
```

Output: `dist/linux_labelCraft_<version>.tar.gz`

### Build for Windows (from Linux using Wine)

**Prerequisites:**
- Install Wine: `sudo apt install wine64`
- Install Python 3.11 for Windows in Wine

```bash
cd build-tools
chmod +x build-windows.sh
./build-windows.sh
```

Output: `dist/windows_labelCraft_<version>.zip`

**First-time Wine setup:**
```bash
# Download Python 3.11 for Windows
wget https://www.python.org/ftp/python/3.11.0/python-3.11.0-amd64.exe

# Install in Wine
wine python-3.11.0-amd64.exe
# Follow installer, use default path C:\Python311
```

### Build for macOS

```bash
cd build-tools
chmod +x build-macos.sh
./build-macos.sh
```

Output: `dist/macOS_labelCraft_<version>.zip` and `.dmg`

### Build for PyPI

```bash
cd build-tools
chmod +x build-pypi.sh
./build-pypi.sh
```

This will create source distribution and wheel packages, and optionally upload to PyPI.

### Install from PyPI Package

After building or once the package is published to PyPI, you can install it:

#### Install from Local Build

If you built the package locally:

```bash
# Install the wheel file (replace <version> with actual version)
pip install dist/labelCraft-<version>-py3-none-any.whl

# Or install from source distribution
pip install dist/labelCraft-<version>.tar.gz
```

#### Install from PyPI (Published Package)

Once published to PyPI:

```bash
# Install to current Python environment
pip install labelcraft

# Install to virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate   # Windows
pip install labelcraft
```

#### Usage After Installation

```bash
# Launch the application
labelcraft

# With image path
labelcraft /path/to/image.jpg

# With full parameters
labelcraft images/ classes.txt annotations/
```

#### Upgrade and Uninstall

```bash
# Upgrade to latest version
pip install --upgrade labelcraft

# Uninstall
pip uninstall labelcraft
```

## Troubleshooting

### Linux Build Issues

If you encounter missing dependencies:
```bash
pip install pyinstaller PySide6 lxml
```

### Windows Build Issues (Wine)

If Wine Python is not found:
```bash
# Check Wine prefix
ls ~/.wine/drive_c/Python311/python.exe

# Reinstall Python in Wine if needed
wine python-3.11.0-amd64.exe
```

Clean Wine environment:
```bash
rm -rf ~/.wine
winecfg  # Reconfigure Wine
```

### macOS Build Issues

Install py2app:
```bash
pip install py2app
```

## Distribution Structure

Each build creates a distribution directory with:
- Executable file (`.exe`, binary, or `.app`)
- `data/` directory with predefined classes
- `README.md` with usage instructions

## Advanced Usage

### Custom PyInstaller Options

Edit the build script and modify the PyInstaller command:
```bash
pyinstaller --name=labelCraft \\
    --onefile \
    --windowed \
    --add-data="resources:resources" \
    --hidden-import=your_module \
    main.py
```

### Building on Different Platforms

- **Linux**: Native build with PyInstaller
- **Windows**: Cross-compile from Linux using Wine, or native build on Windows
- **macOS**: Native build with py2app (requires macOS)

## Notes

- All scripts automatically detect the version from `libs/__init__.py`
- Previous builds are cleaned before each build
- Scripts exit on first error (`set -e`)
- Dependencies are installed automatically if missing

---

# GitHub Actions CI/CD

This project uses GitHub Actions for automated building and testing of LabelCraft.

## Automatic Builds

### On Every Push
- ✅ Runs tests on Ubuntu, Windows, and macOS
- ✅ Tests with Python 3.9, 3.10, 3.11, and 3.12
- ✅ Validates imports and basic functionality

### On Tagged Releases (e.g., `v1.0.0`)
- 🚀 Builds executables for all three platforms
- 📦 Creates distribution packages
- 🎯 Uploads to GitHub Releases
- 🐍 Publishes to PyPI (if configured)

## How to Create a Release

### Step 1: Update Version
Edit `libs/__init__.py` and update the version number:
```python
__version__ = '1.8.6'  # Change this
```

### Step 2: Commit and Tag
```bash
git add libs/__init__.py
git commit -m "Bump version to 1.8.6"
git tag v1.8.6
git push origin main --tags
```

### Step 3: Wait for GitHub Actions
GitHub will automatically:
1. Run all tests
2. Build executables for Linux, Windows, and macOS
3. Create a GitHub Release with all artifacts
4. Upload to PyPI (if `PYPI_API_TOKEN` secret is configured)

### Step 4: Check the Release
Visit: `https://github.com/syd168/LabelCraft/releases/tag/v1.8.6`

## Manual Trigger

You can also manually trigger builds:
1. Go to **Actions** tab in your GitHub repository
2. Select **Build Releases** workflow
3. Click **Run workflow**
4. Choose branch and click **Run workflow**

## Configuring PyPI Upload

To enable automatic PyPI uploads:

1. Generate an API token from [pypi.org](https://pypi.org/manage/account/token/)
2. Add it as a secret in your GitHub repository:
   - Go to **Settings** → **Secrets and variables** → **Actions**
   - Click **New repository secret**
   - Name: `PYPI_API_TOKEN`
   - Value: Your PyPI API token

## Workflow Files

- `.github/workflows/build-releases.yml` - Main build workflow
- `.github/workflows/ci-tests.yml` - Continuous integration tests
- `.github/generate_release_notes.py` - Auto-generate release notes

## Artifacts

After each build, you can download:
- **Linux**: `linux_labelCraft_<version>.tar.gz`
- **Windows**: `windows_labelCraft_<version>.zip`
- **macOS**: `macOS_labelCraft_<version>.zip` and `.dmg`

Artifacts are available in:
1. GitHub Actions run page (temporary, 90 days)
2. GitHub Releases page (permanent, for tagged releases)
