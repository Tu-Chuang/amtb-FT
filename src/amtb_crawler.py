import os
import time
import logging
from datetime import datetime
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import re
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import requests
import zipfile
import tempfile
import shutil
import subprocess
import wget
from urllib.parse import urlparse
from multiprocessing import Lock

class AmtbCrawler:
    def __init__(self):
        self.base_url = "https://ft.amtb.tw/index_as.php"
        self.download_dir = Path("/root/amtb/downloads")
        self.log_dir = Path("/root/amtb/logs")
        self.stats_file = self.log_dir / "download_stats.log"
        self.progress_file = self.log_dir / "download_progress.json"
        self.failed_file = self.log_dir / "failed_downloads.json"
        
        # 确保目录存在
        self.setup_dirs()
        self.setup_logging()
        
        # 设置浏览器选项
        options = webdriver.ChromeOptions()
        
        # 基本配置
        options.add_argument('--headless=new')
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        
        # 内存和稳定性配置
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-software-rasterizer')
        options.add_argument('--disable-features=VizDisplayCompositor')
        options.add_argument('--disable-features=NetworkService')
        options.add_argument('--disable-features=NetworkServiceInProcess')
        options.add_argument('--disable-features=IsolateOrigins')
        options.add_argument('--disable-features=site-per-process')
        options.add_argument('--single-process')
        options.add_argument('--ignore-certificate-errors')
        options.add_argument('--disable-web-security')
        options.add_argument('--window-size=1920,1080')
        options.add_argument(f'--user-data-dir=/tmp/chrome-{os.getpid()}')
        options.add_argument('--disable-background-networking')
        
        # 禁用日志
        options.add_experimental_option('excludeSwitches', ['enable-logging', 'enable-automation'])
        options.add_experimental_option('useAutomationExtension', False)
        
        # 下载设置
        prefs = {
            "download.default_directory": str(self.download_dir.absolute()),
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True,
            "browser.helperApps.neverAsk.saveToDisk": "application/zip,application/octet-stream"
        }
        options.add_experimental_option("prefs", prefs)
        
        # 初始化浏览器
        max_retries = 3
        retry_delay = 5
        last_error = None
        
        for attempt in range(max_retries):
            try:
                print(f"尝试启动浏览器 (第 {attempt + 1} 次)")
                
                # 确保之前的实例被清理
                try:
                    os.system("pkill -f chrome")
                    os.system("pkill -f chromedriver")
                    time.sleep(2)
                except:
                    pass
                
                service = Service("/usr/local/bin/chromedriver")
                service.creation_flags = 0  # Linux 系统不需要这个标志
                self.driver = webdriver.Chrome(service=service, options=options)
                self.driver.implicitly_wait(10)
                
                # 测试浏览器是否正常工作
                self.driver.get("about:blank")
                WebDriverWait(self.driver, 10).until(
                    lambda driver: driver.execute_script('return document.readyState') == 'complete'
                )
                print("浏览器启动成功")
                break
                
            except Exception as e:
                last_error = e
                print(f"浏览器启动失败 (尝试 {attempt + 1}/{max_retries}): {str(e)}")
                
                try:
                    if hasattr(self, 'driver'):
                        self.driver.quit()
                except:
                    pass
                
                if attempt < max_retries - 1:
                    print(f"等待 {retry_delay} 秒后重试...")
                    time.sleep(retry_delay)
                else:
                    print("所有重试都失败了")
                    raise Exception(f"无法启动浏览器: {str(last_error)}")
        
        # 加载进度和失败记录
        self.load_progress()
        self.load_failed_records()
        self.file_lock = Lock()

    def setup_dirs(self):
        """创建必要的目录结构"""
        self.download_dir.mkdir(exist_ok=True)
        self.log_dir.mkdir(exist_ok=True)

    def setup_logging(self):
        """设置日志"""
        self.log_count = 0
        self.log_file_max_lines = 1000
        self.current_log_file = None
        self.create_new_log_file()

    def create_new_log_file(self):
        """创建新的日志文件"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = self.log_dir / f"crawler_{timestamp}.log"
        
        if self.current_log_file:
            logging.getLogger().handlers = []
            
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.current_log_file = log_file
        self.log_count = 0

    def write_stats(self, lecture_no, lang_name, action, details):
        """写入实时统计信息（添加进程锁）"""
        with self.file_lock:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            stats = f"{timestamp} - 讲座: {lecture_no} - {lang_name} - {action}\n"
            for key, value in details.items():
                stats += f"  {key}: {value}\n"
            stats += "-" * 50 + "\n"
            
            with open(self.stats_file, 'a', encoding='utf-8') as f:
                f.write(stats)
            logging.info(f"讲座: {lecture_no} - {lang_name} - {action} - {details}")

    def write_final_stats(self, lecture_no, stats):
        """写入最终统计信息"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        final_stats = (
            f"\n{timestamp} - 讲座 {lecture_no} 最终统计\n"
            f"  总文件数: {stats['total_count']}\n"
            f"  已下载: {stats['downloaded_count']}\n"
            f"  成功: {stats['success_count']}\n"
            f"  失败: {stats['failed_count']}\n"
            f"{'='*50}\n"
        )
        
        with open(self.stats_file, 'a', encoding='utf-8') as f:
            f.write(final_stats)
        logging.info(f"讲座 {lecture_no} 处理完成 - {stats}")

    def load_progress(self):
        """加载下载进度"""
        import json
        self.progress = {}
        if self.progress_file.exists():
            try:
                with open(self.progress_file, 'r', encoding='utf-8') as f:
                    self.progress = json.load(f)
            except Exception as e:
                logging.error(f"加载进度文件失败: {str(e)}")

    def save_progress(self, lecture_no, status="completed", current_page=None):
        """保存下载进度（添加进程锁）"""
        with self.file_lock:
            import json
            try:
                self.progress[lecture_no] = {
                    "status": status,
                    "current_page": current_page,
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                with open(self.progress_file, 'w', encoding='utf-8') as f:
                    json.dump(self.progress, f, ensure_ascii=False, indent=2)
            except Exception as e:
                logging.error(f"保存进度失败: {str(e)}")

    def load_failed_records(self):
        """加载失败记录"""
        import json
        self.failed_records = {}
        if self.failed_file.exists():
            try:
                with open(self.failed_file, 'r', encoding='utf-8') as f:
                    self.failed_records = json.load(f)
            except Exception as e:
                logging.error(f"加载失败记录文件失败: {str(e)}")

    def save_failed_record(self, lecture_no, lang, error_msg):
        """保存失败记录（添加进程锁）"""
        with self.file_lock:
            import json
            try:
                if lecture_no not in self.failed_records:
                    self.failed_records[lecture_no] = {}
                self.failed_records[lecture_no][lang] = {
                    'error': error_msg,
                    'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                with open(self.failed_file, 'w', encoding='utf-8') as f:
                    json.dump(self.failed_records, f, ensure_ascii=False, indent=2)
            except Exception as e:
                logging.error(f"保存失败记录时出错: {str(e)}")

    def remove_failed_record(self, lecture_no, lang):
        """移除失败记录"""
        import json
        try:
            if lecture_no in self.failed_records and lang in self.failed_records[lecture_no]:
                del self.failed_records[lecture_no][lang]
                if not self.failed_records[lecture_no]:  # 如果该讲座的所有语言版本都成功了
                    del self.failed_records[lecture_no]
                with open(self.failed_file, 'w', encoding='utf-8') as f:
                    json.dump(self.failed_records, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logging.error(f"移除失败记录时出错: {str(e)}")

    def process_lecture(self, lecture_no):
        """处理单个讲座编号"""
        try:
            print(f"\n开始处理讲座: {lecture_no}")
            
            # 创建目录结构
            base_dir = self.download_dir / lecture_no
            base_dir.mkdir(exist_ok=True)
            
            total_stats = {
                'total_count': 0,
                'downloaded_count': 0,
                'success_count': 0,
                'failed_count': 0
            }
            
            for lang, lang_name in [('zh_TW', '正体'), ('zh_CN', '简体')]:
                try:
                    print(f"\n处理{lang_name}版本...")
                    
                    # 创建语言目录
                    lang_dir = base_dir / lang
                    lang_dir.mkdir(exist_ok=True)
                    self.set_download_directory(str(lang_dir.absolute()))
                    
                    # 访问页面并设置搜索条件
                    self.driver.get(self.base_url)
                    
                    # 设置语言
                    lang_select = WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "select.form-control[name='lang']"))
                    )
                    for option in lang_select.find_elements(By.TAG_NAME, "option"):
                        if option.get_attribute("value") == lang:
                            option.click()
                            break
                    
                    # 设置搜索条件
                    search_input = WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.NAME, "as_query_all_words"))
                    )
                    search_input.clear()
                    search_input.send_keys(lecture_no)
                    
                    # 执行搜索
                    search_button = WebDriverWait(self.driver, 10).until(
                        EC.element_to_be_clickable((By.NAME, "searchButton"))
                    )
                    search_button.click()
                    
                    # 获取搜索结果数量
                    result_text = WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "span#ctl00_CH_C_Label_ServerCostTime"))
                    ).text
                    total_count = int(re.search(r'共發現\s*(\d+)\s*筆資料', result_text).group(1))
                    print(f"找到 {total_count} 个文件")
                    
                    if total_count == 0:
                        print(f"{lang_name}版本无可用文件")
                        continue
                    
                    # 设置下载选项
                    select_all = WebDriverWait(self.driver, 10).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, "input[name='selectall'][value='ALL']"))
                    )
                    select_all.click()
                    
                    # 选择doc格式
                    for checkbox in self.driver.find_elements(By.CSS_SELECTOR, "input[name='docstype[]']"):
                        if checkbox.is_selected():
                            checkbox.click()
                    checkbox = WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "input[name='docstype[]'][value='doc']"))
                    )
                    checkbox.click()
                    
                    # 开始下载
                    print(f"开始下载{lang_name}版本...")
                    download_button = WebDriverWait(self.driver, 10).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, "input#zipdownloadbutton"))
                    )
                    download_button.click()
                    
                    try:
                        self.wait_for_download(lang_dir)
                        print(f"{lang_name}版本下载成功")
                        total_stats['downloaded_count'] += total_count
                        total_stats['success_count'] += total_count
                        self.remove_failed_record(lecture_no, lang)
                    except Exception as e:
                        print(f"{lang_name}版本下载失败: {str(e)}")
                        total_stats['failed_count'] += total_count
                        self.save_failed_record(lecture_no, lang, str(e))
                    
                except Exception as e:
                    error_msg = str(e)
                    print(f"{lang_name}版本处理失败: {error_msg}")
                    total_stats['failed_count'] += total_count
                    self.save_failed_record(lecture_no, lang, error_msg)
                    continue
            
            # 输出最终统计
            print(f"\n讲座 {lecture_no} 处理完成:")
            print(f"总文件数: {total_stats['total_count']}")
            print(f"成功: {total_stats['success_count']}")
            print(f"失败: {total_stats['failed_count']}")
            
            self.save_progress(lecture_no, "completed")
            
        except Exception as e:
            print(f"讲座 {lecture_no} 处理出错: {str(e)}")
            self.save_progress(lecture_no, "error")
            raise

    def set_download_directory(self, directory):
        """设置下载目录"""
        self.driver.command_executor._commands["send_command"] = ("POST", '/session/$sessionId/chromium/send_command')
        params = {
            'cmd': 'Page.setDownloadBehavior',
            'params': {
                'behavior': 'allow',
                'downloadPath': directory
            }
        }
        self.driver.execute("send_command", params)

    def wait_for_download(self, download_dir, timeout=120):
        """等待下载完成"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            # 检查是否有正在下载的文件
            downloading = False
            for file in download_dir.glob("*"):
                if file.suffix in ['.crdownload', '.tmp']:
                    downloading = True
                    break
            
            # 如果没有正在下载的文件，且目录中有zip文件，说明下载完成
            if not downloading and list(download_dir.glob("*.zip")):
                return True
            
            time.sleep(2)
        
        raise TimeoutException(f"下载超时 ({timeout}秒)")

    def close(self):
        """关闭浏览器"""
        self.driver.quit()

    def select_language(self, lang):
        """选择语言"""
        lang_select = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.NAME, "lang"))
        )
        for option in lang_select.find_elements(By.TAG_NAME, "option"):
            if option.get_attribute("value") == lang:
                option.click()
                break
        time.sleep(1)

    def set_search_conditions(self, lecture_no):
        """设置搜索条件"""
        # 选择编号搜索
        srange_select = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.NAME, "srange"))
        )
        for option in srange_select.find_elements(By.TAG_NAME, "option"):
            if option.get_attribute("value") == "sn":
                option.click()
                break
        time.sleep(1)
        
        # 勾选精确匹配
        exact_match = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[name='index'][value='amtbfulltext']"))
        )
        if not exact_match.is_selected():
            exact_match.click()
        time.sleep(1)
        
        # 输入讲座编号
        search_input = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.NAME, "as_query_all_words"))
        )
        search_input.clear()
        search_input.send_keys(lecture_no)

    def perform_search(self):
        """执行搜索"""
        search_button = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.NAME, "searchButton"))
        )
        search_button.click()
        time.sleep(3)

    def check_search_results(self):
        """检查搜索结果数量"""
        result_text = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "span#ctl00_CH_C_Label_ServerCostTime"))
        ).text
        match = re.search(r'共發現\s*(\d+)\s*筆資料', result_text)
        if match:
            return int(match.group(1))
        return 0

    def set_page_size(self):
        """设置每页显示数量"""
        limit_select = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "select[name='limit']"))
        )
        options = limit_select.find_elements(By.TAG_NAME, "option")
        max_option = max(options, key=lambda x: int(x.get_attribute("value")))
        max_option.click()
        time.sleep(2)

    def set_download_options(self):
        """设置下载选项"""
        # 点击全选
        select_all = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "input[name='selectall'][value='ALL']"))
        )
        select_all.click()
        time.sleep(1)
        
        # 选择文件类型
        for doc_type in ['doc', 'pdf', 'txt']:
            checkbox = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, f"input[name='docstype[]'][value='{doc_type}']"))
            )
            if not checkbox.is_selected():
                checkbox.click()
                time.sleep(0.5)

    def download_with_retry(self, url, max_retries=3):
        """带重试的下载功能"""
        import wget
        import os
        from urllib.parse import urlparse
        
        filename = os.path.basename(urlparse(url).path)
        temp_file = f"{filename}.tmp"
        
        for attempt in range(max_retries):
            try:
                if os.path.exists(temp_file):
                    # 如果临时文件存在，尝试继续下载
                    print(f"\n发现未完成的下载，继续下载: {temp_file}")
                    wget.download(url, temp_file, continue_=True)
                else:
                    # 新下载
                    print(f"\n开始下载: {filename}")
                    wget.download(url, temp_file)
                
                # 下载完成后重命名
                if os.path.exists(temp_file):
                    os.rename(temp_file, filename)
                    print(f"\n下载完成: {filename}")
                    return filename
                    
            except Exception as e:
                print(f"\n第 {attempt + 1} 次下载失败: {str(e)}")
                if attempt == max_retries - 1:
                    raise
                print("等待 5 秒后重试...")
                time.sleep(5)
        
        raise Exception("下载失败，已达到最大重试次数") 