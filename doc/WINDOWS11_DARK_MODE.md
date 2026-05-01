#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
LabelCraft Windows 11 Dark Mode Setup Guide

This document describes how Windows 11 users can use the automatic dark mode detection
feature in LabelCraft.

Windows 11 Dark Mode Detection
==============================

LabelCraft automatically detects and applies the Windows 11 dark mode setting by reading
the Windows Registry.

Registry Key:
  HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Themes\Personalize
  
Registry Value:
  AppsUseLightTheme
  - 0 = Dark Mode (deep-dark interface)
  - 1 = Light Mode (default)

How to Enable Dark Mode in Windows 11
====================================

Method 1: Through Settings (Recommended)
1. Open Settings (Win + I)
2. Go to: Personalization > Colors
3. Select "Dark" in the "Choose your mode" section
4. Optionally, set "Choose your default app mode" to "Dark" as well
5. Close Settings - LabelCraft will automatically apply dark theme on next launch

Method 2: Through Registry Editor (Advanced Users)
1. Press Win + R, type "regedit" and press Enter
2. Navigate to: HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Themes\Personalize
3. Find the "AppsUseLightTheme" DWORD value
4. Set it to 0 (Dark Mode) or 1 (Light Mode)
5. Click OK and restart LabelCraft

Troubleshooting
==============

Q: The app doesn't show dark mode even after setting it in Windows 11 settings?
A: Make sure you've:
   - Restarted LabelCraft (not just minimized it)
   - Checked Windows Settings > Personalization > Colors is set to "Dark"
   - The registry value AppsUseLightTheme is actually set to 0

Q: How do I know if the detection is working?
A: When LabelCraft starts, check the terminal/console output. With verbose mode enabled,
   you should see "Detecting system theme..." message.

Q: Can I force light mode even if Windows is in dark mode?
A: Currently, LabelCraft follows the system setting. To use light mode, change your
   Windows setting to Light mode.

Technical Details
=================

LabelCraft uses the Python 'winreg' module (Windows Registry) to detect the theme.
The detection is performed automatically when the application starts, and the appropriate
color palette is applied using Qt's Fusion style.

Supported Platforms
===================
- Windows 10 (Build 1809+)
- Windows 11
- Linux (GNOME, KDE, Ubuntu)
- macOS 10.14+

Platform Detection Methods
==========================
- Windows: Registry (HKEY_CURRENT_USER)
- Linux: dconf, gsettings, or environment variables (GTK_THEME, QT_STYLE_OVERRIDE)
- macOS: defaults read command

For more information, see the main README.md file.
