from playwright.sync_api import sync_playwright
from .config import USER_AGENT, WAIT_TIMES
import os
import time
import logging

# 設置日誌級別
logging.getLogger('playwright').setLevel(logging.ERROR)

def setup_driver(test_mode=False):
    """設置並返回 Playwright 瀏覽器"""
    try:
        playwright = sync_playwright().start()
        
        # 啟動瀏覽器
        browser = playwright.chromium.launch(
            headless=not test_mode,  # 測試模式下顯示瀏覽器
            args=[
                '--no-sandbox',
                '--disable-dev-shm-usage',
                '--disable-extensions',
                '--disable-gpu',
                '--single-process'
            ]
        )
        
        context = browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent=USER_AGENT
        )
        
        page = context.new_page()
        
        # 返回包裝的對象
        return PlaywrightWrapper(playwright, browser, context, page)
        
    except Exception as e:
        print(f"Playwright 初始化失敗: {e}")
        return None

class PlaywrightWrapper:
    """Playwright 包裝類，提供類似 Selenium 的介面"""
    
    def __init__(self, playwright, browser, context, page):
        self.playwright = playwright
        self.browser = browser
        self.context = context
        self.page = page
    
    def get(self, url):
        """導航到指定URL"""
        return self.page.goto(url, wait_until='networkidle')
    
    @property
    def title(self):
        """獲取頁面標題"""
        return self.page.title()
    
    @property
    def current_url(self):
        """獲取當前URL"""
        return self.page.url
    
    def set_window_size(self, width, height):
        """設置視窗大小"""
        self.page.set_viewport_size({'width': width, 'height': height})
    
    def find_elements(self, locator_type, locator_value):
        """查找元素（兼容Selenium介面）"""
        if locator_type == "tag name":
            return [PlaywrightElement(elem) for elem in self.page.query_selector_all(locator_value)]
        else:
            # 其他類型可以根據需要添加
            return []
    
    def quit(self):
        """關閉瀏覽器"""
        try:
            self.browser.close()
            self.playwright.stop()
        except:
            pass

class PlaywrightElement:
    """Playwright 元素包裝類"""
    
    def __init__(self, element):
        self.element = element
    
    @property
    def text(self):
        """獲取元素文字"""
        try:
            return self.element.inner_text()
        except:
            return ""
    
    def get_attribute(self, name):
        """獲取元素屬性"""
        try:
            return self.element.get_attribute(name)
        except:
            return None
    
    def click(self):
        """點擊元素"""
        return self.element.click()

def get_page_info(driver):
    """獲取頁面資訊"""
    try:
        # 獲取頁面標題
        title = driver.title
        
        # 獲取當前URL
        url = driver.current_url
        
        # 獲取所有按鈕的文字
        buttons = driver.page.query_selector_all('button')
        button_texts = []
        for btn in buttons:
            text = btn.inner_text()
            if text:
                button_texts.append(text)
        
        # 獲取所有輸入框的屬性
        inputs = driver.page.query_selector_all('input')
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

def wait_for_element(driver, selector, timeout=WAIT_TIMES["element"]):
    """等待元素出現並返回（Playwright版本）"""
    try:
        # 將Selenium格式的locator轉換為CSS選擇器
        if isinstance(selector, tuple):
            by, value = selector
            if by.lower() == 'id':
                css_selector = f'#{value}'
            elif by.lower() == 'class name':
                css_selector = f'.{value}'
            elif by.lower() == 'tag name':
                css_selector = value
            elif by.lower() == 'css selector':
                css_selector = value
            else:
                css_selector = value
        else:
            css_selector = selector
        
        driver.page.wait_for_selector(css_selector, timeout=timeout*1000)
        element = driver.page.query_selector(css_selector)
        return PlaywrightElement(element) if element else None
        
    except Exception as e:
        error_msg = str(e)
        print_debug_info(driver, selector, f"等待元素超時: {error_msg}")
        return None

def safe_click(driver, selector, timeout=WAIT_TIMES["element"]):
    """安全地點擊元素（Playwright版本）"""
    element = wait_for_element(driver, selector, timeout)
    if element:
        try:
            print_debug_info(driver, selector, "找到元素")
            element.click()
            return True
        except Exception as e:
            error_msg = str(e)
            print_debug_info(driver, selector, f"點擊元素時發生錯誤: {error_msg}")
    return False 