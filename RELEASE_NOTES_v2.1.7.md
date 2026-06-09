# Release v2.1.7

**Release Date**: 2026-06-09

## Summary

This release fixes macOS UI layout issues where a large blank area appeared below the bottom panel section.

## Bug Fixes

- **macOS Dock Panel**: Remove bottom stretch spacer; let label and completed lists absorb extra vertical space
- **macOS Dock Title Bar**: Use zero-height title bar widget to avoid reserved empty space
- **macOS Toolbar**: Align toolbar buttons to top and prevent vertical stretching below the last item

## Installation

### From PyPI
```bash
pip install labelcraft==2.1.7
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

- **Linux**: `linux_LabelCraft_2.1.7.tar.gz`
- **Windows**: `windows_LabelCraft_2.1.7.zip`
- **macOS**: `macOS_LabelCraft_2.1.7.zip` or `.dmg`
