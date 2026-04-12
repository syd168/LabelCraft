#!/bin/bash

# LabelCraft 快速启动脚本 (Linux/macOS)
# 此脚本会自动创建虚拟环境、安装依赖并启动应用
# 使用方法:
#   ./start.sh           # 正常启动
#   ./start.sh --rebuild # 强制重新编译资源文件

set -e  # 遇到错误时退出

echo "======================================"
echo "  LabelCraft - 图像标注工具"
echo "======================================"
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查是否强制重新编译
FORCE_REBUILD=false
if [[ "$1" == "--rebuild" || "$1" == "-r" ]]; then
    FORCE_REBUILD=true
    echo -e "${YELLOW}⚠ 强制重新编译模式${NC}"
    rm -f libs/resources.py venv/.installed
fi

# 检查 Python 是否安装
echo -e "${YELLOW}[1/5]${NC} 检查 Python 环境..."
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}错误: 未找到 Python3${NC}"
    echo "请先安装 Python 3.8 或更高版本"
    echo "下载地址: https://www.python.org/downloads/"
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo -e "${GREEN}✓${NC} Python 版本: $PYTHON_VERSION"

# 检查 Python 版本是否符合要求
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 8 ]); then
    echo -e "${RED}错误: Python 版本需要 3.8 或更高${NC}"
    echo "当前版本: $PYTHON_VERSION"
    exit 1
fi

# 检查 venv 模块
echo -e "${YELLOW}[2/5]${NC} 检查虚拟环境模块..."
if ! python3 -m venv --help &> /dev/null; then
    echo -e "${RED}错误: venv 模块不可用${NC}"
    echo "请安装 python3-venv 包:"
    echo "  Ubuntu/Debian: sudo apt install python3-venv"
    echo "  CentOS/RHEL: sudo yum install python3-venv"
    echo "  macOS: 通常已包含在 Python 安装包中"
    exit 1
fi
echo -e "${GREEN}✓${NC} venv 模块可用"

# 创建虚拟环境
VENV_DIR="venv"
if [ ! -d "$VENV_DIR" ]; then
    echo -e "${YELLOW}[3/5]${NC} 创建虚拟环境..."
    python3 -m venv $VENV_DIR
    echo -e "${GREEN}✓${NC} 虚拟环境创建成功"
else
    echo -e "${GREEN}✓${NC} 虚拟环境已存在"
fi

# 激活虚拟环境
echo -e "${YELLOW}[4/5]${NC} 激活虚拟环境并安装依赖..."
source $VENV_DIR/bin/activate

# 升级 pip
pip install --upgrade pip -q

# 安装依赖
if [ ! -f "$VENV_DIR/.installed" ] || [ "requirements.txt" -nt "$VENV_DIR/.installed" ]; then
    echo "安装 Python 依赖包..."
    pip install -r requirements.txt -q
    touch $VENV_DIR/.installed
    echo -e "${GREEN}✓${NC} 依赖安装完成"
else
    echo -e "${GREEN}✓${NC} 依赖已安装（跳过）"
fi

# 编译资源文件
if [ ! -f "libs/resources.py" ] || [ "resources.qrc" -nt "libs/resources.py" ]; then
    echo "编译 Qt 资源文件..."
    if command -v pyside6-rcc &> /dev/null; then
        pyside6-rcc -o libs/resources.py resources.qrc
        echo -e "${GREEN}✓${NC} 资源文件编译完成"
    else
        echo -e "${RED}错误: 未找到 pyside6-rcc 命令${NC}"
        echo "尝试重新安装 PySide6..."
        pip install --force-reinstall pyside6 -q
        pyside6-rcc -o libs/resources.py resources.qrc
        echo -e "${GREEN}✓${NC} 资源文件编译完成"
    fi
else
    echo -e "${GREEN}✓${NC} 资源文件已是最新（跳过）"
fi

# 启动 LabelCraft
echo -e "${YELLOW}[5/5]${NC} 启动 LabelCraft..."
echo ""
echo -e "${GREEN}======================================"
echo "  环境准备完成！"
echo "======================================${NC}"
echo ""
echo "提示:"
echo "  - 使用 'source venv/bin/activate' 激活虚拟环境"
echo "  - 使用 'deactivate' 退出虚拟环境"
echo "  - 直接运行 './start.sh' 可快速启动"
echo ""
echo "正在启动 LabelCraft..."
echo ""

# 移除 --rebuild 或 -r 参数，不传递给 main.py
LABELIMG_ARGS=()
for arg in "$@"; do
    if [[ "$arg" != "--rebuild" && "$arg" != "-r" ]]; then
        LABELIMG_ARGS+=("$arg")
    fi
done

python main.py "${LABELIMG_ARGS[@]}"
