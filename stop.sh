#!/bin/bash

echo "正在停止所有服务..."

# 停止爬虫程序
pkill -f "python3 -m scripts.crawler"

# 停止Web监控
pkill -f "python3 -m scripts.web_monitor"

# 停止通知服务
pkill -f "python3 -m scripts.notify"

echo "所有服务已停止" 