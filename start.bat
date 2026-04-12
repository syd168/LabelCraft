@echo off
chcp 65001 >nul
REM LabelCraft 快速启动脚本 (Windows)
REM 此脚本会自动创建虚拟环境、安装依赖并启动应用

setlocal enabledelayedexpansion

echo ======================================
echo   LabelCraft - 图像标注工具
echo ======================================
echo.

REM 检查 Python 是否安装
echo [1/5] 检查 Python 环境...
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo 错误: 未找到 Python
    echo 请先安装 Python 3.8 或更高版本
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo ✓ Python 版本: %PYTHON_VERSION%

REM 创建虚拟环境
set VENV_DIR=venv
if not exist %VENV_DIR% (
    echo [2/5] 创建虚拟环境...
    python -m venv %VENV_DIR%
    if %errorlevel% neq 0 (
        echo 错误: 创建虚拟环境失败
        echo 请确保已安装 venv 模块
        pause
        exit /b 1
    )
    echo ✓ 虚拟环境创建成功
) else (
    echo ✓ 虚拟环境已存在
)

REM 激活虚拟环境
echo [3/5] 激活虚拟环境...
call %VENV_DIR%\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo 错误: 激活虚拟环境失败
    pause
    exit /b 1
)

REM 升级 pip
echo [4/5] 安装依赖包...
python -m pip install --upgrade pip -q

REM 检查是否需要安装依赖
if not exist %VENV_DIR%\.installed (
    echo 正在安装 Python 依赖包...
    pip install -r requirements.txt -q
    if %errorlevel% neq 0 (
        echo 错误: 安装依赖失败
        pause
        exit /b 1
    )
    echo. > %VENV_DIR%\.installed
    echo ✓ 依赖安装完成
) else (
    REM 检查 requirements.txt 是否更新
    if requirements.txt -nt %VENV_DIR%\.installed (
        echo 检测到依赖更新，重新安装...
        pip install -r requirements.txt -q
        if %errorlevel% neq 0 (
            echo 错误: 安装依赖失败
            pause
            exit /b 1
        )
        echo. > %VENV_DIR%\.installed
        echo ✓ 依赖更新完成
    ) else (
        echo ✓ 依赖已安装（跳过）
    )
)

REM 编译资源文件
if not exist libs\resources.py (
    echo 编译 Qt 资源文件...
    where pyside6-rcc >nul 2>&1
    if %errorlevel% neq 0 (
        echo 错误: 未找到 pyside6-rcc 命令
        echo 尝试重新安装 PySide6...
        pip install --force-reinstall pyside6 -q
    )
    pyside6-rcc -o libs\resources.py resources.qrc
    if %errorlevel% neq 0 (
        echo 错误: 编译资源文件失败
        pause
        exit /b 1
    )
    echo ✓ 资源文件编译完成
) else (
    REM 检查 resources.qrc 是否更新
    if resources.qrc -nt libs\resources.py (
        echo 检测到资源文件更新，重新编译...
        pyside6-rcc -o libs\resources.py resources.qrc
        if %errorlevel% neq 0 (
            echo 错误: 编译资源文件失败
            pause
            exit /b 1
        )
        echo ✓ 资源文件编译完成
    ) else (
        echo ✓ 资源文件已是最新（跳过）
    )
)

REM 启动 LabelCraft
echo [5/5] 启动 LabelCraft...
echo.
echo ======================================
echo   环境准备完成！
echo ======================================
echo.
echo 提示:
echo   - 运行 'venv\Scripts\activate' 激活虚拟环境
echo   - 运行 'deactivate' 退出虚拟环境
echo   - 直接运行 'start.bat' 可快速启动
echo.
echo 正在启动 LabelCraft...
echo.

python main.py %*

REM 如果程序退出，暂停以便查看错误信息
if %errorlevel% neq 0 (
    echo.
    echo 程序异常退出，错误代码: %errorlevel%
    pause
)
