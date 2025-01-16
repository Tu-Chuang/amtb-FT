from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
import time
import os
from selenium.webdriver.chrome.options import Options
from pathlib import Path

class AmtbCrawler:
    def __init__(self):
        self.base_url = "https://ft.amtb.tw/"
        # 使用固定路径
        self.base_dir = Path('/root/amtb')
        
    def setup_driver(self, code_dir):
        """
        设置浏览器，指定下载目录
        """
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-software-rasterizer')
        
        # 设置下载选项，使用绝对路径
        prefs = {
            "download.default_directory": str(code_dir),
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True
        }
        options.add_experimental_option("prefs", prefs)
        
        # 在 Linux 上可能需要指定 chrome 二进制文件位置
        options.binary_location = "/usr/bin/google-chrome"
        
        return webdriver.Chrome(options=options)

    def crawl(self, code, max_retries=3):
        """
        抓取指定代码的内容，支持重试
        """
        for attempt in range(max_retries):
            try:
                # 创建编号对应的目录，使用 Path
                code_dir = self.base_dir / "downloads" / code
                code_dir.mkdir(parents=True, exist_ok=True)
                print(f"创建目录: {code_dir}")
                
                # 初始化浏览器
                self.driver = self.setup_driver(code_dir)
                
                try:
                    # 打开网页
                    self.driver.get(self.base_url)
                    
                    # 等待并选择"编号"搜索模式
                    select_element = WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.ID, "srange"))
                    )
                    Select(select_element).select_by_value("sn")
                    
                    # 输入编号
                    search_box = self.driver.find_element(By.ID, "query")
                    search_box.clear()
                    search_box.send_keys(code)
                    
                    # 点击搜索
                    search_button = self.driver.find_element(By.ID, "searchButton")
                    search_button.click()
                    time.sleep(2)
                    
                    # 处理每一页
                    current_page = 0
                    total_downloaded = 0
                    
                    while True:
                        try:
                            # 取消所有格式选择
                            checkboxes = self.driver.find_elements(By.NAME, "docstype[]")
                            for checkbox in checkboxes:
                                if checkbox.is_selected():
                                    checkbox.click()
                            
                            # 选择DOC格式
                            doc_checkbox = self.driver.find_element(By.ID, "docstype_3")
                            if not doc_checkbox.is_selected():
                                doc_checkbox.click()
                            
                            # 点击全选
                            select_all = self.driver.find_element(By.NAME, "selectall")
                            select_all.click()
                            
                            # 获取当前页面条目数
                            items = self.driver.find_elements(By.NAME, "sn[]")
                            total_downloaded += len(items)
                            
                            # 点击下载
                            download_button = self.driver.find_element(By.ID, "zipdownloadbutton")
                            download_button.click()
                            
                            def wait_for_download(directory, timeout=300):
                                start_time = time.time()
                                while time.time() - start_time < timeout:
                                    # 使用 Path 来检查文件
                                    if not any(f.suffix in ['.crdownload', '.tmp'] 
                                             for f in Path(directory).iterdir()):
                                        if any(f.is_file() for f in Path(directory).iterdir()):
                                            return True
                                    time.sleep(1)
                                return False
                            
                            if not wait_for_download(code_dir):
                                print(f"下载超时: {code}")
                                return 0
                            
                            print(f"下载第 {current_page + 1} 页，{len(items)} 个文件")
                            
                            # 检查下一页
                            try:
                                next_button = self.driver.find_element(By.CSS_SELECTOR, ".pagination li:last-child:not(.disabled) a")
                                next_button.click()
                                time.sleep(2)
                                current_page += 1
                            except:
                                print(f"编号 {code} 下载完成，共 {total_downloaded} 个文件")
                                break
                                
                        except Exception as e:
                            print(f"处理页面时出错: {str(e)}")
                            break
                    
                    return total_downloaded
                    
                finally:
                    self.driver.quit()
            except Exception as e:
                if attempt < max_retries - 1:
                    print(f"下载失败，正在重试 ({attempt + 1}/{max_retries}): {str(e)}")
                    time.sleep(5 * (attempt + 1))
                    continue
                else:
                    print(f"处理编号 {code} 时出错: {str(e)}")
                    return 0

    def get_total_pages(self, code):
        """
        获取指定编号的总页数
        """
        try:
            # 初始化临时浏览器
            temp_driver = webdriver.Chrome(options=self.setup_driver("").options)
            
            try:
                # 打开网页
                temp_driver.get(self.base_url)
                
                # 等待并选择"编号"搜索模式
                select_element = WebDriverWait(temp_driver, 10).until(
                    EC.presence_of_element_located((By.ID, "srange"))
                )
                Select(select_element).select_by_value("sn")
                
                # 输入编号
                search_box = temp_driver.find_element(By.ID, "query")
                search_box.clear()
                search_box.send_keys(code)
                
                # 点击搜索
                search_button = temp_driver.find_element(By.ID, "searchButton")
                search_button.click()
                time.sleep(2)
                
                # 获取分页信息
                pagination = temp_driver.find_elements(By.CSS_SELECTOR, ".pagination li:not(.disabled)")
                if pagination:
                    return len(pagination) - 1  # 减去"下一页"按钮
                return 1
                
            finally:
                temp_driver.quit()
                
        except Exception as e:
            print(f"获取页数时出错: {str(e)}")
            return 0

def main():
    # 使用固定路径
    base_dir = Path('/root/amtb')
    downloads_dir = base_dir / "downloads"
    downloads_dir.mkdir(exist_ok=True)
    
    # 读取编号列表
    lecture_numbers_file = base_dir / "lecture_numbers.md"
    with open(lecture_numbers_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        codes = [line.strip() for line in lines if line.strip()]
    
    # 读取已完成的下载记录
    completed_codes = set()
    log_file = base_dir / "download_log.txt"
    if log_file.exists():
        with open(log_file, 'r', encoding='utf-8') as f:
            for line in f:
                if "成功下载" in line:
                    code = line.split(']')[1].split(':')[0].strip()
                    completed_codes.add(code)
    
    # 过滤掉已完成的编号
    remaining_codes = [code for code in codes if code not in completed_codes]
    
    print(f"总共 {len(codes)} 个编号")
    print(f"已完成 {len(completed_codes)} 个")
    print(f"剩余 {len(remaining_codes)} 个需要下载")
    
    if not remaining_codes:
        print("所有下载已完成！")
        return
    
    # 开始下载
    crawler = AmtbCrawler()
    failed_codes = []
    
    # 创建日志文件
    log_file = base_dir / "download_log.txt"
    current_time = time.strftime("%Y-%m-%d %H:%M:%S")
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(f"\n=== 断点续传会话开始于 {current_time} ===\n")
    
    total_codes = len(remaining_codes)
    successful_downloads = 0
    
    for i, code in enumerate(remaining_codes, 1):
        # 获取总页数
        total_pages = crawler.get_total_pages(code)
        print(f"\n[{i}/{total_codes}] 处理编号: {code} (预计 {total_pages} 页)")
        
        try:
            downloaded = crawler.crawl(code)
            if downloaded > 0:
                successful_downloads += 1
                success_rate = (successful_downloads / i) * 100
                status = f"[{current_time}] {code}: 成功下载 {downloaded} 个文件 "
                status += f"(总进度: {i}/{total_codes}, 成功率: {success_rate:.1f}%)"
                
                # 写入日志
                with open(log_file, 'a', encoding='utf-8') as f:
                    f.write(status + '\n')
                
                print(status)
            else:
                failed_codes.append(code)
                # 记录失败
                with open(log_file, 'a', encoding='utf-8') as f:
                    f.write(f"[{current_time}] {code}: 下载失败\n")
                
        except Exception as e:
            error_msg = f"[{current_time}] {code}: 发生错误 - {str(e)}"
            print(error_msg)
            failed_codes.append(code)
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(error_msg + '\n')
        
        # 记录失败的编号到单独文件
        failed_codes_file = base_dir / "failed_codes.txt"
        if failed_codes:
            with open(failed_codes_file, 'w', encoding='utf-8') as f:
                f.write("\n".join(failed_codes))
        
        time.sleep(3)  # 防止请求过快
    
    # 记录会话结束状态
    end_time = time.strftime("%Y-%m-%d %H:%M:%S")
    summary = f"""
=== 下载会话结束于 {end_time} ===
本次下载:
  总数: {total_codes}
  成功: {successful_downloads}
  失败: {len(failed_codes)}
  成功率: {(successful_downloads/total_codes)*100:.1f}%
所有编号:
  总数: {len(codes)}
  已完成: {len(completed_codes) + successful_downloads}
  剩余: {len(codes) - (len(completed_codes) + successful_downloads)}
"""
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(summary)
    print(summary)

if __name__ == "__main__":
    main() 