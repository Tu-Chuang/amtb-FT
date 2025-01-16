#!/bin/bash

# 设置工作目录
cd /root/amtb_project

# 确保目录结构存在
mkdir -p logs/{crawler,monitor,notify}
mkdir -p downloads
mkdir -p data
mkdir -p config

# 检查配置文件
if [ ! -f config/telegram.json ]; then
    echo '{"bot_token": "YOUR_BOT_TOKEN", "chat_id": "YOUR_CHAT_ID"}' > config/telegram.json
fi

if [ ! -f config/web.json ]; then
    echo '{"port": 5000, "host": "0.0.0.0"}' > config/web.json
fi

# 获取当前时间
datetime=$(date +"%Y%m%d_%H%M%S")

# 启动爬虫程序
nohup python3 -m scripts.crawler > "logs/crawler/crawler_${datetime}.log" 2>&1 &
echo "爬虫程序已启动，进程ID: $!"

# 启动Web监控
nohup python3 -m scripts.web_monitor > "logs/monitor/monitor_${datetime}.log" 2>&1 &
echo "Web监控已启动: http://$(hostname -I | awk '{print $1}'):5000"

# 启动通知服务
nohup python3 -m scripts.notify > "logs/notify/notify_${datetime}.log" 2>&1 &
echo "通知服务已启动"

echo "所有服务已启动，查看日志请使用:"
echo "tail -f logs/crawler/crawler_${datetime}.log"
echo "tail -f logs/monitor/monitor_${datetime}.log"
echo "tail -f logs/notify/notify_${datetime}.log" 