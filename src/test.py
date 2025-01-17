from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import sys

def test_browser():
    print("开始测试浏览器...")
    print(f"Python 版本: {sys.version}")
    
    try:
        print("正在配置 Chrome 选项...")
        options = webdriver.ChromeOptions()
        
        print("正在初始化 ChromeDriver...")
        service = Service(ChromeDriverManager().install())
        
        print("正在启动 Chrome 浏览器...")
        driver = webdriver.Chrome(service=service, options=options)
        print("Chrome浏览器启动成功")
        
        print("正在访问测试网页...")
        driver.get("https://ft.amtb.tw/")
        print("网页访问成功")
        
        print("正在测试页面元素...")
        search_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[name='query']"))
        )
        print("搜索框定位成功")
        
        driver.quit()
        print("测试完成")
        
    except Exception as e:
        print(f"测试失败: {str(e)}")
        print(f"错误类型: {type(e).__name__}")
        if driver:
            driver.quit()

if __name__ == "__main__":
    test_browser() 