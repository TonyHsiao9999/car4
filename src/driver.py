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

def wait_for_element(driver, locator, timeout=WAIT_TIMES["element"]):
    """等待元素出現並返回"""
    try:
        element = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located(locator)
        )
        return element
    except TimeoutException:
        print(f"等待元素超時: {locator}")
        # 印出當前頁面標題和URL，而不是整個原始碼
        print(f"當前頁面標題: {driver.title}")
        print(f"當前頁面URL: {driver.current_url}")
        return None

def safe_click(driver, locator, timeout=WAIT_TIMES["element"]):
    """安全地點擊元素"""
    element = wait_for_element(driver, locator, timeout)
    if element:
        try:
            # 印出元素的關鍵屬性，而不是整個元素
            print(f"找到元素: {locator}")
            print(f"元素可見性: {element.is_displayed()}")
            print(f"元素可點擊性: {element.is_enabled()}")
            element.click()
            return True
        except Exception as e:
            print(f"點擊元素時發生錯誤: {e}")
            # 印出錯誤發生時的頁面狀態
            print(f"錯誤發生時的頁面標題: {driver.title}")
            print(f"錯誤發生時的頁面URL: {driver.current_url}")
    return False 