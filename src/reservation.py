from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from .driver import setup_driver, wait_for_element, safe_click, print_debug_info
from .config import WAIT_TIMES
import time
import os
from datetime import datetime

def take_screenshot(driver, prefix="error"):
    """在錯誤發生時截圖"""
    if not os.path.exists("screenshots"):
        os.makedirs("screenshots")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"screenshots/{prefix}_{timestamp}.png"
    driver.save_screenshot(filename)
    print(f"已儲存截圖: {filename}")

def login(driver, username, password):
    """登入系統"""
    print_debug_info(driver, "開始登入流程")
    
    # 輸入帳號
    print_debug_info(driver, "準備輸入帳號")
    username_input = wait_for_element(driver, (By.ID, "username"))
    if not username_input:
        print_debug_info(driver, "找不到帳號輸入框")
        take_screenshot(driver, "login_username_not_found")
        return False
    username_input.send_keys(username)
    print_debug_info(driver, "已輸入帳號")
    
    # 輸入密碼
    print_debug_info(driver, "準備輸入密碼")
    password_input = wait_for_element(driver, (By.ID, "password"))
    if not password_input:
        print_debug_info(driver, "找不到密碼輸入框")
        take_screenshot(driver, "login_password_not_found")
        return False
    password_input.send_keys(password)
    print_debug_info(driver, "已輸入密碼")
    
    # 點擊登入按鈕
    print_debug_info(driver, "準備點擊登入按鈕")
    if not safe_click(driver, (By.CSS_SELECTOR, "button[type='submit']")):
        print_debug_info(driver, "登入按鈕點擊失敗")
        take_screenshot(driver, "login_button_click_failed")
        return False
    print_debug_info(driver, "已點擊登入按鈕")
    
    # 等待登入成功
    print_debug_info(driver, "等待登入成功")
    try:
        WebDriverWait(driver, WAIT_TIMES["page"]).until(
            EC.url_contains("dashboard")
        )
        print_debug_info(driver, "登入成功")
        return True
    except TimeoutException:
        print_debug_info(driver, "登入超時")
        take_screenshot(driver, "login_timeout")
        return False

def navigate_to_reservation(driver):
    """導航到預約頁面"""
    print_debug_info(driver, "準備導航到預約頁面")
    
    # 點擊預約按鈕
    print_debug_info(driver, "準備點擊預約按鈕")
    if not safe_click(driver, (By.XPATH, "//a[contains(text(), '預約')]")):
        print_debug_info(driver, "預約按鈕點擊失敗")
        take_screenshot(driver, "reservation_button_click_failed")
        return False
    print_debug_info(driver, "已點擊預約按鈕")
    
    # 等待預約頁面載入
    print_debug_info(driver, "等待預約頁面載入")
    try:
        WebDriverWait(driver, WAIT_TIMES["page"]).until(
            EC.url_contains("reservation")
        )
        print_debug_info(driver, "預約頁面載入成功")
        return True
    except TimeoutException:
        print_debug_info(driver, "預約頁面載入超時")
        take_screenshot(driver, "reservation_page_timeout")
        return False

def select_date(driver, target_date):
    """選擇日期"""
    print_debug_info(driver, f"準備選擇日期: {target_date}")
    
    # 等待日期選擇器出現
    print_debug_info(driver, "等待日期選擇器")
    date_picker = wait_for_element(driver, (By.CLASS_NAME, "date-picker"))
    if not date_picker:
        print_debug_info(driver, "找不到日期選擇器")
        take_screenshot(driver, "date_picker_not_found")
        return False
    print_debug_info(driver, "找到日期選擇器")
    
    # 點擊日期選擇器
    print_debug_info(driver, "準備點擊日期選擇器")
    if not safe_click(driver, (By.CLASS_NAME, "date-picker")):
        print_debug_info(driver, "日期選擇器點擊失敗")
        take_screenshot(driver, "date_picker_click_failed")
        return False
    print_debug_info(driver, "已點擊日期選擇器")
    
    # 選擇目標日期
    print_debug_info(driver, f"準備選擇目標日期: {target_date}")
    date_element = wait_for_element(driver, (By.XPATH, f"//td[@data-date='{target_date}']"))
    if not date_element:
        print_debug_info(driver, "找不到目標日期")
        take_screenshot(driver, "target_date_not_found")
        return False
    
    if not safe_click(driver, (By.XPATH, f"//td[@data-date='{target_date}']")):
        print_debug_info(driver, "目標日期點擊失敗")
        take_screenshot(driver, "target_date_click_failed")
        return False
    print_debug_info(driver, "已選擇目標日期")
    return True

def select_time_slot(driver, time_slot):
    """選擇時段"""
    print_debug_info(driver, f"準備選擇時段: {time_slot}")
    
    # 等待時段列表載入
    print_debug_info(driver, "等待時段列表")
    time_slots = wait_for_element(driver, (By.CLASS_NAME, "time-slots"))
    if not time_slots:
        print_debug_info(driver, "找不到時段列表")
        take_screenshot(driver, "time_slots_not_found")
        return False
    print_debug_info(driver, "找到時段列表")
    
    # 選擇指定時段
    print_debug_info(driver, f"準備點擊時段: {time_slot}")
    time_element = wait_for_element(driver, (By.XPATH, f"//div[contains(@class, 'time-slot') and contains(text(), '{time_slot}')]"))
    if not time_element:
        print_debug_info(driver, "找不到指定時段")
        take_screenshot(driver, "time_slot_not_found")
        return False
    
    if not safe_click(driver, (By.XPATH, f"//div[contains(@class, 'time-slot') and contains(text(), '{time_slot}')]")):
        print_debug_info(driver, "時段點擊失敗")
        take_screenshot(driver, "time_slot_click_failed")
        return False
    print_debug_info(driver, "已選擇時段")
    return True

def confirm_reservation(driver):
    """確認預約"""
    print_debug_info(driver, "準備確認預約")
    
    # 點擊確認按鈕
    print_debug_info(driver, "準備點擊確認按鈕")
    if not safe_click(driver, (By.XPATH, "//button[contains(text(), '確認預約')]")):
        print_debug_info(driver, "確認按鈕點擊失敗")
        take_screenshot(driver, "confirm_button_click_failed")
        return False
    print_debug_info(driver, "已點擊確認按鈕")
    
    # 等待確認成功
    print_debug_info(driver, "等待確認成功")
    try:
        success_message = WebDriverWait(driver, WAIT_TIMES["element"]).until(
            EC.presence_of_element_located((By.CLASS_NAME, "success-message"))
        )
        print_debug_info(driver, "預約確認成功")
        return True
    except TimeoutException:
        print_debug_info(driver, "預約確認超時")
        take_screenshot(driver, "confirmation_timeout")
        return False

def make_reservation(username, password, target_date, time_slot, test_mode=False):
    """執行預約流程"""
    print_debug_info(None, "開始預約流程")
    
    driver = setup_driver(test_mode)
    try:
        print_debug_info(driver, "瀏覽器已啟動")
        
        # 登入
        if not login(driver, username, password):
            print_debug_info(driver, "登入失敗")
            return False
        print_debug_info(driver, "登入成功")
        
        # 導航到預約頁面
        if not navigate_to_reservation(driver):
            print_debug_info(driver, "導航到預約頁面失敗")
            return False
        print_debug_info(driver, "已到達預約頁面")
        
        # 選擇日期
        if not select_date(driver, target_date):
            print_debug_info(driver, "選擇日期失敗")
            return False
        print_debug_info(driver, "日期選擇成功")
        
        # 選擇時段
        if not select_time_slot(driver, time_slot):
            print_debug_info(driver, "選擇時段失敗")
            return False
        print_debug_info(driver, "時段選擇成功")
        
        # 確認預約
        if not confirm_reservation(driver):
            print_debug_info(driver, "確認預約失敗")
            return False
        print_debug_info(driver, "預約流程完成")
        
        return True
    except Exception as e:
        print_debug_info(driver, f"預約過程發生錯誤: {str(e)}")
        take_screenshot(driver, "reservation_error")
        return False
    finally:
        driver.quit()
        print_debug_info(None, "瀏覽器已關閉") 