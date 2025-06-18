from flask import Flask, jsonify, send_file, send_from_directory
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import os
from dotenv import load_dotenv
from selenium.webdriver.common.action_chains import ActionChains

app = Flask(__name__, static_folder='static')

def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
    chrome_options.add_argument('--log-level=3')
    chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
    
    # Zeabur 環境設定
    if os.path.exists('/usr/bin/google-chrome'):
        chrome_options.binary_location = '/usr/bin/google-chrome'
        service = Service('/usr/local/bin/chromedriver')
    elif os.path.exists('/usr/bin/chromium'):
        chrome_options.binary_location = '/usr/bin/chromium'
        service = Service('/usr/bin/chromedriver')
    else:
        # 如果沒有安裝 Chrome，使用 webdriver-manager
        try:
            from webdriver_manager.chrome import ChromeDriverManager
            service = Service(ChromeDriverManager().install())
        except:
            # 最後備案：使用系統預設
            service = Service()
    
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

def wait_for_element(driver, by, value, timeout=30):
    """等待元素出現並返回"""
    try:
        element = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((by, value))
        )
        return element
    except TimeoutException:
        print(f"等待元素超時: {by}={value}")
        driver.save_screenshot('timeout.png')
        return None

def make_reservation():
    driver = setup_driver()
    screenshot_count = 0
    
    def take_screenshot(description):
        nonlocal screenshot_count
        screenshot_count += 1
        filename = f'step_{screenshot_count:03d}_{description}.png'
        driver.save_screenshot(filename)
        print(f"截圖 {screenshot_count}: {description} - {filename}")
        return filename
    
    try:
        driver.get("https://www.ntpc.ltc-car.org/")
        print("已載入網頁，等待頁面載入...")
        take_screenshot("page_loaded")
        
        # 等待頁面完全載入
        WebDriverWait(driver, 30).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
        print("頁面已完全載入")
        take_screenshot("page_complete")
        
        # 等待浮動視窗出現
        print("等待浮動視窗出現...")
        try:
            # 先等待浮動視窗出現
            WebDriverWait(driver, 10).until(
                lambda d: len(d.find_elements(By.XPATH, "//*[contains(text(), '我知道了')]")) > 0
            )
            print("浮動視窗已出現")
            take_screenshot("popup_appeared")
            
            # 尋找「我知道了」按鈕
            elements = driver.find_elements(By.XPATH, "//*[contains(text(), '我知道了')]")
            print(f"找到元素數量：{len(elements)}")
            
            # 找到第一個可見的按鈕
            i_know_button = None
            for element in elements:
                if element.is_displayed():
                    i_know_button = element
                    print(f"找到可見的「我知道了」按鈕：{element.tag_name}")
                    break
            
            if i_know_button:
                print("準備點擊「我知道了」按鈕...")
                take_screenshot("before_click_i_know")
                # 使用 JavaScript 點擊，避免被其他元素遮擋
                driver.execute_script("arguments[0].click();", i_know_button)
                print("已點擊「我知道了」按鈕...")
                take_screenshot("after_click_i_know")
                
                # 等待浮動視窗消失
                try:
                    # 使用更穩定的方式等待浮動視窗消失
                    def is_popup_gone(driver):
                        try:
                            elements = driver.find_elements(By.XPATH, "//*[contains(text(), '我知道了')]")
                            return not any(element.is_displayed() for element in elements)
                        except:
                            return True  # 如果發生任何錯誤，假設浮動視窗已經消失
                    
                    WebDriverWait(driver, 5).until(is_popup_gone)
                    print("浮動視窗已消失")
                    take_screenshot("popup_disappeared")
                except TimeoutException:
                    print("浮動視窗可能未完全消失，繼續執行...")
            else:
                print("找不到可見的「我知道了」按鈕")
        except TimeoutException:
            print("等待浮動視窗超時，繼續執行...")
        
        # 檢查頁面狀態
        print(f"當前頁面標題: {driver.title}")
        print(f"當前頁面URL: {driver.current_url}")
        take_screenshot("main_page")
        
        # 等待登入表單出現
        print("等待登入表單出現...")
        
        # 尋找登入表單的文字輸入框
        print("尋找身分證字號輸入框...")
        id_input = None
        try:
            # 先嘗試在主頁面尋找
            id_input = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='text'][placeholder*='身分證']"))
            )
            print("在主頁面找到身分證字號輸入框")
            take_screenshot("found_id_input")
        except TimeoutException:
            print("主頁面找不到身分證字號輸入框，嘗試切換 iframe...")
            take_screenshot("id_input_not_found")
            # 如果主頁面找不到，嘗試在 iframe 中尋找
            iframes = driver.find_elements(By.TAG_NAME, "iframe")
            for iframe in iframes:
                try:
                    driver.switch_to.frame(iframe)
                    id_input = WebDriverWait(driver, 5).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='text'][placeholder*='身分證']"))
                    )
                    print("在 iframe 中找到身分證字號輸入框")
                    take_screenshot("found_id_input_in_iframe")
                    break
                except:
                    driver.switch_to.default_content()
        
        if not id_input:
            print("無法找到身分證字號輸入框")
            take_screenshot("id_input_final_not_found")
            return False
        
        # 尋找密碼輸入框
        print("尋找密碼輸入框...")
        try:
            password_input = driver.find_element(By.CSS_SELECTOR, "input[type='password']")
            print("找到密碼輸入框")
            take_screenshot("found_password_input")
        except NoSuchElementException:
            print("找不到密碼輸入框")
            take_screenshot("password_input_not_found")
            return False
        
        # 輸入登入資訊
        print("準備輸入登入資訊...")
        id_input.clear()
        id_input.send_keys("A102574899")
        print("已輸入身分證字號")
        take_screenshot("entered_id")
        
        password_input.clear()
        password_input.send_keys("visi319VISI")
        print("已輸入密碼")
        take_screenshot("entered_password")
        
        # 尋找登入按鈕
        print("尋找登入按鈕...")
        try:
            # 嘗試多種方式尋找登入按鈕
            login_button = None
            
            # 方法1：使用 XPath 尋找包含文字的按鈕
            try:
                login_button = driver.find_element(By.XPATH, "//button[contains(text(), '民眾登入')]")
                print("使用 XPath 找到登入按鈕")
            except NoSuchElementException:
                print("XPath 方式找不到登入按鈕")
            
            # 方法2：使用 CSS 選擇器尋找按鈕
            if not login_button:
                try:
                    login_button = driver.find_element(By.CSS_SELECTOR, "button.btn-primary")
                    print("使用 CSS 選擇器找到登入按鈕")
                except NoSuchElementException:
                    print("CSS 選擇器方式找不到登入按鈕")
            
            # 方法3：尋找所有按鈕
            if not login_button:
                try:
                    buttons = driver.find_elements(By.TAG_NAME, "button")
                    for button in buttons:
                        if button.is_displayed() and ("登入" in button.text or "login" in button.text.lower()):
                            login_button = button
                            print("找到登入按鈕")
                            break
                except:
                    print("找不到登入按鈕")
            
            if login_button:
                print("準備點擊登入按鈕...")
                take_screenshot("before_login_click")
                
                # 嘗試多種點擊方式
                try:
                    # 方法1：使用 JavaScript 點擊
                    driver.execute_script("arguments[0].click();", login_button)
                    print("使用 JavaScript 點擊登入按鈕")
                except:
                    try:
                        # 方法2：使用 Actions 點擊
                        actions = ActionChains(driver)
                        actions.move_to_element(login_button).click().perform()
                        print("使用 Actions 點擊登入按鈕")
                    except:
                        try:
                            # 方法3：直接點擊
                            login_button.click()
                            print("直接點擊登入按鈕")
                        except:
                            print("所有點擊方式都失敗")
                            take_screenshot("login_click_failed")
                            return False
                
                print("已點擊登入按鈕...")
                take_screenshot("after_login_click")
                
                # 等待登入成功
                try:
                    # 等待登入成功浮動視窗出現
                    def wait_for_login_success(driver):
                        try:
                            # 檢查是否出現登入成功的浮動視窗
                            success_elements = driver.find_elements(By.XPATH, "//*[contains(text(), '登入成功') or contains(text(), '歡迎') or contains(text(), '成功')]")
                            return any(element.is_displayed() for element in success_elements)
                        except:
                            return False
                    
                    WebDriverWait(driver, 10).until(wait_for_login_success)
                    print("登入成功浮動視窗已出現")
                    take_screenshot("login_success_popup")
                    
                    # 尋找確定按鈕並點擊
                    try:
                        confirm_buttons = driver.find_elements(By.XPATH, "//*[contains(text(), '確定') or contains(text(), 'OK') or contains(text(), '確認')]")
                        confirm_button = None
                        for button in confirm_buttons:
                            if button.is_displayed():
                                confirm_button = button
                                break
                        
                        if confirm_button:
                            print("準備點擊確定按鈕...")
                            take_screenshot("before_confirm_click")
                            driver.execute_script("arguments[0].click();", confirm_button)
                            print("已點擊確定按鈕...")
                            take_screenshot("after_confirm_click")
                            
                            # 等待浮動視窗消失
                            try:
                                def is_popup_gone(driver):
                                    try:
                                        elements = driver.find_elements(By.XPATH, "//*[contains(text(), '確定') or contains(text(), 'OK') or contains(text(), '確認')]")
                                        return not any(element.is_displayed() for element in elements)
                                    except:
                                        return True
                                
                                WebDriverWait(driver, 5).until(is_popup_gone)
                                print("登入成功浮動視窗已消失")
                                take_screenshot("login_success_popup_gone")
                            except TimeoutException:
                                print("登入成功浮動視窗可能未完全消失，繼續執行...")
                        else:
                            print("找不到可見的確定按鈕")
                            take_screenshot("confirm_button_not_found")
                            return False
                    except TimeoutException:
                        print("等待登入成功浮動視窗超時")
                        take_screenshot("login_success_timeout")
                        return False
                except Exception as e:
                    print(f"處理登入成功浮動視窗時發生錯誤：{str(e)}")
                    take_screenshot("login_success_error")
                    return False
            else:
                print("找不到登入按鈕")
                take_screenshot("login_button_not_found")
                return False
        except Exception as e:
            print(f"尋找登入按鈕時發生錯誤：{str(e)}")
            take_screenshot("login_button_error")
            return False
        
        # 等待「新增預約」按鈕出現
        print("等待「新增預約」按鈕...")
        try:
            # 等待一下確保頁面完全載入
            time.sleep(2)
            take_screenshot("before_reserve_button_search")
            
            # 初始化按鈕變數
            reserve_button = None
            
            # 方法1：使用 XPath 尋找按鈕
            try:
                reserve_buttons = driver.find_elements(By.XPATH, "//button[contains(text(), '新增預約')]")
                for button in reserve_buttons:
                    if button.is_displayed():
                        reserve_button = button
                        print("XPath 方式找到「新增預約」按鈕")
                        break
            except:
                print("XPath 方式找不到「新增預約」按鈕")
            
            # 方法2：使用 CSS 選擇器尋找按鈕
            if not reserve_button:
                try:
                    reserve_buttons = driver.find_elements(By.CSS_SELECTOR, "button.btn-primary, button.btn-default, button.btn")
                    for button in reserve_buttons:
                        if button.is_displayed() and "新增預約" in button.text:
                            reserve_button = button
                            print("CSS 選擇器方式找到「新增預約」按鈕")
                            break
                except:
                    print("CSS 選擇器方式找不到「新增預約」按鈕")
            
            # 方法3：尋找所有按鈕
            if not reserve_button:
                try:
                    buttons = driver.find_elements(By.TAG_NAME, "button")
                    for button in buttons:
                        if button.is_displayed() and "新增預約" in button.text:
                            reserve_button = button
                            print("找到「新增預約」按鈕")
                            break
                except:
                    print("找不到「新增預約」按鈕")
            
            # 方法4：尋找任何包含「新增預約」文字的元素
            if not reserve_button:
                try:
                    elements = driver.find_elements(By.XPATH, "//*[contains(text(), '新增預約')]")
                    for element in elements:
                        if element.is_displayed() and element.is_enabled():
                            reserve_button = element
                            print("找到包含「新增預約」文字的元素")
                            break
                except:
                    print("找不到包含「新增預約」文字的元素")
            
            # 方法5：尋找任何可點擊元素
            if not reserve_button:
                try:
                    elements = driver.find_elements(By.CSS_SELECTOR, "button, a, input[type='button'], input[type='submit']")
                    for element in elements:
                        if element.is_displayed() and element.is_enabled():
                            reserve_button = element
                            print("找到可點擊元素")
                            break
                except:
                    print("找不到可點擊元素")
            
            if reserve_button:
                print("準備點擊「新增預約」按鈕...")
                take_screenshot("before_reserve_click")
                
                # 記錄當前 URL
                current_url = driver.current_url
                
                # 嘗試多種點擊方式
                try:
                    # 方法1：使用 JavaScript 點擊
                    driver.execute_script("arguments[0].click();", reserve_button)
                    print("使用 JavaScript 點擊「新增預約」按鈕")
                except:
                    try:
                        # 方法2：使用 Actions 點擊
                        actions = ActionChains(driver)
                        actions.move_to_element(reserve_button).click().perform()
                        print("使用 Actions 點擊「新增預約」按鈕")
                    except:
                        try:
                            # 方法3：直接點擊
                            reserve_button.click()
                            print("直接點擊「新增預約」按鈕")
                        except:
                            print("所有點擊方式都失敗")
                            take_screenshot("reserve_click_failed")
                            return False
                
                print("已點擊「新增預約」按鈕...")
                take_screenshot("after_reserve_click")
                
                # 等待頁面跳轉
                try:
                    def is_page_changed(driver):
                        try:
                            # 檢查 URL 是否改變
                            if driver.current_url != current_url:
                                print(f"URL 已改變：{driver.current_url}")
                                return True
                            
                            # 檢查頁面標題是否改變
                            if "預約" in driver.title:
                                print(f"頁面標題包含預約：{driver.title}")
                                return True
                            
                            # 檢查是否出現預約相關元素
                            elements = driver.find_elements(By.XPATH, "//*[contains(text(), '預約')]")
                            visible_elements = [e for e in elements if e.is_displayed()]
                            if visible_elements:
                                print(f"找到 {len(visible_elements)} 個可見的預約相關元素")
                                return True
                            
                            # 檢查是否出現預約表單
                            try:
                                form = driver.find_element(By.TAG_NAME, "form")
                                if form.is_displayed():
                                    print("找到可見的預約表單")
                                    return True
                            except:
                                pass
                            
                            return False
                        except:
                            return False
                    
                    # 增加等待時間到 30 秒
                    WebDriverWait(driver, 30).until(is_page_changed)
                    print("成功跳轉到預約頁面")
                    take_screenshot("reserve_page_loaded")
                    
                    # 等待一下確保頁面完全載入
                    time.sleep(2)
                    
                    # 再次檢查是否在預約頁面
                    is_reserve_page = False
                    
                    # 檢查 URL
                    if "預約" in driver.current_url:
                        print(f"URL 包含預約：{driver.current_url}")
                        is_reserve_page = True
                    
                    # 檢查頁面標題
                    if "預約" in driver.title:
                        print(f"頁面標題包含預約：{driver.title}")
                        is_reserve_page = True
                    
                    # 檢查預約相關元素
                    elements = driver.find_elements(By.XPATH, "//*[contains(text(), '預約')]")
                    visible_elements = [e for e in elements if e.is_displayed()]
                    if visible_elements:
                        print(f"找到 {len(visible_elements)} 個可見的預約相關元素")
                        is_reserve_page = True
                    
                    # 檢查預約表單
                    try:
                        form = driver.find_element(By.TAG_NAME, "form")
                        if form.is_displayed():
                            print("找到可見的預約表單")
                            is_reserve_page = True
                    except:
                        pass
                    
                    if not is_reserve_page:
                        print("頁面跳轉可能失敗，嘗試繼續執行...")
                        take_screenshot("page_jump_may_failed")
                    
                except TimeoutException:
                    print("等待頁面跳轉超時，嘗試繼續執行...")
                    take_screenshot("page_jump_timeout")
                
            else:
                print("找不到「新增預約」按鈕")
                take_screenshot("reserve_button_not_found")
                return False
        except Exception as e:
            print(f"尋找「新增預約」按鈕時發生錯誤：{str(e)}")
            take_screenshot("reserve_button_error")
            return False
        
        # 等待預約表單載入
        print("等待預約表單載入...")
        time.sleep(3)
        take_screenshot("reserve_form_loaded")
        
        # 尋找上車地點選擇
        print("尋找上車地點選擇...")
        try:
            # 方法1：尋找下拉選單
            pickup_location = None
            try:
                pickup_location = driver.find_element(By.CSS_SELECTOR, "select[name*='pickup'], select[name*='location'], select[name*='from']")
                print("找到上車地點下拉選單")
            except NoSuchElementException:
                print("找不到上車地點下拉選單")
            
            # 方法2：尋找單選框
            if not pickup_location:
                try:
                    radio_buttons = driver.find_elements(By.CSS_SELECTOR, "input[type='radio']")
                    for radio in radio_buttons:
                        if radio.is_displayed() and ("醫療院所" in radio.get_attribute("value") or "醫療院所" in radio.get_attribute("name")):
                            pickup_location = radio
                            print("找到上車地點單選框")
                            break
                except:
                    print("找不到上車地點單選框")
            
            # 方法3：尋找按鈕
            if not pickup_location:
                try:
                    buttons = driver.find_elements(By.TAG_NAME, "button")
                    for button in buttons:
                        if button.is_displayed() and "醫療院所" in button.text:
                            pickup_location = button
                            print("找到上車地點按鈕")
                            break
                except:
                    print("找不到上車地點按鈕")
            
            # 方法4：尋找任何包含「醫療院所」的元素
            if not pickup_location:
                try:
                    elements = driver.find_elements(By.XPATH, "//*[contains(text(), '醫療院所')]")
                    for element in elements:
                        if element.is_displayed() and element.is_enabled():
                            pickup_location = element
                            print("找到包含「醫療院所」的元素")
                            break
                except:
                    print("找不到包含「醫療院所」的元素")
            
            if pickup_location:
                print("準備選擇上車地點...")
                take_screenshot("before_pickup_selection")
                
                # 嘗試多種選擇方式
                try:
                    # 方法1：如果是下拉選單，選擇「醫療院所」選項
                    if pickup_location.tag_name == "select":
                        from selenium.webdriver.support.ui import Select
                        select = Select(pickup_location)
                        select.select_by_visible_text("醫療院所")
                        print("使用下拉選單選擇「醫療院所」")
                    # 方法2：如果是單選框，點擊
                    elif pickup_location.tag_name == "input" and pickup_location.get_attribute("type") == "radio":
                        driver.execute_script("arguments[0].click();", pickup_location)
                        print("點擊單選框選擇「醫療院所」")
                    # 方法3：如果是按鈕，點擊
                    elif pickup_location.tag_name == "button":
                        driver.execute_script("arguments[0].click();", pickup_location)
                        print("點擊按鈕選擇「醫療院所」")
                    # 方法4：其他元素，嘗試點擊
                    else:
                        driver.execute_script("arguments[0].click();", pickup_location)
                        print("點擊元素選擇「醫療院所」")
                except Exception as e:
                    print(f"選擇上車地點時發生錯誤：{str(e)}")
                    take_screenshot("pickup_selection_error")
                    return False
                
                print("已選擇上車地點...")
                take_screenshot("after_pickup_selection")
                
                # 等待選擇生效
                try:
                    def is_selection_effective(driver):
                        try:
                            # 檢查是否有選中的元素
                            selected_elements = driver.find_elements(By.CSS_SELECTOR, "input[type='radio']:checked, select option:checked")
                            if selected_elements:
                                print("找到選中的元素")
                                return True
                            
                            # 檢查是否有相關的視覺反饋
                            elements = driver.find_elements(By.XPATH, "//*[contains(text(), '醫療院所')]")
                            for element in elements:
                                if element.is_displayed():
                                    # 檢查是否有選中狀態的樣式
                                    classes = element.get_attribute("class") or ""
                                    if "selected" in classes or "active" in classes or "checked" in classes:
                                        print("找到選中狀態的元素")
                                        return True
                            return False
                        except:
                            return False
                    
                    WebDriverWait(driver, 10).until(is_selection_effective)
                    print("上車地點選擇已生效")
                    take_screenshot("pickup_selection_effective")
                except TimeoutException:
                    print("等待上車地點選擇生效超時，繼續執行...")
                    take_screenshot("pickup_selection_timeout")
                
            else:
                print("找不到上車地點選擇")
                take_screenshot("pickup_location_not_found")
                return False
        except Exception as e:
            print(f"尋找上車地點選擇時發生錯誤：{str(e)}")
            take_screenshot("pickup_location_error")
            return False
        
        # 等待一下確保選擇生效
        time.sleep(2)
        take_screenshot("before_next_step")
        
        # 這裡可以繼續添加其他預約步驟...
        print("預約流程執行完成")
        take_screenshot("reservation_complete")
        
        # 檢查是否成功完成預約
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//*[contains(text(), '已完成預約')]"))
            )
            print("已完成預約")
            driver.save_screenshot('after_success.png')
            return True
        except Exception as e:
            import traceback
            print(traceback.format_exc())
            driver.save_screenshot('error.png')
            print("error.png exists:", os.path.exists('error.png'))
            return False
    finally:
        driver.quit()

@app.route('/')
def index():
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>長照交通接送預約系統</title>
        <meta charset="utf-8">
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            .container { max-width: 800px; margin: 0 auto; }
            .button { 
                background-color: #4CAF50; 
                color: white; 
                padding: 15px 32px; 
                text-align: center; 
                text-decoration: none; 
                display: inline-block; 
                font-size: 16px; 
                margin: 4px 2px; 
                cursor: pointer; 
                border: none; 
                border-radius: 4px; 
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>長照交通接送預約系統</h1>
            <a href="/reserve" class="button">開始預約</a>
            <a href="/screenshots" class="button">查看截圖</a>
            <a href="/page_source" class="button">查看頁面原始碼</a>
        </div>
    </body>
    </html>
    '''

@app.route('/screenshots')
def screenshots():
    import os
    import glob
    
    # 獲取所有截圖檔案
    screenshot_files = glob.glob('step_*.png')
    screenshot_files.sort()
    
    html = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>預約過程截圖</title>
        <meta charset="utf-8">
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            .container { max-width: 1200px; margin: 0 auto; }
            .screenshot { margin: 20px 0; padding: 10px; border: 1px solid #ddd; border-radius: 5px; }
            .screenshot img { max-width: 100%; height: auto; }
            .screenshot h3 { margin: 5px 0; color: #333; }
            .back-button { 
                background-color: #2196F3; 
                color: white; 
                padding: 10px 20px; 
                text-decoration: none; 
                border-radius: 4px; 
                display: inline-block; 
                margin-bottom: 20px; 
            }
        </style>
    </head>
    <body>
        <div class="container">
            <a href="/" class="back-button">返回首頁</a>
            <h1>預約過程截圖</h1>
    '''
    
    if screenshot_files:
        for file_path in screenshot_files:
            filename = os.path.basename(file_path)
            description = filename.replace('.png', '').replace('step_', '').replace('_', ' ')
            html += f'''
            <div class="screenshot">
                <h3>{description}</h3>
                <img src="/screenshot/{filename}" alt="{description}">
            </div>
            '''
    else:
        html += '<p>目前沒有截圖</p>'
    
    html += '''
        </div>
    </body>
    </html>
    '''
    
    return html

@app.route('/screenshot/<filename>')
def get_screenshot(filename):
    return send_from_directory('.', filename)

@app.route('/page_source')
def page_source():
    try:
        with open('page_source.html', 'r', encoding='utf-8') as f:
            content = f.read()
        return f'''
        <!DOCTYPE html>
        <html>
        <head>
            <title>頁面原始碼</title>
            <meta charset="utf-8">
            <style>
                body {{ font-family: monospace; margin: 20px; }}
                pre {{ background-color: #f5f5f5; padding: 20px; border-radius: 5px; overflow-x: auto; }}
                .back-button {{ 
                    background-color: #2196F3; 
                    color: white; 
                    padding: 10px 20px; 
                    text-decoration: none; 
                    border-radius: 4px; 
                    display: inline-block; 
                    margin-bottom: 20px; 
                }}
            </style>
        </head>
        <body>
            <a href="/" class="back-button">返回首頁</a>
            <h1>頁面原始碼</h1>
            <pre>{content}</pre>
        </body>
        </html>
        '''
    except FileNotFoundError:
        return '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>頁面原始碼</title>
            <meta charset="utf-8">
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                .back-button { 
                    background-color: #2196F3; 
                    color: white; 
                    padding: 10px 20px; 
                    text-decoration: none; 
                    border-radius: 4px; 
                    display: inline-block; 
                    margin-bottom: 20px; 
                }
            </style>
        </head>
        <body>
            <a href="/" class="back-button">返回首頁</a>
            <h1>頁面原始碼</h1>
            <p>頁面原始碼檔案不存在</p>
        </body>
        </html>
        '''

@app.route('/reserve')
def reservation():
    result = make_reservation()
    return jsonify({"success": result})

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                             'favicon.ico', mimetype='image/vnd.microsoft.icon')

if __name__ == '__main__':
    # Zeabur 環境變數
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port) 