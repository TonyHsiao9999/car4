from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from .config import USER_AGENT, WAIT_TIMES

def setup_driver():
    """設置並返回 Chrome WebDriver"""
    chrome_options = Options()
    chrome_options.add_argument(f'user-agent={USER_AGENT}')
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    
    service = Service()
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.set_window_size(1920, 1080)
    return driver

def print_debug_info(driver, locator, error=None):
    """印出除錯資訊，限制輸出長度"""
    print("\n=== 除錯資訊 ===")
    print(f"當前頁面標題: {driver.title}")
    print(f"當前頁面URL: {driver.current_url}")
    print(f"目標元素: {locator}")
    
    if error:
        print(f"錯誤訊息: {error}")
    
    # 印出頁面中所有按鈕的數量
    buttons = driver.find_elements("tag name", "button")
    print(f"頁面按鈕數量: {len(buttons)}")
    
    # 印出頁面中所有輸入框的數量
    inputs = driver.find_elements("tag name", "input")
    print(f"頁面輸入框數量: {len(inputs)}")
    
    # 印出頁面中所有連結的數量
    links = driver.find_elements("tag name", "a")
    print(f"頁面連結數量: {len(links)}")
    
    print("================\n")

def wait_for_element(driver, locator, timeout=WAIT_TIMES["element"]):
    """等待元素出現並返回"""
    try:
        element = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located(locator)
        )
        return element
    except TimeoutException:
        print_debug_info(driver, locator, "等待元素超時")
        return None

def safe_click(driver, locator, timeout=WAIT_TIMES["element"]):
    """安全地點擊元素"""
    element = wait_for_element(driver, locator, timeout)
    if element:
        try:
            print(f"找到元素: {locator}")
            print(f"元素可見性: {element.is_displayed()}")
            print(f"元素可點擊性: {element.is_enabled()}")
            element.click()
            return True
        except Exception as e:
            print_debug_info(driver, locator, f"點擊元素時發生錯誤: {e}")
    return False 