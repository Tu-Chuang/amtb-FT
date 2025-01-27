#!/bin/bash

# 设置工作目录
WORK_DIR="/root/amtb"
VENV_DIR="$WORK_DIR/venv"
SRC_DIR="$WORK_DIR/src"
LOG_FILE="$WORK_DIR/logs/nohup.log"

# 确保日志目录存在
mkdir -p "$(dirname "$LOG_FILE")"

# 检查 screen 是否已安装
if ! command -v screen &> /dev/null; then
    echo "正在安装 screen..."
    apt-get update && apt-get install -y screen
fi

# 检查是否已存在名为 amtb_new 的 screen 会话
if screen -list | grep -q "amtb_new"; then
    echo "爬虫已在运行中"
    echo "使用 'screen -r amtb_new' 查看运行状态"
    exit 1
fi

# 创建新的 screen 会话并运行爬虫
echo "启动爬虫..."
screen -dmS amtb_new bash -c "
    echo '激活虚拟环境...'
    source $VENV_DIR/bin/activate
    
    echo '切换到工作目录...'
    cd $SRC_DIR
    
    echo '开始运行爬虫...'
    python3 main.py 2>&1 | tee -a $LOG_FILE
"

echo "爬虫已在后台启动"
echo "使用以下命令管理爬虫："
echo "  查看运行状态: screen -r amtb_new"
echo "  退出查看但保持运行: Ctrl+A 然后按 D"
echo "  查看日志: tail -f $LOG_FILE"