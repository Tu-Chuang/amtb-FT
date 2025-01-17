from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def test_browser():
    print("开始测试浏览器...")
    try:
        options = webdriver.ChromeOptions()
        driver = webdriver.Chrome(options=options)
        print("Chrome浏览器启动成功")
        
        driver.get("https://ft.amtb.tw/")
        print("网页访问成功")
        
        # 测试页面元素
        search_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[name='query']"))
        )
        print("搜索框定位成功")
        
        driver.quit()
        print("测试完成")
        
    except Exception as e:
        print(f"测试失败: {str(e)}")

if __name__ == "__main__":
    test_browser() 