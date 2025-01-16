from flask import Flask, render_template
import os
import psutil
import json
from datetime import datetime
from amtb_project.scripts.utils.config import config
from amtb_project.scripts.utils.logger import monitor_logger as logger

app = Flask(__name__, 
            template_folder=config.templates_dir)

def get_status():
    """获取系统状态"""
    try:
        # 统计下载信息
        total_codes = len(os.listdir(config.downloads_dir))
        total_files = sum([len(files) for _, _, files in os.walk(config.downloads_dir)])
        
        # 获取最新日志
        log_files = [f for f in os.listdir(os.path.join(config.logs_dir, "crawler")) 
                    if f.startswith("crawler_")]
        latest_log = ""
        if log_files:
            latest_log_file = os.path.join(config.logs_dir, "crawler", max(log_files))
            with open(latest_log_file, 'r', encoding='utf-8') as f:
                latest_log = "".join(f.readlines()[-10:])  # 最后10行
        
        # 检查进程状态
        is_running = any("python" in p.name() and "crawler.py" in " ".join(p.cmdline()) 
                        for p in psutil.process_iter(['name', 'cmdline']))
        
        # 获取磁盘使用情况
        disk = psutil.disk_usage(config.downloads_dir)
        disk_usage = f"已用: {disk.used//(1024**3)}GB, 可用: {disk.free//(1024**3)}GB"
        
        return {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'is_running': is_running,
            'total_codes': total_codes,
            'total_files': total_files,
            'disk_usage': disk_usage,
            'latest_log': latest_log
        }
    except Exception as e:
        logger.error(f"获取状态信息失败: {str(e)}")
        return {
            'error': str(e)
        }

@app.route('/')
def index():
    """主页"""
    status = get_status()
    return render_template('status.html', status=status)

@app.route('/api/status')
def api_status():
    """API接口"""
    return json.dumps(get_status())

if __name__ == '__main__':
    port = config.web_config.get('port', 5000)
    host = config.web_config.get('host', '0.0.0.0')
    app.run(host=host, port=port) 