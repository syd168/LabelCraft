# Release v2.1.2

**Release Date**: 2026-05-01

## Summary

This release focuses on improving cross-platform compatibility across Windows, macOS, and Linux, with enhanced build scripts and better platform-specific handling.

## Improvements

- **Cross-Platform Build System**: Unified PyInstaller-based build approach for all platforms
- **macOS Build Script**: Migrated from py2app to PyInstaller for consistency and better compatibility
- **Path Handling**: Improved cross-platform path separator handling in build configurations
- **Theme Detection**: Enhanced system theme detection for Windows, macOS, and Linux desktop environments
- **Build Automation**: GitHub Actions workflows now build for all three platforms with Python 3.9-3.12

## Platform Support

### Windows
- Native executable via PyInstaller
- Windows 10/11 dark mode detection via registry
- Batch startup script (`start.bat`)

### macOS
- Application bundle via PyInstaller (migrated from py2app)
- macOS dark mode detection via `defaults` command
- DMG and ZIP distribution formats

### Linux
- Single executable via PyInstaller
- GNOME/KDE/Ubuntu theme detection via dconf and gsettings
- Shell startup script (`start.sh`)

## Build & CI

- GitHub Actions automatically builds for ubuntu-latest, windows-latest, and macos-latest
- Tests run on Python 3.9, 3.10, 3.11, and 3.12
- Automatic release artifacts uploaded to GitHub Releases

## Installation

### From PyPI
```bash
pip install LabelCraft
```

### From Source
```bash
git clone https://github.com/syd168/LabelCraft.git
cd LabelCraft
pip install -r requirements.txt
python main.py
```

### Quick Start
- **Linux/macOS**: `./start.sh`
- **Windows**: `start.bat`

## Downloads

- **Linux**: `linux_LabelCraft_2.1.2.tar.gz`
- **Windows**: `windows_LabelCraft_2.1.2.zip`
- **macOS**: `macOS_LabelCraft_2.1.2.zip` or `.dmg`
