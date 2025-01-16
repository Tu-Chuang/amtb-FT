# AMTB 讲座下载项目

## 项目结构
```
/root/amtb_project/
├── scripts/          # 程序脚本
├── templates/        # Web页面模板
├── logs/            # 日志文件
├── downloads/       # 下载文件
├── data/           # 数据文件
└── config/         # 配置文件
```

## 安装
1. 安装依赖：
```bash
pip3 install -r requirements.txt
```

2. 配置：
- 编辑 config/telegram.json 设置通知
- 编辑 config/web.json 设置Web监控

## 使用方法
1. 启动服务：
```bash
./start.sh
```

2. 停止服务：
```bash
./stop.sh
```

3. 查看状态：
- Web界面：http://your_server_ip:5000
- 查看日志：`tail -f logs/crawler/crawler_*.log`

## 监控方式
1. Web监控页面
2. Telegram通知（每小时）
3. 日志文件

## 注意事项
- 程序会在后台运行
- 所有输出记录在logs目录
- 下载文件在downloads目录 