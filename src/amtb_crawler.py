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

class AmtbCrawler:
    def __init__(self):
        self.base_url = "https://ft.amtb.tw/"
        self.download_dir = Path("downloads")
        self.log_dir = Path("logs")
        self.stats_file = self.log_dir / "download_stats.log"
        self.progress_file = self.log_dir / "download_progress.json"
        self.setup_dirs()
        self.setup_logging()
        self.setup_driver()
        self.load_progress()

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

    def setup_driver(self):
        """设置Chrome浏览器"""
        options = webdriver.ChromeOptions()
        
        # Ubuntu 下的特殊设置
        options.add_argument('--no-sandbox')  # 必须的参数
        options.add_argument('--headless')  # 无界面模式
        options.add_argument('--disable-dev-shm-usage')  # 解决内存不足问题
        options.add_argument('--disable-gpu')  # 禁用 GPU 加速
        
        # 下载设置
        prefs = {
            "download.default_directory": "",  # 会在process_lecture中动态设置
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True,
            "safebrowsing.disable_download_protection": True
        }
        options.add_experimental_option("prefs", prefs)
        
        # 使用 webdriver_manager 自动安装和管理 ChromeDriver
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=options)
        self.driver.implicitly_wait(10)

    def write_stats(self, lecture_no, total_count, downloaded_count, success_count, failed_count):
        """写入下载统计信息"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        stats = (
            f"{timestamp} - 讲座编号: {lecture_no}\n"
            f"  总文件数: {total_count}\n"
            f"  已下载: {downloaded_count}\n"
            f"  成功: {success_count}\n"
            f"  失败: {failed_count}\n"
            f"{'='*50}\n"
        )
        with open(self.stats_file, 'a', encoding='utf-8') as f:
            f.write(stats)

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
        """保存下载进度"""
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

    def process_lecture(self, lecture_no):
        """处理单个讲座编号"""
        if lecture_no in self.progress and self.progress[lecture_no]["status"] == "completed":
            logging.info(f"讲座 {lecture_no} 已下载完成，跳过")
            return

        start_page = 0
        if lecture_no in self.progress and self.progress[lecture_no]["current_page"]:
            start_page = self.progress[lecture_no]["current_page"]
            logging.info(f"从第 {start_page + 1} 页继续下载讲座 {lecture_no}")

        total_count = 0
        downloaded_count = 0
        success_count = 0
        failed_count = 0
        
        try:
            # 创建讲座专属目录
            lecture_dir = self.download_dir / lecture_no
            lecture_dir.mkdir(exist_ok=True)
            
            # 更新下载目录
            self.driver.command_executor._commands["send_command"] = ("POST", '/session/$sessionId/chromium/send_command')
            params = {
                'cmd': 'Page.setDownloadBehavior',
                'params': {
                    'behavior': 'allow',
                    'downloadPath': str(lecture_dir.absolute())
                }
            }
            self.driver.execute("send_command", params)
            
            logging.info(f"开始处理讲座编号: {lecture_no}")
            
            # 访问网页
            self.driver.get(self.base_url)
            time.sleep(3)
            
            try:
                # 选择"编号"搜索模式
                select = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "select#srange[name='srange']"))
                )
                select.click()
                option = select.find_element(By.CSS_SELECTOR, "option[value='sn']")
                option.click()
                time.sleep(1)
                
                # 定位搜索框并输入讲座编号
                search_input = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "input#query[name='query']"))
                )
                search_input.clear()
                search_input.send_keys(lecture_no)
                time.sleep(1)
                
                # 选择繁体选项
                traditional_radio = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "input#lang_tw[type='radio'][value='zh_TW']"))
                )
                if not traditional_radio.is_selected():
                    traditional_radio.click()
                time.sleep(1)
                
                # 点击搜索按钮
                search_button = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "input#searchButton[type='button']"))
                )
                self.driver.execute_script("arguments[0].click();", search_button)
                time.sleep(3)
                
                # 等待搜索结果加载并获取结果数量
                try:
                    result_text = WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "span#ctl00_CH_C_Label_ServerCostTime[style*='color:#C00000']"))
                    ).text
                    
                    match = re.search(r'(\d+)\s*筆資料', result_text)
                    if match:
                        total_count = int(match.group(1))
                        logging.info(f"讲座 {lecture_no} 找到 {total_count} 个文件")
                    else:
                        logging.warning(f"无法解析结果数量: {result_text}")
                        total_count = 0
                    
                    if total_count > 0:
                        try:
                            # 获取总页数
                            page_links = self.driver.find_elements(By.CSS_SELECTOR, ".pagination .page-link")
                            page_numbers = []
                            for link in page_links:
                                if link.text.isdigit():
                                    page_numbers.append(int(link.text))
                            total_pages = max(page_numbers) if page_numbers else 1
                            logging.info(f"总共 {total_pages} 页")
                            
                            # 处理每一页
                            current_page = start_page  # 从上次中断的地方开始
                            while current_page < total_pages:
                                try:
                                    # 等待页面加载完成
                                    WebDriverWait(self.driver, 10).until(
                                        EC.presence_of_element_located((By.CSS_SELECTOR, "input[name='sn[]']"))
                                    )
                                    
                                    # 点击全选
                                    select_all = WebDriverWait(self.driver, 10).until(
                                        EC.element_to_be_clickable((By.CSS_SELECTOR, "input#selectall[name='selectall']"))
                                    )
                                    if not select_all.is_selected():
                                        select_all.click()
                                    time.sleep(1)
                                    
                                    # 处理文件类型选项
                                    file_type_checkboxes = self.driver.find_elements(
                                        By.CSS_SELECTOR, 
                                        "input[name='docstype[]']"
                                    )
                                    # 取消选中所有类型
                                    for checkbox in file_type_checkboxes:
                                        if checkbox.is_selected():
                                            checkbox.click()
                                            time.sleep(0.5)
                                    
                                    # 只选中 DOC 类型
                                    doc_checkbox = self.driver.find_element(
                                        By.CSS_SELECTOR, 
                                        "input[name='docstype[]'][value='doc']"
                                    )
                                    if not doc_checkbox.is_selected():
                                        doc_checkbox.click()
                                    time.sleep(1)
                                    
                                    # 获取当前页的文件数量
                                    current_page_items = self.driver.find_elements(By.CSS_SELECTOR, "input[name='sn[]']")
                                    current_page_count = len(current_page_items)
                                    
                                    # 点击下载按钮
                                    try:
                                        download_button = self.driver.find_element(By.CSS_SELECTOR, "input#zipdownloadbutton")
                                        download_button.click()
                                        time.sleep(max(5, current_page_count * 0.5))  # 等待下载完成
                                        success_count += current_page_count
                                        downloaded_count += current_page_count
                                        logging.info(f"已下载第 {current_page + 1}/{total_pages} 页，{current_page_count} 个文件")
                                    except Exception as e:
                                        logging.error(f"下载失败: {str(e)}")
                                        failed_count += current_page_count
                                    
                                    # 保存当前进度
                                    self.save_progress(lecture_no, "in_progress", current_page)
                                    
                                    current_page += 1
                                    
                                except Exception as e:
                                    logging.error(f"处理第 {current_page + 1} 页时出错: {str(e)}")
                                    failed_count += current_page_count
                                    # 保存出错状态
                                    self.save_progress(lecture_no, "error", current_page)
                                    break
                            
                            # 完成后标记为已完成
                            if current_page >= total_pages:
                                self.save_progress(lecture_no, "completed")
                                
                            logging.info(f"讲座 {lecture_no} 全部 {total_count} 个文件下载完成")
                        except Exception as e:
                            logging.error(f"处理分页时出错: {str(e)}")
                            self.save_progress(lecture_no, "error", current_page)
                    else:
                        logging.info(f"讲座 {lecture_no} 没有可下载的文件")
                    
                except TimeoutException:
                    logging.info(f"讲座 {lecture_no} 未找到任何结果")
                except Exception as e:
                    logging.error(f"处理搜索结果时出错: {str(e)}")
                
                # 检查是否需要创建新的日志文件
                self.log_count += 1
                if self.log_count >= self.log_file_max_lines:
                    self.create_new_log_file()
                    
            except TimeoutException as e:
                logging.error(f"页面元素等待超时: {str(e)}")
            except Exception as e:
                logging.error(f"处理过程中出错: {str(e)}")
                
            # 在处理完成后写入统计信息
            self.write_stats(
                lecture_no=lecture_no,
                total_count=total_count,
                downloaded_count=downloaded_count,
                success_count=success_count,
                failed_count=failed_count
            )
            
        except Exception as e:
            logging.error(f"处理讲座 {lecture_no} 时出错: {str(e)}")
            # 发生错误时也记录统计信息
            self.write_stats(
                lecture_no=lecture_no,
                total_count=total_count,
                downloaded_count=downloaded_count,
                success_count=success_count,
                failed_count=failed_count
            )
            
    def close(self):
        """关闭浏览器"""
        self.driver.quit() 