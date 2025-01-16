import os
import json
from datetime import datetime

class Config:
    def __init__(self):
        self.project_dir = "/root/amtb_project"
        self.downloads_dir = os.path.join(self.project_dir, "downloads")
        self.logs_dir = os.path.join(self.project_dir, "logs")
        self.data_dir = os.path.join(self.project_dir, "data")
        self.config_dir = os.path.join(self.project_dir, "config")
        self.templates_dir = os.path.join(self.project_dir, "scripts/templates")

        # 创建必要的目录
        for dir_path in [
            self.downloads_dir,
            self.logs_dir,
            self.data_dir,
            self.config_dir,
            os.path.join(self.logs_dir, "crawler"),
            os.path.join(self.logs_dir, "monitor"),
            os.path.join(self.logs_dir, "notify")
        ]:
            os.makedirs(dir_path, exist_ok=True)

        # 加载配置
        self.telegram_config = self._load_config("telegram.json")
        self.web_config = self._load_config("web.json")

    def _load_config(self, filename):
        config_path = os.path.join(self.config_dir, filename)
        if not os.path.exists(config_path):
            # 创建默认配置
            default_configs = {
                "telegram.json": {
                    "bot_token": "YOUR_BOT_TOKEN",
                    "chat_id": "YOUR_CHAT_ID"
                },
                "web.json": {
                    "port": 5000,
                    "host": "0.0.0.0"
                }
            }
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(default_configs.get(filename, {}), f, indent=4)
            return default_configs.get(filename, {})
        
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def get_log_file(self, service_name):
        """获取日志文件路径"""
        log_dir = os.path.join(self.logs_dir, service_name)
        os.makedirs(log_dir, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        return os.path.join(log_dir, f"{service_name}_{timestamp}.log")

    def get_download_dir(self, code):
        """获取指定编号的下载目录"""
        download_dir = os.path.join(self.downloads_dir, code)
        os.makedirs(download_dir, exist_ok=True)
        return download_dir

# 创建全局配置实例
config = Config() 