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
    chrome_options.binary_location = '/usr/bin/chromium'
    chrome_options.add_argument('--log-level=3')
    chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])

    service = Service('/usr/bin/chromedriver')
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
        driver.save_screenshot('/app/timeout.png')
        return None

def make_reservation():
    driver = setup_driver()
    try:
        driver.get("https://www.ntpc.ltc-car.org/")
        print("已載入網頁，等待頁面載入...")
        
        # 等待頁面完全載入
        WebDriverWait(driver, 30).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
        print("頁面已完全載入")
        driver.save_screenshot('/app/page_loaded.png')
        
        # 等待浮動視窗出現
        print("等待浮動視窗出現...")
        try:
            # 先等待浮動視窗出現
            WebDriverWait(driver, 10).until(
                lambda d: len(d.find_elements(By.XPATH, "//*[contains(text(), '我知道了')]")) > 0
            )
            print("浮動視窗已出現")
            
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
                driver.save_screenshot('/app/before_click.png')
                # 使用 JavaScript 點擊，避免被其他元素遮擋
                driver.execute_script("arguments[0].click();", i_know_button)
                print("已點擊「我知道了」按鈕...")
                driver.save_screenshot('/app/after_click.png')
                
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
                except TimeoutException:
                    print("浮動視窗可能未完全消失，繼續執行...")
            else:
                print("找不到可見的「我知道了」按鈕")
        except TimeoutException:
            print("等待浮動視窗超時，繼續執行...")
        
        # 檢查頁面狀態
        print(f"當前頁面標題: {driver.title}")
        print(f"當前頁面URL: {driver.current_url}")
        
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
        except TimeoutException:
            print("主頁面找不到身分證字號輸入框，嘗試切換 iframe...")
            # 如果主頁面找不到，嘗試在 iframe 中尋找
            iframes = driver.find_elements(By.TAG_NAME, "iframe")
            for iframe in iframes:
                try:
                    driver.switch_to.frame(iframe)
                    id_input = WebDriverWait(driver, 5).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='text'][placeholder*='身分證']"))
                    )
                    print("在 iframe 中找到身分證字號輸入框")
                    break
                except:
                    driver.switch_to.default_content()
        
        if not id_input:
            print("無法找到身分證字號輸入框")
            driver.save_screenshot('/app/login_form_not_found.png')
            return False
        
        # 尋找密碼輸入框
        print("尋找密碼輸入框...")
        try:
            password_input = driver.find_element(By.CSS_SELECTOR, "input[type='password']")
            print("找到密碼輸入框")
        except NoSuchElementException:
            print("找不到密碼輸入框")
            driver.save_screenshot('/app/password_input_not_found.png')
            return False
        
        # 輸入登入資訊
        print("準備輸入登入資訊...")
        id_input.clear()
        id_input.send_keys("A102574899")
        print("已輸入身分證字號")
        
        password_input.clear()
        password_input.send_keys("visi319VISI")
        print("已輸入密碼")
        
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
            
            # 方法3：尋找所有按鈕並檢查文字
            if not login_button:
                try:
                    buttons = driver.find_elements(By.TAG_NAME, "button")
                    for button in buttons:
                        if "民眾登入" in button.text:
                            login_button = button
                            print("通過按鈕文字找到登入按鈕")
                            break
                except:
                    print("按鈕文字搜尋失敗")
            
            # 方法4：在 iframe 中尋找
            if not login_button:
                print("嘗試在 iframe 中尋找登入按鈕...")
                iframes = driver.find_elements(By.TAG_NAME, "iframe")
                for iframe in iframes:
                    try:
                        driver.switch_to.frame(iframe)
                        # 在 iframe 中嘗試所有方法
                        try:
                            login_button = driver.find_element(By.XPATH, "//button[contains(text(), '民眾登入')]")
                            print("在 iframe 中使用 XPath 找到登入按鈕")
                        except:
                            try:
                                login_button = driver.find_element(By.CSS_SELECTOR, "button.btn-primary")
                                print("在 iframe 中使用 CSS 選擇器找到登入按鈕")
                            except:
                                buttons = driver.find_elements(By.TAG_NAME, "button")
                                for button in buttons:
                                    if "民眾登入" in button.text:
                                        login_button = button
                                        print("在 iframe 中通過按鈕文字找到登入按鈕")
                                        break
                        if login_button:
                            break
                        driver.switch_to.default_content()
                    except:
                        driver.switch_to.default_content()
            
            # 方法5：在表單中尋找
            if not login_button:
                print("嘗試在表單中尋找登入按鈕...")
                try:
                    # 尋找包含輸入框的表單
                    form = driver.find_element(By.TAG_NAME, "form")
                    print("找到表單")
                    
                    # 在表單中尋找按鈕
                    try:
                        # 方法1：使用 XPath 尋找包含文字的按鈕
                        login_button = form.find_element(By.XPATH, ".//button[contains(text(), '民眾登入')]")
                        print("在表單中使用 XPath 找到登入按鈕")
                    except:
                        try:
                            # 方法2：使用 CSS 選擇器尋找按鈕
                            login_button = form.find_element(By.CSS_SELECTOR, "button.btn-primary")
                            print("在表單中使用 CSS 選擇器找到登入按鈕")
                        except:
                            try:
                                # 方法3：尋找所有按鈕並檢查文字
                                buttons = form.find_elements(By.TAG_NAME, "button")
                                for button in buttons:
                                    if "民眾登入" in button.text:
                                        login_button = button
                                        print("在表單中通過按鈕文字找到登入按鈕")
                                        break
                            except:
                                print("在表單中找不到按鈕")
                    
                    # 如果還是找不到，嘗試尋找表單中的其他元素
                    if not login_button:
                        print("嘗試在表單中尋找其他可能的登入元素...")
                        try:
                            # 方法4：尋找包含「登入」文字的任何元素
                            elements = form.find_elements(By.XPATH, ".//*[contains(text(), '登入')]")
                            for element in elements:
                                if element.is_displayed() and element.is_enabled():
                                    login_button = element
                                    print("在表單中找到包含「登入」文字的元素")
                                    break
                        except:
                            print("在表單中找不到包含「登入」文字的元素")
                        
                        # 方法5：尋找表單中的提交按鈕
                        if not login_button:
                            try:
                                submit_button = form.find_element(By.CSS_SELECTOR, "input[type='submit']")
                                if submit_button.is_displayed() and submit_button.is_enabled():
                                    login_button = submit_button
                                    print("在表單中找到提交按鈕")
                            except:
                                print("在表單中找不到提交按鈕")
                        
                        # 方法6：尋找表單中的任何可點擊元素
                        if not login_button:
                            try:
                                clickable_elements = form.find_elements(By.CSS_SELECTOR, "button, input[type='submit'], input[type='button']")
                                for element in clickable_elements:
                                    if element.is_displayed() and element.is_enabled():
                                        login_button = element
                                        print("在表單中找到可點擊元素")
                                        break
                            except:
                                print("在表單中找不到可點擊元素")
                except:
                    print("找不到表單或表單中沒有登入按鈕")
            
            # 點擊登入按鈕
            if login_button:
                print("找到登入按鈕，準備點擊...")
                driver.save_screenshot('/app/before_login.png')
                
                # 先等待一下確保按鈕可以點擊
                time.sleep(1)
                
                try:
                    # 使用 JavaScript 點擊，避免被其他元素遮擋
                    driver.execute_script("arguments[0].click();", login_button)
                    print("已點擊「民眾登入」按鈕...")
                    driver.save_screenshot('/app/after_login.png')
                    
                    # 等待一下確保點擊事件被處理
                    time.sleep(2)
                    
                    # 檢查是否有錯誤訊息
                    try:
                        error_elements = driver.find_elements(By.XPATH, "//*[contains(text(), '錯誤') or contains(text(), '失敗') or contains(text(), '無效')]")
                        for element in error_elements:
                            if element.is_displayed():
                                print(f"發現錯誤訊息：{element.text}")
                                driver.save_screenshot('/app/login_error.png')
                                return False
                    except:
                        pass
                    
                    # 檢查是否仍在登入頁面
                    if "登入" in driver.title or "login" in driver.current_url.lower():
                        print("仍在登入頁面，可能登入失敗")
                        driver.save_screenshot('/app/still_on_login_page.png')
                        return False
                    
                    # 等待登入成功
                    print("等待「登入成功」浮動視窗...")
                    try:
                        # 等待浮動視窗出現，增加等待時間並使用更靈活的條件
                        def wait_for_login_success(driver):
                            try:
                                # 檢查多種可能的文字
                                success_texts = ["登入成功", "登入完成", "成功登入", "歡迎"]
                                for text in success_texts:
                                    elements = driver.find_elements(By.XPATH, f"//*[contains(text(), '{text}')]")
                                    if any(element.is_displayed() for element in elements):
                                        return True
                                
                                # 檢查是否已經跳轉到主頁面
                                if "登入" not in driver.title and "login" not in driver.current_url.lower():
                                    return True
                                
                                return False
                            except:
                                return False
                        
                        # 增加等待時間到 30 秒
                        WebDriverWait(driver, 30).until(wait_for_login_success)
                        print("找到「登入成功」浮動視窗")
                        driver.save_screenshot('/app/login_success_popup.png')
                        
                        # 等待一下確保浮動視窗完全載入
                        time.sleep(2)
                        
                        # 尋找確定按鈕，使用多種方式
                        confirm_button = None
                        
                        # 方法1：直接尋找確定按鈕
                        try:
                            # 先找到浮動視窗
                            popup = None
                            for text in ["登入成功", "登入完成", "成功登入", "歡迎"]:
                                elements = driver.find_elements(By.XPATH, f"//*[contains(text(), '{text}')]")
                                for element in elements:
                                    if element.is_displayed():
                                        # 找到包含這個文字的父元素（可能是浮動視窗）
                                        try:
                                            popup = element.find_element(By.XPATH, "./ancestor::div[contains(@class, 'modal') or contains(@class, 'popup') or contains(@class, 'dialog')]")
                                            if popup:
                                                break
                                        except:
                                            # 如果找不到父元素，可能是浮動視窗本身
                                            popup = element
                                            break
                                if popup:
                                    break
                            
                            if popup:
                                print("找到浮動視窗，在其中尋找確定按鈕")
                                # 在浮動視窗中尋找按鈕
                                try:
                                    # 方法1.1：使用 XPath 尋找按鈕
                                    buttons = popup.find_elements(By.XPATH, ".//button[contains(text(), '確定')]")
                                    for button in buttons:
                                        if button.is_displayed():
                                            confirm_button = button
                                            print("在浮動視窗中使用 XPath 找到確定按鈕")
                                            break
                                except:
                                    print("在浮動視窗中使用 XPath 找不到確定按鈕")
                                
                                # 方法1.2：使用 CSS 選擇器尋找按鈕
                                if not confirm_button:
                                    try:
                                        buttons = popup.find_elements(By.CSS_SELECTOR, "button.btn-primary, button.btn-default, button.btn")
                                        for button in buttons:
                                            if button.is_displayed():
                                                confirm_button = button
                                                print("在浮動視窗中使用 CSS 選擇器找到確定按鈕")
                                                break
                                    except:
                                        print("在浮動視窗中使用 CSS 選擇器找不到確定按鈕")
                                
                                # 方法1.3：尋找所有按鈕
                                if not confirm_button:
                                    try:
                                        buttons = popup.find_elements(By.TAG_NAME, "button")
                                        for button in buttons:
                                            if button.is_displayed():
                                                confirm_button = button
                                                print("在浮動視窗中找到任何按鈕")
                                                break
                                    except:
                                        print("在浮動視窗中找不到任何按鈕")
                                
                                # 方法1.4：尋找任何可點擊元素
                                if not confirm_button:
                                    try:
                                        elements = popup.find_elements(By.CSS_SELECTOR, "button, a, input[type='button'], input[type='submit']")
                                        for element in elements:
                                            if element.is_displayed() and element.is_enabled():
                                                confirm_button = element
                                                print("在浮動視窗中找到任何可點擊元素")
                                                break
                                    except:
                                        print("在浮動視窗中找不到任何可點擊元素")
                            else:
                                print("找不到浮動視窗")
                        except:
                            print("尋找浮動視窗失敗")
                        
                        # 方法2：在整個頁面中尋找確定按鈕
                        if not confirm_button:
                            try:
                                # 方法2.1：使用 XPath 尋找按鈕
                                buttons = driver.find_elements(By.XPATH, "//button[contains(text(), '確定')]")
                                for button in buttons:
                                    if button.is_displayed():
                                        confirm_button = button
                                        print("在頁面中使用 XPath 找到確定按鈕")
                                        break
                            except:
                                print("在頁面中使用 XPath 找不到確定按鈕")
                            
                            # 方法2.2：使用 CSS 選擇器尋找按鈕
                            if not confirm_button:
                                try:
                                    buttons = driver.find_elements(By.CSS_SELECTOR, "button.btn-primary, button.btn-default, button.btn")
                                    for button in buttons:
                                        if button.is_displayed():
                                            confirm_button = button
                                            print("在頁面中使用 CSS 選擇器找到確定按鈕")
                                            break
                                except:
                                    print("在頁面中使用 CSS 選擇器找不到確定按鈕")
                            
                            # 方法2.3：尋找所有按鈕
                            if not confirm_button:
                                try:
                                    buttons = driver.find_elements(By.TAG_NAME, "button")
                                    for button in buttons:
                                        if button.is_displayed():
                                            confirm_button = button
                                            print("在頁面中找到任何按鈕")
                                            break
                                except:
                                    print("在頁面中找不到任何按鈕")
                        
                        if confirm_button:
                            print("準備點擊確定按鈕...")
                            driver.save_screenshot('/app/before_confirm_click.png')
                            
                            # 嘗試多種點擊方式
                            try:
                                # 方法1：使用 JavaScript 點擊
                                driver.execute_script("arguments[0].click();", confirm_button)
                                print("使用 JavaScript 點擊確定按鈕")
                            except:
                                try:
                                    # 方法2：使用 Actions 點擊
                                    actions = ActionChains(driver)
                                    actions.move_to_element(confirm_button).click().perform()
                                    print("使用 Actions 點擊確定按鈕")
                                except:
                                    try:
                                        # 方法3：直接點擊
                                        confirm_button.click()
                                        print("直接點擊確定按鈕")
                                    except:
                                        print("所有點擊方式都失敗")
                                        driver.save_screenshot('/app/confirm_click_failed.png')
                                        return False
                            
                            print("已點擊確定按鈕...")
                            driver.save_screenshot('/app/after_confirm_click.png')
                            
                            # 等待浮動視窗消失
                            try:
                                def is_popup_gone(driver):
                                    try:
                                        for text in ["登入成功", "登入完成", "成功登入", "歡迎"]:
                                            elements = driver.find_elements(By.XPATH, f"//*[contains(text(), '{text}')]")
                                            if any(element.is_displayed() for element in elements):
                                                return False
                                        return True
                                    except:
                                        return True
                                
                                WebDriverWait(driver, 10).until(is_popup_gone)
                                print("登入成功浮動視窗已消失")
                                
                                # 等待一下確保頁面完全載入
                                time.sleep(2)
                                
                                # 檢查是否已經在主頁面
                                if "登入" not in driver.title and "login" not in driver.current_url.lower():
                                    print("已經在主頁面，繼續執行...")
                                else:
                                    print("仍在登入頁面，可能登入失敗")
                                    driver.save_screenshot('/app/still_on_login_page.png')
                                    return False
                            except TimeoutException:
                                print("登入成功浮動視窗可能未完全消失，繼續執行...")
                        else:
                            print("找不到可見的確定按鈕")
                            driver.save_screenshot('/app/confirm_button_not_found.png')
                            return False
                    except TimeoutException:
                        print("等待登入成功浮動視窗超時")
                        driver.save_screenshot('/app/login_success_timeout.png')
                        return False
                    except Exception as e:
                        print(f"處理登入成功浮動視窗時發生錯誤：{str(e)}")
                        driver.save_screenshot('/app/login_success_error.png')
                        return False
                except Exception as e:
                    print(f"點擊登入按鈕時發生錯誤：{str(e)}")
                    driver.save_screenshot('/app/login_button_error.png')
                    return False
            else:
                print("所有方法都找不到登入按鈕")
                driver.save_screenshot('/app/login_button_not_found.png')
                return False
        except Exception as e:
            print(f"點擊登入按鈕時發生錯誤：{str(e)}")
            driver.save_screenshot('/app/login_button_error.png')
            return False

        # 等待「新增預約」按鈕出現
        print("等待「新增預約」按鈕...")
        try:
            # 等待一下確保頁面完全載入
            time.sleep(2)
            
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
                driver.save_screenshot('/app/before_reserve_click.png')
                
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
                            driver.save_screenshot('/app/reserve_click_failed.png')
                            return False
                
                print("已點擊「新增預約」按鈕...")
                driver.save_screenshot('/app/after_reserve_click.png')
                
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
                            
                            # 檢查是否出現預約相關輸入欄位
                            try:
                                inputs = driver.find_elements(By.TAG_NAME, "input")
                                for input_field in inputs:
                                    if input_field.is_displayed() and input_field.get_attribute("type") in ["text", "date", "time"]:
                                        print("找到預約相關輸入欄位")
                                        return True
                            except:
                                pass
                            
                            return False
                        except:
                            return False
                    
                    # 增加等待時間到 30 秒
                    WebDriverWait(driver, 30).until(is_page_changed)
                    print("成功跳轉到預約頁面")
                    
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
                    
                    # 檢查預約相關輸入欄位
                    try:
                        inputs = driver.find_elements(By.TAG_NAME, "input")
                        for input_field in inputs:
                            if input_field.is_displayed() and input_field.get_attribute("type") in ["text", "date", "time"]:
                                print("找到預約相關輸入欄位")
                                is_reserve_page = True
                                break
                    except:
                        pass
                    
                    if is_reserve_page:
                        print("確認在預約頁面，繼續執行...")
                    else:
                        print("可能未成功跳轉到預約頁面")
                        driver.save_screenshot('/app/reserve_page_check_failed.png')
                        return False
                except TimeoutException:
                    print("等待頁面跳轉超時")
                    driver.save_screenshot('/app/reserve_page_timeout.png')
                    return False
            else:
                print("找不到「新增預約」按鈕")
                driver.save_screenshot('/app/reserve_button_not_found.png')
                return False
        except Exception as e:
            print(f"處理「新增預約」按鈕時發生錯誤：{str(e)}")
            driver.save_screenshot('/app/reserve_button_error.png')
            return False

        # 選擇上車地點
        print("選擇上車地點「醫療院所」...")
        try:
            # 等待一下確保頁面完全載入
            time.sleep(2)
            
            # 先截圖記錄當前頁面狀態
            driver.save_screenshot('/app/before_pickup_type_search.png')
            
            # 方法1：使用 XPath 尋找下拉選單
            try:
                pickup_type = driver.find_element(By.XPATH, "//select[contains(@name, 'pickup_type') or contains(@id, 'pickup_type')]")
                print("使用 XPath 找到上車地點下拉選單")
            except:
                print("使用 XPath 找不到上車地點下拉選單")
                pickup_type = None
            
            # 方法2：使用 CSS 選擇器尋找下拉選單
            if not pickup_type:
                try:
                    pickup_type = driver.find_element(By.CSS_SELECTOR, "select.form-control, select.select2-hidden-accessible")
                    print("使用 CSS 選擇器找到上車地點下拉選單")
                except:
                    print("使用 CSS 選擇器找不到上車地點下拉選單")
            
            # 方法3：尋找所有下拉選單
            if not pickup_type:
                try:
                    selects = driver.find_elements(By.TAG_NAME, "select")
                    print(f"找到 {len(selects)} 個下拉選單")
                    for i, select in enumerate(selects):
                        if select.is_displayed():
                            pickup_type = select
                            print(f"找到可見的下拉選單 #{i+1}")
                            break
                except:
                    print("找不到下拉選單")
            
            # 方法4：尋找包含「上車地點」或「醫療院所」文字的元素
            if not pickup_type:
                try:
                    elements = driver.find_elements(By.XPATH, "//*[contains(text(), '上車地點') or contains(text(), '醫療院所')]")
                    print(f"找到 {len(elements)} 個包含相關文字的元素")
                    for i, element in enumerate(elements):
                        if element.is_displayed():
                            print(f"檢查元素 #{i+1}：{element.text}")
                            # 嘗試找到相關的下拉選單
                            try:
                                nearby_select = element.find_element(By.XPATH, "./following-sibling::select")
                                if nearby_select.is_displayed():
                                    pickup_type = nearby_select
                                    print("找到包含相關文字的下拉選單")
                                    break
                            except:
                                try:
                                    nearby_select = element.find_element(By.XPATH, "./ancestor::div//select")
                                    if nearby_select.is_displayed():
                                        pickup_type = nearby_select
                                        print("找到包含相關文字的下拉選單")
                                        break
                                except:
                                    # 如果找不到下拉選單，檢查是否有其他可點擊元素
                                    try:
                                        # 尋找單選框
                                        radio_buttons = element.find_elements(By.XPATH, "./ancestor::div//input[@type='radio']")
                                        for radio in radio_buttons:
                                            if radio.is_displayed() and "醫療院所" in radio.get_attribute("value"):
                                                pickup_type = radio
                                                print("找到醫療院所單選框")
                                                break
                                    except:
                                        try:
                                            # 尋找按鈕
                                            buttons = element.find_elements(By.XPATH, "./ancestor::div//button")
                                            for button in buttons:
                                                if button.is_displayed() and "醫療院所" in button.text:
                                                    pickup_type = button
                                                    print("找到醫療院所按鈕")
                                                    break
                                        except:
                                            continue
                except:
                    print("找不到包含相關文字的下拉選單")
            
            # 方法5：尋找任何可點擊的下拉選單
            if not pickup_type:
                try:
                    elements = driver.find_elements(By.CSS_SELECTOR, "select, .select2-container")
                    print(f"找到 {len(elements)} 個可點擊的下拉選單")
                    for element in elements:
                        if element.is_displayed() and element.is_enabled():
                            pickup_type = element
                            print("找到可點擊的下拉選單")
                            break
                except:
                    print("找不到可點擊的下拉選單")
            
            # 方法6：尋找所有可能的選擇器
            if not pickup_type:
                try:
                    # 嘗試多種可能的選擇器
                    selectors = [
                        "//select[@id='pickupType']",
                        "//select[@name='pickupType']",
                        "//select[@id='pickup_type']",
                        "//select[@name='pickup_type']",
                        "//select[contains(@class, 'pickup')]",
                        "//select[contains(@class, 'location')]",
                        "//select[contains(@class, 'type')]"
                    ]
                    
                    for selector in selectors:
                        try:
                            pickup_type = driver.find_element(By.XPATH, selector)
                            if pickup_type.is_displayed():
                                print(f"使用選擇器找到下拉選單：{selector}")
                                break
                        except:
                            continue
                except:
                    print("使用所有選擇器都找不到下拉選單")
            
            # 方法7：尋找單選框
            if not pickup_type:
                try:
                    radio_buttons = driver.find_elements(By.XPATH, "//input[@type='radio']")
                    print(f"找到 {len(radio_buttons)} 個單選框")
                    for radio in radio_buttons:
                        if radio.is_displayed():
                            value = radio.get_attribute("value")
                            if value and "醫療院所" in value:
                                pickup_type = radio
                                print("找到醫療院所單選框")
                                break
                except:
                    print("找不到醫療院所單選框")
            
            # 方法8：尋找按鈕
            if not pickup_type:
                try:
                    buttons = driver.find_elements(By.TAG_NAME, "button")
                    print(f"找到 {len(buttons)} 個按鈕")
                    for button in buttons:
                        if button.is_displayed() and "醫療院所" in button.text:
                            pickup_type = button
                            print("找到醫療院所按鈕")
                            break
                except:
                    print("找不到醫療院所按鈕")
            
            # 如果還是找不到，檢查頁面結構
            if not pickup_type:
                print("檢查頁面結構...")
                try:
                    # 檢查所有表單元素
                    forms = driver.find_elements(By.TAG_NAME, "form")
                    print(f"找到 {len(forms)} 個表單")
                    
                    # 檢查所有輸入元素
                    inputs = driver.find_elements(By.TAG_NAME, "input")
                    print(f"找到 {len(inputs)} 個輸入元素")
                    
                    # 檢查所有選擇元素
                    selects = driver.find_elements(By.TAG_NAME, "select")
                    print(f"找到 {len(selects)} 個選擇元素")
                    
                    # 檢查所有標籤元素
                    labels = driver.find_elements(By.TAG_NAME, "label")
                    print(f"找到 {len(labels)} 個標籤元素")
                    
                    # 檢查頁面標題和 URL
                    print(f"當前頁面標題：{driver.title}")
                    print(f"當前頁面 URL：{driver.current_url}")
                    
                    # 保存頁面原始碼以供檢查
                    with open('/app/page_source.html', 'w', encoding='utf-8') as f:
                        f.write(driver.page_source)
                    print("已保存頁面原始碼到 page_source.html")
                    
                except Exception as e:
                    print(f"檢查頁面結構時發生錯誤：{str(e)}")
            
            if pickup_type:
                print("準備選擇上車地點...")
                driver.save_screenshot('/app/before_pickup_type_select.png')
                
                # 根據元素類型選擇不同的操作方式
                element_type = pickup_type.tag_name
                element_input_type = pickup_type.get_attribute("type")
                
                if element_type == "select":
                    # 下拉選單
                    try:
                        from selenium.webdriver.support.ui import Select
                        select = Select(pickup_type)
                        select.select_by_visible_text("醫療院所")
                        print("使用 Select 類別選擇上車地點")
                    except:
                        try:
                            driver.execute_script("arguments[0].value = '醫療院所'; arguments[0].dispatchEvent(new Event('change'));", pickup_type)
                            print("使用 JavaScript 選擇上車地點")
                        except:
                            pickup_type.click()
                            time.sleep(1)
                            options = pickup_type.find_elements(By.TAG_NAME, "option")
                            for option in options:
                                if "醫療院所" in option.text:
                                    option.click()
                                    print("直接點擊選擇上車地點")
                                    break
                elif element_input_type == "radio":
                    # 單選框
                    try:
                        pickup_type.click()
                        print("點擊醫療院所單選框")
                    except:
                        driver.execute_script("arguments[0].click();", pickup_type)
                        print("使用 JavaScript 點擊醫療院所單選框")
                elif element_type == "button":
                    # 按鈕
                    try:
                        pickup_type.click()
                        print("點擊醫療院所按鈕")
                    except:
                        driver.execute_script("arguments[0].click();", pickup_type)
                        print("使用 JavaScript 點擊醫療院所按鈕")
                else:
                    # 其他元素
                    try:
                        pickup_type.click()
                        print("點擊上車地點元素")
                    except:
                        driver.execute_script("arguments[0].click();", pickup_type)
                        print("使用 JavaScript 點擊上車地點元素")
                
                print("已選擇上車地點...")
                driver.save_screenshot('/app/after_pickup_type_select.png')
                
                # 等待選擇生效
                try:
                    def is_selection_effective(driver):
                        try:
                            # 檢查元素是否被選中
                            if pickup_type.get_attribute("checked") == "true":
                                return True
                            
                            # 檢查是否出現相關元素
                            elements = driver.find_elements(By.XPATH, "//*[contains(text(), '醫療院所')]")
                            if any(element.is_displayed() for element in elements):
                                return True
                            
                            return False
                        except:
                            return False
                    
                    # 增加等待時間到 30 秒
                    WebDriverWait(driver, 30).until(is_selection_effective)
                    print("上車地點選擇已生效")
                    
                    # 等待一下確保選擇生效
                    time.sleep(2)
                    
                    # 尋找醫院名稱輸入框
                    print("尋找醫院名稱輸入框...")
                    hospital_input = None
                    
                    # 方法1：使用 XPath 尋找輸入框
                    try:
                        hospital_input = driver.find_element(By.XPATH, "//input[contains(@name, 'hospital') or contains(@id, 'hospital') or contains(@placeholder, '醫院')]")
                        print("使用 XPath 找到醫院名稱輸入框")
                    except:
                        print("使用 XPath 找不到醫院名稱輸入框")
                    
                    # 方法2：使用 CSS 選擇器尋找輸入框
                    if not hospital_input:
                        try:
                            hospital_input = driver.find_element(By.CSS_SELECTOR, "input.form-control, input[type='text']")
                            print("使用 CSS 選擇器找到醫院名稱輸入框")
                        except:
                            print("使用 CSS 選擇器找不到醫院名稱輸入框")
                    
                    # 方法3：尋找所有輸入框
                    if not hospital_input:
                        try:
                            inputs = driver.find_elements(By.TAG_NAME, "input")
                            for input_field in inputs:
                                if input_field.is_displayed() and input_field.get_attribute("type") == "text":
                                    hospital_input = input_field
                                    print("找到可見的文字輸入框")
                                    break
                        except:
                            print("找不到文字輸入框")
                    
                    if hospital_input:
                        print("準備輸入醫院名稱...")
                        driver.save_screenshot('/app/before_hospital_input.png')
                        
                        # 清空輸入框
                        hospital_input.clear()
                        
                        # 輸入醫院名稱
                        hospital_input.send_keys("亞東紀念醫院")
                        print("已輸入醫院名稱")
                        
                        # 等待一下確保輸入完成
                        time.sleep(2)
                        
                        # 等待 Google 搜尋結果出現
                        print("等待 Google 搜尋結果...")
                        try:
                            def wait_for_google_results(driver):
                                try:
                                    # 尋找搜尋結果列表
                                    results = driver.find_elements(By.CSS_SELECTOR, ".pac-item, .pac-container")
                                    if results and any(result.is_displayed() for result in results):
                                        return True
                                    return False
                                except:
                                    return False
                            
                            # 等待搜尋結果出現
                            WebDriverWait(driver, 10).until(wait_for_google_results)
                            print("Google 搜尋結果已出現")
                            
                            # 點擊第一個搜尋結果
                            results = driver.find_elements(By.CSS_SELECTOR, ".pac-item, .pac-container")
                            for result in results:
                                if result.is_displayed():
                                    print("準備點擊第一個搜尋結果...")
                                    driver.save_screenshot('/app/before_click_result.png')
                                    
                                    # 嘗試點擊搜尋結果
                                    try:
                                        result.click()
                                        print("已點擊第一個搜尋結果")
                                        driver.save_screenshot('/app/after_click_result.png')
                                        break
                                    except:
                                        try:
                                            # 使用 JavaScript 點擊
                                            driver.execute_script("arguments[0].click();", result)
                                            print("使用 JavaScript 點擊第一個搜尋結果")
                                            driver.save_screenshot('/app/after_click_result.png')
                                            break
                                        except:
                                            print("點擊搜尋結果失敗")
                                            continue
                        except TimeoutException:
                            print("等待 Google 搜尋結果超時")
                            driver.save_screenshot('/app/google_results_timeout.png')
                            return False
                    else:
                        print("找不到醫院名稱輸入框")
                        driver.save_screenshot('/app/hospital_input_not_found.png')
                        return False
                except TimeoutException:
                    print("等待上車地點選擇生效超時")
                    driver.save_screenshot('/app/pickup_type_timeout.png')
                    return False
            else:
                print("找不到上車地點下拉選單")
                driver.save_screenshot('/app/pickup_type_not_found.png')
                return False
        except Exception as e:
            print(f"選擇上車地點時發生錯誤：{str(e)}")
            driver.save_screenshot('/app/pickup_type_error.png')
            return False

        # 下車地點請下拉選擇「住家」
        print("選擇下車地點「住家」...")
        dropoff_type = driver.find_element(By.ID, "dropoffType")
        dropoff_type.send_keys("住家")
        driver.save_screenshot('/app/after_dropoff_type.png')

        # 預約日期/時段請下拉選擇最後一個選項，右邊請下拉選擇16，再往右邊請下拉選擇40
        print("選擇預約日期/時段...")
        date_select = driver.find_element(By.ID, "date")
        date_select.send_keys("最後一個選項")
        hour_select = driver.find_element(By.ID, "hour")
        hour_select.send_keys("16")
        minute_select = driver.find_element(By.ID, "minute")
        minute_select.send_keys("40")
        driver.save_screenshot('/app/after_time_selection.png')

        # 於預約時間前後30分鐘到達 選擇「不同意」
        print("選擇「不同意」於預約時間前後30分鐘到達...")
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//input[@value='不同意']"))
        ).click()
        driver.save_screenshot('/app/after_flexible_time.png')

        # 陪同人數 下拉選擇「1人(免費)」
        print("選擇陪同人數「1人(免費)」...")
        companion_select = driver.find_element(By.ID, "companion")
        companion_select.send_keys("1人(免費)")
        driver.save_screenshot('/app/after_companion.png')

        # 同意共乘 選擇「否」
        print("選擇「否」同意共乘...")
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//input[@value='否']"))
        ).click()
        driver.save_screenshot('/app/after_share_ride.png')

        # 搭乘輪椅上車 選擇「是」
        print("選擇「是」搭乘輪椅上車...")
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//input[@value='是']"))
        ).click()
        driver.save_screenshot('/app/after_wheelchair.png')

        # 大型輪椅 選擇「否」
        print("選擇「否」大型輪椅...")
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//input[@value='否']"))
        ).click()
        driver.save_screenshot('/app/after_large_wheelchair.png')

        # 點擊「下一步，確認預約資訊」按鈕
        print("點擊「下一步，確認預約資訊」按鈕...")
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), '下一步，確認預約資訊')]"))
        ).click()
        driver.save_screenshot('/app/after_next_step.png')

        # 新的頁面點擊「送出預約」
        print("點擊「送出預約」按鈕...")
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), '送出預約')]"))
        ).click()
        driver.save_screenshot('/app/after_submit.png')

        # 跳出「已完成預約」畫面，表示完成
        print("等待「已完成預約」畫面...")
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//*[contains(text(), '已完成預約')]"))
        )
        print("已完成預約")
        driver.save_screenshot('/app/after_success.png')
        return True
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        driver.save_screenshot('/app/error.png')
        print("error.png exists:", os.path.exists('/app/error.png'))
        return False
    finally:
        driver.quit()

@app.route('/')
def index():
    return jsonify({"status": "running"})

@app.route('/reserve')
def reservation():
    result = make_reservation()
    return jsonify({"success": result})

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                             'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route('/before-click')
def before_click():
    try:
        return send_file('/app/before_click.png', mimetype='image/png')
    except Exception as e:
        return jsonify({"error": "找不到截圖檔案"}), 404

@app.route('/after-click')
def after_click():
    try:
        return send_file('/app/after_click.png', mimetype='image/png')
    except Exception as e:
        return jsonify({"error": "找不到截圖檔案"}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080))) 