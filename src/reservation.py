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
    driver.page.screenshot(path=filename)
    print(f"已儲存截圖: {filename}")

def login(driver, username, password):
    """登入系統"""
    print_debug_info(driver, "開始登入流程")
    
    # 輸入帳號
    print_debug_info(driver, "準備輸入帳號")
    try:
        driver.page.wait_for_selector("#username", timeout=WAIT_TIMES["element"]*1000)
        driver.page.fill("#username", username)
        print_debug_info(driver, "已輸入帳號")
    except Exception as e:
        print_debug_info(driver, f"找不到帳號輸入框: {e}")
        take_screenshot(driver, "login_username_not_found")
        return False
    
    # 輸入密碼
    print_debug_info(driver, "準備輸入密碼")
    try:
        driver.page.fill("#password", password)
        print_debug_info(driver, "已輸入密碼")
    except Exception as e:
        print_debug_info(driver, f"找不到密碼輸入框: {e}")
        take_screenshot(driver, "login_password_not_found")
        return False
    
    # 點擊登入按鈕
    print_debug_info(driver, "準備點擊登入按鈕")
    try:
        driver.page.click("button[type='submit']")
        print_debug_info(driver, "已點擊登入按鈕")
    except Exception as e:
        print_debug_info(driver, f"登入按鈕點擊失敗: {e}")
        take_screenshot(driver, "login_button_click_failed")
        return False
    
    # 等待登入成功
    print_debug_info(driver, "等待登入成功")
    try:
        driver.page.wait_for_url("**/dashboard**", timeout=WAIT_TIMES["page_load"]*1000)
        print_debug_info(driver, "登入成功")
        return True
    except Exception as e:
        print_debug_info(driver, f"登入超時: {e}")
        take_screenshot(driver, "login_timeout")
        return False

def navigate_to_reservation(driver):
    """導航到預約頁面"""
    print_debug_info(driver, "準備導航到預約頁面")
    
    # 點擊預約按鈕
    print_debug_info(driver, "準備點擊預約按鈕")
    try:
        driver.page.click("a:has-text('預約')")
        print_debug_info(driver, "已點擊預約按鈕")
    except Exception as e:
        print_debug_info(driver, f"預約按鈕點擊失敗: {e}")
        take_screenshot(driver, "reservation_button_click_failed")
        return False
    
    # 等待預約頁面載入
    print_debug_info(driver, "等待預約頁面載入")
    try:
        driver.page.wait_for_url("**/reservation**", timeout=WAIT_TIMES["page_load"]*1000)
        print_debug_info(driver, "預約頁面載入成功")
        return True
    except Exception as e:
        print_debug_info(driver, f"預約頁面載入超時: {e}")
        take_screenshot(driver, "reservation_page_timeout")
        return False

def select_date(driver, target_date):
    """選擇日期"""
    print_debug_info(driver, f"準備選擇日期: {target_date}")
    
    # 等待日期選擇器出現
    print_debug_info(driver, "等待日期選擇器")
    try:
        driver.page.wait_for_selector(".date-picker", timeout=WAIT_TIMES["element"]*1000)
        print_debug_info(driver, "找到日期選擇器")
    except Exception as e:
        print_debug_info(driver, f"找不到日期選擇器: {e}")
        take_screenshot(driver, "date_picker_not_found")
        return False
    
    # 點擊日期選擇器
    print_debug_info(driver, "準備點擊日期選擇器")
    try:
        driver.page.click(".date-picker")
        print_debug_info(driver, "已點擊日期選擇器")
    except Exception as e:
        print_debug_info(driver, f"日期選擇器點擊失敗: {e}")
        take_screenshot(driver, "date_picker_click_failed")
        return False
    
    # 選擇目標日期
    print_debug_info(driver, f"準備選擇目標日期: {target_date}")
    try:
        driver.page.click(f"td[data-date='{target_date}']")
        print_debug_info(driver, "已選擇目標日期")
        return True
    except Exception as e:
        print_debug_info(driver, f"目標日期點擊失敗: {e}")
        take_screenshot(driver, "target_date_click_failed")
        return False

def select_time_slot(driver, time_slot):
    """選擇時段"""
    print_debug_info(driver, f"準備選擇時段: {time_slot}")
    
    # 等待時段列表載入
    print_debug_info(driver, "等待時段列表")
    try:
        driver.page.wait_for_selector(".time-slots", timeout=WAIT_TIMES["element"]*1000)
        print_debug_info(driver, "找到時段列表")
    except Exception as e:
        print_debug_info(driver, f"找不到時段列表: {e}")
        take_screenshot(driver, "time_slots_not_found")
        return False
    
    # 選擇指定時段
    print_debug_info(driver, f"準備點擊時段: {time_slot}")
    try:
        driver.page.click(f".time-slot:has-text('{time_slot}')")
        print_debug_info(driver, "已選擇時段")
        return True
    except Exception as e:
        print_debug_info(driver, f"時段點擊失敗: {e}")
        take_screenshot(driver, "time_slot_click_failed")
        return False

def confirm_reservation(driver):
    """確認預約"""
    print_debug_info(driver, "準備確認預約")
    
    # 點擊確認按鈕
    print_debug_info(driver, "準備點擊確認按鈕")
    try:
        driver.page.click("button:has-text('確認預約')")
        print_debug_info(driver, "已點擊確認按鈕")
    except Exception as e:
        print_debug_info(driver, f"確認按鈕點擊失敗: {e}")
        take_screenshot(driver, "confirm_button_click_failed")
        return False
    
    # 等待確認成功
    print_debug_info(driver, "等待確認成功")
    try:
        driver.page.wait_for_selector(".success-message", timeout=WAIT_TIMES["element"]*1000)
        print_debug_info(driver, "預約確認成功")
        return True
    except Exception as e:
        print_debug_info(driver, f"預約確認超時: {e}")
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
        print_debug_info(driver, "預約確認成功")
        
        print_debug_info(driver, "預約流程完成")
        return True
        
    except Exception as e:
        print_debug_info(driver, f"預約流程發生錯誤: {e}")
        take_screenshot(driver, "reservation_error")
        return False
        
    finally:
        if driver:
            driver.quit()
            print_debug_info(None, "瀏覽器已關閉") 