@echo off
chcp 65001 >nul
REM LabelCraft Quick Start Script (Windows)
REM This script will automatically create a virtual environment, install dependencies, and launch the application

setlocal enabledelayedexpansion

echo ======================================
echo   LabelCraft - Image Annotation Tool
echo ======================================
echo.

REM Check if Python is installed
echo [1/5] Checking Python environment...
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Python not found
    echo Please install Python 3.8 or higher
    echo Download: https://www.python.org/downloads/
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo ✓ Python version: %PYTHON_VERSION%

REM Create virtual environment
set VENV_DIR=venv
if not exist %VENV_DIR% (
    echo [2/5] Creating virtual environment...
    python -m venv %VENV_DIR%
    if %errorlevel% neq 0 (
        echo Error: Failed to create virtual environment
        echo Please ensure venv module is installed
        pause
        exit /b 1
    )
    echo ✓ Virtual environment created
) else (
    echo ✓ Virtual environment already exists
)

REM Activate virtual environment
echo [3/5] Activating virtual environment...
call %VENV_DIR%\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo Error: Failed to activate virtual environment
    pause
    exit /b 1
)

REM Upgrade pip
echo [4/5] Installing dependencies...
python -m pip install --upgrade pip -q

REM Check if dependencies need to be installed
if not exist %VENV_DIR%\.installed (
    echo Installing Python dependencies...
    pip install -r requirements.txt -q
    if %errorlevel% neq 0 (
        echo Error: Failed to install dependencies
        pause
        exit /b 1
    )
    echo. > %VENV_DIR%\.installed
    echo ✓ Dependencies installed
) else (
    REM Check if requirements.txt has been updated
    if requirements.txt -nt %VENV_DIR%\.installed (
        echo Dependencies updated, reinstalling...
        pip install -r requirements.txt -q
        if %errorlevel% neq 0 (
            echo Error: Failed to install dependencies
            pause
            exit /b 1
        )
        echo. > %VENV_DIR%\.installed
        echo ✓ Dependencies updated
    ) else (
        echo ✓ Dependencies already installed (skipped)
    )
)

REM Compile resource files
if not exist libs\resources.py (
    echo Compiling Qt resource files...
    where pyside6-rcc >nul 2>&1
    if %errorlevel% neq 0 (
        echo Error: pyside6-rcc command not found
        echo Attempting to reinstall PySide6...
        pip install --force-reinstall pyside6 -q
    )
    pyside6-rcc -o libs\resources.py resources.qrc
    if %errorlevel% neq 0 (
        echo Error: Failed to compile resource files
        pause
        exit /b 1
    )
    echo ✓ Resource files compiled
) else (
    REM Check if resources.qrc has been updated
    if resources.qrc -nt libs\resources.py (
        echo Resource files updated, recompiling...
        pyside6-rcc -o libs\resources.py resources.qrc
        if %errorlevel% neq 0 (
            echo Error: Failed to compile resource files
            pause
            exit /b 1
        )
        echo ✓ Resource files compiled
    ) else (
        echo ✓ Resource files are up to date (skipped)
    )
)

REM Launch LabelCraft
echo [5/5] Launching LabelCraft...
echo.
echo ======================================
echo   Environment ready!
echo ======================================
echo.
echo Tips:
echo   - Run 'venv\Scripts\activate' to activate virtual environment
echo   - Run 'deactivate' to exit virtual environment
echo   - Run 'start.bat' for quick start
echo.
echo Starting LabelCraft...
echo.

python main.py %*

REM If program exits, pause to view error messages
if %errorlevel% neq 0 (
    echo.
    echo Program exited abnormally, error code: %errorlevel%
    pause
)
