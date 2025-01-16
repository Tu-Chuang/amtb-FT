import telegram
import os
import time
from datetime import datetime

class TelegramNotifier:
    def __init__(self):
        self.bot_token = 'YOUR_BOT_TOKEN'  # 替换为你的bot token
        self.chat_id = 'YOUR_CHAT_ID'      # 替换为你的chat id
        self.bot = telegram.Bot(token=self.bot_token)
    
    def send_status(self, message):
        try:
            self.bot.send_message(chat_id=self.chat_id, text=message)
        except Exception as e:
            print(f"发送通知失败: {str(e)}")

def get_download_status():
    project_dir = "/root/amtb_project"
    downloads_dir = os.path.join(project_dir, "downloads")
    
    # 获取下载统计
    total_files = sum([len(files) for _, _, files in os.walk(downloads_dir)])
    total_dirs = sum([len(d) for _, d, _ in os.walk(downloads_dir)])
    
    # 获取最新日志
    log_files = [f for f in os.listdir(os.path.join(project_dir, "logs")) if f.startswith("crawler_")]
    latest_log = max(log_files) if log_files else None
    
    # 检查进程状态
    is_running = os.system('ps aux | grep "[p]ython3 scripts/crawler.py" > /dev/null') == 0
    
    status = f"""
AMTB 下载状态报告
时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
运行状态: {'运行中' if is_running else '已停止'}
已下载编号数: {total_dirs}
总文件数: {total_files}
最新日志: {latest_log}
"""
    return status

def main():
    notifier = TelegramNotifier()
    while True:
        status = get_download_status()
        notifier.send_status(status)
        time.sleep(3600)  # 每小时发送一次状态

if __name__ == "__main__":
    main() 