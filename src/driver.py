from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from .config import USER_AGENT, WAIT_TIMES
import os
import time
import logging
import sys
from io import StringIO

# 設置 Selenium 的日誌級別
logging.getLogger('selenium').setLevel(logging.ERROR)
logging.getLogger('urllib3').setLevel(logging.ERROR)

def setup_driver(test_mode=False):
    """設置並返回 Chrome WebDriver"""
    chrome_options = Options()
    chrome_options.add_argument(f'user-agent={USER_AGENT}')
    
    # 測試模式下不使用無頭模式
    if not test_mode:
        chrome_options.add_argument('--headless')
    
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--log-level=3')  # 只顯示致命錯誤
    chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
    
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
        element = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located(locator)
        )
        return element
    except Exception as e:
        # 只輸出錯誤訊息，不輸出頁面原始碼
        error_msg = str(e)
        if "Message: " in error_msg:
            error_msg = error_msg.split("Message: ")[1]
        print_debug_info(driver, locator, f"等待元素超時: {error_msg}")
        return None

def safe_click(driver, locator, timeout=WAIT_TIMES["element"]):
    """安全地點擊元素"""
    element = wait_for_element(driver, locator, timeout)
    if element:
        try:
            print_debug_info(driver, locator, "找到元素")
            element.click()
            return True
        except Exception as e:
            error_msg = str(e)
            if "Message: " in error_msg:
                error_msg = error_msg.split("Message: ")[1]
            print_debug_info(driver, locator, f"點擊元素時發生錯誤: {error_msg}")
    return False 