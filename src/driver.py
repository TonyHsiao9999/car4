from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from .config import USER_AGENT, WAIT_TIMES
import os
import time

def setup_driver(test_mode=False):
    """設置並返回 Chrome WebDriver"""
    chrome_options = Options()
    chrome_options.add_argument(f'user-agent={USER_AGENT}')
    
    # 測試模式下不使用無頭模式
    if not test_mode:
        chrome_options.add_argument('--headless')
    
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    
    service = Service()
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.set_window_size(1920, 1080)
    return driver

def get_page_info(driver):
    """獲取頁面資訊"""
    try:
        # 獲取頁面標題
        title = driver.title
        
        # 獲取當前URL
        url = driver.current_url
        
        # 獲取所有按鈕的文字
        buttons = driver.find_elements("tag name", "button")
        button_texts = [btn.text for btn in buttons if btn.text]
        
        # 獲取所有輸入框的屬性
        inputs = driver.find_elements("tag name", "input")
        input_info = []
        for input_elem in inputs:
            input_type = input_elem.get_attribute("type")
            input_id = input_elem.get_attribute("id")
            input_name = input_elem.get_attribute("name")
            if any([input_type, input_id, input_name]):
                input_info.append({
                    "type": input_type,
                    "id": input_id,
                    "name": input_name
                })
        
        return {
            "title": title,
            "url": url,
            "button_texts": button_texts,
            "input_elements": input_info
        }
    except Exception as e:
        return {"error": str(e)}

def print_debug_info(driver, locator, error=None):
    """印出除錯資訊，只顯示關鍵資訊"""
    print("\n=== 除錯資訊 ===")
    
    # 獲取頁面資訊
    page_info = get_page_info(driver)
    
    # 印出基本資訊
    print(f"當前頁面標題: {page_info['title']}")
    print(f"當前頁面URL: {page_info['url']}")
    print(f"目標元素: {locator}")
    
    if error:
        print(f"錯誤訊息: {error}")
    
    # 印出按鈕資訊
    print("\n頁面按鈕:")
    for text in page_info['button_texts']:
        print(f"- {text}")
    
    # 印出輸入框資訊
    print("\n頁面輸入框:")
    for input_elem in page_info['input_elements']:
        print(f"- 類型: {input_elem['type']}, ID: {input_elem['id']}, 名稱: {input_elem['name']}")
    
    print("\n================\n")

def wait_for_element(driver, locator, timeout=WAIT_TIMES["element"]):
    """等待元素出現並返回"""
    try:
        # 使用 try-except 來捕獲可能的頁面原始碼輸出
        try:
            element = WebDriverWait(driver, timeout).until(
                EC.presence_of_element_located(locator)
            )
            return element
        except Exception as e:
            # 如果發生錯誤，只輸出我們自己的除錯資訊
            print_debug_info(driver, locator, f"等待元素超時: {str(e)}")
            return None
    except Exception as e:
        print_debug_info(driver, locator, f"等待元素時發生錯誤: {str(e)}")
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