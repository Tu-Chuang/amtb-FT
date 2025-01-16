from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
import time
import os
from selenium.webdriver.chrome.options import Options

def get_last_successful_code(filename):
    """
    从文件中获取最后一个成功下载的编号
    """
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # 从后往前查找第一个有下载记录的编号
        for line in reversed(lines):
            if '#' in line and '已下载' in line:
                return line.split()[0]
    except:
        pass
    return None

class AmtbCrawler:
    def __init__(self, project_dir=None):
        self.base_url = "https://ft.amtb.tw/"
        # 如果没有指定目录，使用默认目录
        self.project_dir = project_dir or "/root/amtb_project"
        print(f"工作目录设置为: {self.project_dir}")
        
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
        options.add_argument('--remote-debugging-port=9222')
        
        # 设置下载选项，使用绝对路径
        prefs = {
            "download.default_directory": code_dir,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True,
            "profile.default_content_settings.popups": 0,
            "profile.default_content_setting_values.automatic_downloads": 1
        }
        options.add_experimental_option("prefs", prefs)
        
        # 添加日志级别
        options.add_argument('--log-level=3')
        
        return webdriver.Chrome(options=options)

    def crawl(self, code):
        """
        抓取指定代码的内容
        """
        # 使用绝对路径创建目录
        code_dir = os.path.join(self.project_dir, "downloads", code)
        os.makedirs(code_dir, exist_ok=True)
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
                    
                    # 等待下载完成
                    time.sleep(5)
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
            
        except Exception as e:
            print(f"处理编号 {code} 时出错: {str(e)}")
            return 0
            
        finally:
            self.driver.quit()

def main():
    # 可以在这里指定项目目录
    project_dir = "/root/amtb_project"  # 可以根据需要修改这个路径
    
    # 创建主下载目录
    downloads_dir = os.path.join(project_dir, "downloads")
    os.makedirs(downloads_dir, exist_ok=True)
    
    # 读取编号列表
    lecture_numbers_file = os.path.join(project_dir, "lecture_numbers.md")
    with open(lecture_numbers_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()[1:]  # 跳过标题行
        codes = [line.strip() for line in lines if line.strip()]
    
    # 获取上次下载到的位置
    last_code = get_last_successful_code(lecture_numbers_file)
    if last_code and last_code in codes:
        start_index = codes.index(last_code) + 1
        print(f"从上次中断的位置继续下载（{last_code}之后）")
        codes = codes[start_index:]
        print(f"剩余 {len(codes)} 个编号需要下载")
    else:
        print(f"总共 {len(codes)} 个编号需要下载")
    
    # 开始下载
    crawler = AmtbCrawler(project_dir)
    failed_codes = []
    
    for i, code in enumerate(codes, 1):
        print(f"\n处理第 {i}/{len(codes)} 个编号: {code}")
        
        try:
            downloaded = crawler.crawl(code)
            if downloaded > 0:
                # 更新记录
                with open(lecture_numbers_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                
                for j, line in enumerate(lines):
                    if line.strip().startswith(code):
                        lines[j] = f"{code} # 已下载 {downloaded} 个文件\n"
                        break
                
                with open(lecture_numbers_file, 'w', encoding='utf-8') as f:
                    f.writelines(lines)
            else:
                failed_codes.append(code)
                
        except Exception as e:
            print(f"处理编号 {code} 时发生错误: {str(e)}")
            failed_codes.append(code)
        
        # 记录失败的编号
        if failed_codes:
            failed_codes_file = os.path.join(project_dir, "failed_codes.txt")
            with open(failed_codes_file, 'w', encoding='utf-8') as f:
                f.write("\n".join(failed_codes))
        
        time.sleep(3)  # 防止请求过快

if __name__ == "__main__":
    main()