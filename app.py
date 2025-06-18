from flask import Flask, request, jsonify, send_from_directory
from playwright.sync_api import sync_playwright
import time
import os
import base64
from datetime import datetime

app = Flask(__name__)

def take_screenshot(driver, name):
    """截圖功能"""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"step_{name}_{timestamp}.png"
        driver['page'].screenshot(path=filename)
        print(f"截圖已保存: {filename}")
        
        # 將截圖轉換為 base64 以便在日誌中查看
        with open(filename, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode()
            print(f"截圖 base64: data:image/png;base64,{encoded_string[:100]}...")
            
    except Exception as e:
        print(f"截圖失敗: {e}")

def setup_driver():
    """設置 Playwright WebDriver"""
    try:
        print("正在初始化 Playwright...")
        playwright = sync_playwright().start()
        
        # 使用 Playwright 的 Chromium
        browser = playwright.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-dev-shm-usage',
                '--disable-gpu',
                '--disable-web-security',
                '--disable-features=VizDisplayCompositor',
                '--disable-extensions',
                '--disable-plugins',
                '--disable-images',
                '--disable-javascript',
                '--disable-background-timer-throttling',
                '--disable-backgrounding-occluded-windows',
                '--disable-renderer-backgrounding',
                '--disable-features=TranslateUI',
                '--disable-ipc-flooding-protection',
                '--memory-pressure-off',
                '--max_old_space_size=4096'
            ]
        )
        
        context = browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        
        page = context.new_page()
        
        # 創建 driver 字典
        driver = {
            'page': page,
            'context': context,
            'browser': browser,
            'playwright': playwright,
            'get': lambda url: page.goto(url),
            'title': lambda: page.title(),
            'current_url': lambda: page.url,
            'get_window_size': lambda: {'width': 1920, 'height': 1080}
        }
        
        print("Playwright 初始化成功")
        return driver
        
    except Exception as e:
        print(f"Playwright 初始化失敗: {e}")
        return None

def make_reservation():
    driver = None
    screenshot_count = 0
    
    def take_screenshot(description):
        nonlocal screenshot_count
        try:
            screenshot_count += 1
            filename = f'step_{screenshot_count:03d}_{description}.png'
            if driver:
                driver['page'].screenshot(path=filename)
                print(f"截圖 {screenshot_count}: {description} - {filename}")
            return filename
        except Exception as e:
            print(f"截圖失敗: {e}")
            return None
    
    try:
        print("=== 開始執行預約流程 ===")
        print("開始初始化 WebDriver...")
        driver = setup_driver()
        
        if driver is None:
            print("WebDriver 初始化失敗，無法繼續")
            return False
            
        print("WebDriver 初始化完成")
        
        # 設置視窗大小為高解析度
        print("設置視窗大小為 1920x1080...")
        driver['page'].set_viewport_size({'width': 1920, 'height': 1080})
        print("視窗大小設置完成")
        
        print("正在載入網頁...")
        driver['get']("https://www.ntpc.ltc-car.org/")
        print("網頁載入完成")
        take_screenshot("page_loaded")
        
        # 等待頁面完全載入
        print("等待頁面完全載入...")
        driver['page'].wait_for_load_state("networkidle")
        print("頁面已完全載入")
        take_screenshot("page_complete")
        
        # 處理浮動視窗 - 點擊「我知道了」按鈕
        print("檢查並處理浮動視窗...")
        try:
            # 等待浮動視窗出現
            driver['page'].wait_for_selector('text=我知道了', timeout=10000)
            print("找到浮動視窗，點擊「我知道了」按鈕")
            driver['page'].click('text=我知道了')
            print("「我知道了」按鈕點擊成功")
            take_screenshot("popup_closed")
        except Exception as e:
            print(f"沒有找到浮動視窗或點擊失敗: {e}")
            take_screenshot("no_popup_found")
        
        # 登入步驟
        print("開始登入流程...")
        try:
            # 等待登入表單載入
            driver['page'].wait_for_selector('input[type="text"]', timeout=10000)
            print("登入表單已載入")
            take_screenshot("login_form")
            
            # 輸入身分證字號
            print("輸入身分證字號: A102574899")
            driver['page'].fill('input[type="text"]', 'A102574899')
            
            # 輸入密碼
            print("輸入密碼: visi319VISI")
            driver['page'].fill('input[type="password"]', 'visi319VISI')
            
            # 點擊民眾登入按鈕 - 使用更精確的選擇器
            print("點擊民眾登入按鈕")
            take_screenshot("before_login_click")
            
            # 嘗試多種不同類型的登入按鈕選擇器
            login_selectors = [
                # 一般按鈕
                'button:has-text("民眾登入")',
                'button[value*="民眾登入"]',
                'button[name*="login"]',
                
                # input 按鈕
                'input[type="submit"]:has-value("民眾登入")',
                'input[type="button"]:has-value("民眾登入")',
                'input[value="民眾登入"]',
                'input[value*="登入"]',
                
                # 連結
                'a:has-text("民眾登入")',
                'a[href*="login"]',
                
                # 表單提交
                'form input[type="submit"]',
                'form button[type="submit"]',
                
                # 通用文字匹配
                'text=民眾登入',
                ':text("民眾登入")',
                '*:has-text("民眾登入")',
                
                # CSS 類別
                '.login-btn',
                '.btn-login',
                '.submit-btn',
                '.btn[onclick*="login"]',
                
                # ID 選擇器
                '#login-btn',
                '#loginBtn',
                '#submit',
                '#login',
                
                # 更廣泛的匹配
                '[onclick*="login"]',
                '[onclick*="submit"]'
            ]
            
            login_clicked = False
            
            for selector in login_selectors:
                try:
                    print(f"嘗試登入按鈕選擇器: {selector}")
                    
                    # 檢查元素是否存在
                    element = driver['page'].locator(selector).first
                    if element.count() > 0:
                        print(f"找到元素: {selector}")
                        
                        # 檢查元素是否可見
                        if element.is_visible():
                            print(f"元素可見，嘗試點擊: {selector}")
                            element.click()
                            print(f"登入按鈕點擊成功: {selector}")
                            login_clicked = True
                            break
                        else:
                            print(f"元素存在但不可見: {selector}")
                    else:
                        print(f"元素不存在: {selector}")
                        
                except Exception as e:
                    print(f"登入按鈕選擇器 {selector} 失敗: {e}")
                    continue
            
            # 如果還是沒點擊成功，嘗試更激進的方法
            if not login_clicked:
                print("所有標準方法失敗，嘗試更激進的方法...")
                
                try:
                    # 方法1: 檢查所有按鈕的文字內容
                    print("檢查所有按鈕...")
                    all_buttons = driver['page'].locator('button, input[type="button"], input[type="submit"]').all()
                    for i, button in enumerate(all_buttons):
                        try:
                            if button.is_visible():
                                button_text = button.text_content() or button.get_attribute('value') or ''
                                print(f"按鈕 {i}: '{button_text}'")
                                if '登入' in button_text or 'login' in button_text.lower():
                                    print(f"找到疑似登入按鈕，點擊: {button_text}")
                                    button.click()
                                    login_clicked = True
                                    break
                        except Exception as e:
                            print(f"檢查按鈕 {i} 失敗: {e}")
                            continue
                except Exception as e:
                    print(f"檢查所有按鈕失敗: {e}")
                
                # 方法2: 嘗試提交表單
                if not login_clicked:
                    try:
                        print("嘗試直接提交登入表單...")
                        forms = driver['page'].locator('form').all()
                        for i, form in enumerate(forms):
                            try:
                                print(f"提交表單 {i}")
                                # 使用 JavaScript 提交表單
                                driver['page'].evaluate(f'document.forms[{i}].submit()')
                                login_clicked = True
                                break
                            except Exception as e:
                                print(f"提交表單 {i} 失敗: {e}")
                                continue
                    except Exception as e:
                        print(f"表單提交失敗: {e}")
                
                # 方法3: 使用 JavaScript 尋找並點擊
                if not login_clicked:
                    try:
                        print("使用 JavaScript 尋找登入按鈕...")
                        js_script = """
                        // 尋找包含"登入"文字的元素
                        const elements = Array.from(document.querySelectorAll('*'));
                        for (let elem of elements) {
                            const text = elem.textContent || elem.value || '';
                            if (text.includes('登入') || text.includes('民眾')) {
                                if (elem.tagName === 'BUTTON' || elem.tagName === 'INPUT' || elem.tagName === 'A') {
                                    console.log('找到登入元素:', elem);
                                    elem.click();
                                    return true;
                                }
                            }
                        }
                        return false;
                        """
                        result = driver['page'].evaluate(js_script)
                        if result:
                            print("JavaScript 點擊成功")
                            login_clicked = True
                    except Exception as e:
                        print(f"JavaScript 點擊失敗: {e}")
            
            if login_clicked:
                print("登入按鈕點擊完成")
                take_screenshot("login_clicked")
            else:
                print("警告：無法找到或點擊登入按鈕")
                take_screenshot("login_click_failed")
            
            # 等待登入成功浮動視窗
            print("等待登入成功訊息...")
            try:
                # 專門針對浮動視窗的選擇器
                modal_selectors = [
                    '.modal:has-text("登入成功")',
                    '.dialog:has-text("登入成功")', 
                    '.popup:has-text("登入成功")',
                    '.alert:has-text("登入成功")',
                    '[role="dialog"]:has-text("登入成功")',
                    '.swal-modal:has-text("登入成功")',
                    '.modal-content:has-text("登入成功")',
                    '.ui-dialog:has-text("登入成功")'
                ]
                
                # 先嘗試找到浮動視窗
                modal_found = False
                modal_element = None
                
                for selector in modal_selectors:
                    try:
                        print(f"尋找浮動視窗: {selector}")
                        modal_element = driver['page'].wait_for_selector(selector, timeout=5000)
                        print(f"找到登入成功浮動視窗: {selector}")
                        modal_found = True
                        break
                    except Exception as e:
                        print(f"浮動視窗選擇器 {selector} 未找到: {e}")
                        continue
                
                # 如果沒找到特定的浮動視窗，嘗試通用的登入成功訊息
                if not modal_found:
                    generic_selectors = [
                        'text=登入成功',
                        ':text("登入成功")',
                        '*:has-text("登入成功")'
                    ]
                    
                    for selector in generic_selectors:
                        try:
                            print(f"尋找通用登入成功訊息: {selector}")
                            driver['page'].wait_for_selector(selector, timeout=3000)
                            print(f"找到登入成功訊息: {selector}")
                            modal_found = True
                            break
                        except Exception as e:
                            print(f"通用選擇器 {selector} 未找到: {e}")
                            continue
                
                if modal_found:
                    # 截圖記錄找到登入成功訊息
                    take_screenshot("login_success_modal_found")
                    
                    # 等待一下讓浮動視窗完全顯示
                    driver['page'].wait_for_timeout(1000)
                    
                    # 尋找確定按鈕 - 專門針對浮動視窗內的按鈕
                    confirm_selectors = [
                        '.modal button:has-text("確定")',
                        '.dialog button:has-text("確定")',
                        '.popup button:has-text("確定")',
                        '.alert button:has-text("確定")',
                        '[role="dialog"] button:has-text("確定")',
                        '.swal-button:has-text("確定")',
                        '.modal-footer button:has-text("確定")',
                        '.ui-dialog-buttonset button:has-text("確定")',
                        'button:has-text("確定")',
                        'text=確定',
                        '.btn:has-text("確定")',
                        'input[value="確定"]'
                    ]
                    
                    confirm_clicked = False
                    for confirm_selector in confirm_selectors:
                        try:
                            print(f"嘗試點擊確定按鈕: {confirm_selector}")
                            # 等待按鈕可見
                            button = driver['page'].wait_for_selector(confirm_selector, timeout=3000)
                            if button.is_visible():
                                button.click()
                                print(f"確定按鈕點擊成功: {confirm_selector}")
                                confirm_clicked = True
                                break
                        except Exception as e:
                            print(f"確定按鈕 {confirm_selector} 點擊失敗: {e}")
                            continue
                    
                    if not confirm_clicked:
                        print("未找到確定按鈕，嘗試點擊任何可見的按鈕")
                        try:
                            # 嘗試點擊浮動視窗中的任何按鈕
                            buttons = driver['page'].locator('button').all()
                            for button in buttons:
                                if button.is_visible():
                                    button_text = button.text_content()
                                    print(f"發現按鈕: {button_text}")
                                    if any(word in button_text for word in ['確定', 'OK', '好', '關閉']):
                                        button.click()
                                        print(f"點擊按鈕: {button_text}")
                                        confirm_clicked = True
                                        break
                        except Exception as e:
                            print(f"嘗試點擊其他按鈕失敗: {e}")
                    
                    if not confirm_clicked:
                        print("所有按鈕點擊嘗試失敗，嘗試按 ESC 鍵關閉浮動視窗")
                        driver['page'].keyboard.press('Escape')
                    
                    print("登入成功確認完成")
                    take_screenshot("login_success_confirmed")
                else:
                    print("沒有找到登入成功浮動視窗，可能已經登入成功或登入失敗")
                    take_screenshot("no_login_success_modal")
                    
            except Exception as e:
                print(f"登入成功檢測過程發生錯誤: {e}")
                take_screenshot("login_success_detection_error")
            
            # 等待登入完成
            print("等待登入完成...")
            driver['page'].wait_for_load_state("networkidle")
            print("登入流程完成")
            take_screenshot("login_complete")
            
        except Exception as e:
            print(f"登入過程發生錯誤: {e}")
            take_screenshot("login_error")
            return False
        
        # 開始預約流程
        print("開始預約流程...")
        try:
            # 5. 點擊「新增預約」
            print("點擊新增預約")
            driver['page'].click('text=新增預約')
            driver['page'].wait_for_load_state("networkidle")
            take_screenshot("new_reservation")
            
            # 6. 上車地點選擇「醫療院所」
            print("選擇上車地點：醫療院所")
            driver['page'].select_option('select', '醫療院所')
            take_screenshot("pickup_location")
            
            # 7. 輸入「亞東紀念醫院」並選擇第一個搜尋結果
            print("尋找上車地點輸入框...")
            
            # 嘗試多種搜尋框選擇器
            input_selectors = [
                # 通用地點輸入框
                'input[placeholder*="地點"]',
                'input[placeholder*="起點"]',
                'input[placeholder*="上車"]',
                'input[placeholder*="出發"]',
                'input[placeholder*="from"]',
                'input[placeholder*="起始"]',
                
                # 根據 name 屬性
                'input[name*="pickup"]',
                'input[name*="origin"]',
                'input[name*="from"]',
                'input[name*="start"]',
                'input[name*="departure"]',
                
                # 根據 ID
                '#pickup-location',
                '#origin',
                '#from-location',
                '#start-location',
                '#departure',
                
                # 根據 class
                '.pickup-input',
                '.origin-input',
                '.location-input',
                '.address-input',
                
                # 通用輸入框（按順序）
                'form input[type="text"]:nth-of-type(1)',
                'form input[type="text"]:first-of-type',
                'input[type="text"]:nth-of-type(1)',
                'input[type="text"]:first-of-type',
                
                # 更廣泛的搜尋
                'input[type="text"]'
            ]
            
            pickup_input = None
            input_found = False
            
            for selector in input_selectors:
                try:
                    print(f"嘗試搜尋框選擇器: {selector}")
                    elements = driver['page'].locator(selector).all()
                    
                    for i, element in enumerate(elements):
                        try:
                            if element.is_visible() and element.is_enabled():
                                # 檢查是否為上車地點相關的輸入框
                                placeholder = element.get_attribute('placeholder') or ''
                                name = element.get_attribute('name') or ''
                                id_attr = element.get_attribute('id') or ''
                                class_attr = element.get_attribute('class') or ''
                                
                                print(f"找到輸入框 {i}: placeholder='{placeholder}', name='{name}', id='{id_attr}', class='{class_attr}'")
                                
                                # 如果是明確的上車地點輸入框，優先使用
                                if any(keyword in (placeholder + name + id_attr + class_attr).lower() 
                                      for keyword in ['地點', '起點', '上車', '出發', 'pickup', 'origin', 'from', 'start']):
                                    pickup_input = element
                                    input_found = True
                                    print(f"找到上車地點輸入框: {selector} (索引 {i})")
                                    break
                                elif not pickup_input:  # 如果還沒找到明確的，先暫存這個
                                    pickup_input = element
                        except Exception as e:
                            print(f"檢查輸入框 {i} 失敗: {e}")
                            continue
                    
                    if input_found:
                        break
                        
                except Exception as e:
                    print(f"搜尋框選擇器 {selector} 失敗: {e}")
                    continue
            
            if not pickup_input:
                print("警告：無法找到上車地點輸入框")
                take_screenshot("no_input_found")
                return False
            
            print("輸入上車地點：亞東紀念醫院")
            try:
                # 確保輸入框有焦點
                pickup_input.click()
                driver['page'].wait_for_timeout(500)
                
                # 清空輸入框
                pickup_input.clear()
                driver['page'].wait_for_timeout(500)
                
                # 使用多種方式輸入
                try:
                    # 方法1: 使用 fill
                    pickup_input.fill('亞東紀念醫院')
                    driver['page'].wait_for_timeout(1000)
                    
                    # 檢查是否成功輸入
                    current_value = pickup_input.input_value()
                    print(f"輸入後的值: '{current_value}'")
                    
                    if '亞東' not in current_value:
                        print("fill 方法可能失敗，嘗試 type 方法...")
                        pickup_input.clear()
                        pickup_input.type('亞東紀念醫院')
                        driver['page'].wait_for_timeout(1000)
                        current_value = pickup_input.input_value()
                        print(f"type 後的值: '{current_value}'")
                        
                        if '亞東' not in current_value:
                            print("type 方法也失敗，嘗試 JavaScript...")
                            # 使用 JavaScript 直接設置值
                            script = """
                            (element) => {
                                element.value = '亞東紀念醫院';
                                element.dispatchEvent(new Event('input', { bubbles: true }));
                                element.dispatchEvent(new Event('change', { bubbles: true }));
                            }
                            """
                            pickup_input.evaluate(script)
                            driver['page'].wait_for_timeout(1000)
                            current_value = pickup_input.input_value()
                            print(f"JavaScript 後的值: '{current_value}'")
                    
                except Exception as e:
                    print(f"輸入過程發生錯誤: {e}")
                
                take_screenshot("hospital_input_filled")
                
            except Exception as e:
                print(f"輸入亞東紀念醫院失敗: {e}")
                take_screenshot("hospital_input_failed")
                return False
            
            # 等待 Google 搜尋結果出現
            print("等待搜尋結果出現...")
            driver['page'].wait_for_timeout(3000)  # 等待搜尋結果載入
            take_screenshot("search_results_waiting")
            
            # 嘗試多種搜尋結果選擇器
            search_result_selectors = [
                # Google Places 自動完成
                '.pac-item:first-child',
                '.pac-container .pac-item:first-child',
                '.pac-item:nth-child(1)',
                
                # 一般自動完成下拉選項
                '.autocomplete-item:first-child',
                '.autocomplete-suggestion:first-child',
                '.suggestion:first-child',
                '.dropdown-item:first-child',
                
                # 搜尋結果容器
                '.search-results .result:first-child',
                '.results .result:first-child',
                '.search-result:first-child',
                
                # 通用下拉選項
                '.dropdown li:first-child',
                '.dropdown-menu li:first-child',
                '.menu-item:first-child',
                
                # 更通用的選擇器
                'ul li:first-child',
                '.ui-menu-item:first-child',
                '[role="option"]:first-child',
                
                # 包含醫院文字的選項
                'li:has-text("亞東")',
                'div:has-text("亞東紀念醫院")',
                '*:has-text("亞東紀念醫院")'
            ]
            
            search_result_clicked = False
            
            for selector in search_result_selectors:
                try:
                    print(f"嘗試搜尋結果選擇器: {selector}")
                    
                    # 等待元素出現
                    element = driver['page'].wait_for_selector(selector, timeout=5000)
                    if element and element.is_visible():
                        print(f"找到搜尋結果，點擊: {selector}")
                        element.click()
                        search_result_clicked = True
                        break
                    else:
                        print(f"搜尋結果元素不可見: {selector}")
                        
                except Exception as e:
                    print(f"搜尋結果選擇器 {selector} 失敗: {e}")
                    continue
            
            # 如果標準方法失敗，嘗試其他方法
            if not search_result_clicked:
                print("標準方法失敗，嘗試其他方法...")
                
                try:
                    # 方法1: 檢查所有可見的 li 元素
                    print("檢查所有可見的列表項目...")
                    all_lis = driver['page'].locator('li').all()
                    for i, li in enumerate(all_lis):
                        try:
                            if li.is_visible():
                                li_text = li.text_content() or ''
                                print(f"列表項目 {i}: '{li_text}'")
                                if '亞東' in li_text or '醫院' in li_text:
                                    print(f"找到疑似醫院選項，點擊: {li_text}")
                                    li.click()
                                    search_result_clicked = True
                                    break
                        except Exception as e:
                            print(f"檢查列表項目 {i} 失敗: {e}")
                            continue
                except Exception as e:
                    print(f"檢查列表項目失敗: {e}")
                
                # 方法2: 使用鍵盤導航
                if not search_result_clicked:
                    try:
                        print("嘗試使用鍵盤選擇第一個結果...")
                        # 按向下箭頭選擇第一個結果
                        driver['page'].keyboard.press('ArrowDown')
                        driver['page'].wait_for_timeout(500)
                        # 按 Enter 確認選擇
                        driver['page'].keyboard.press('Enter')
                        search_result_clicked = True
                        print("鍵盤選擇成功")
                    except Exception as e:
                        print(f"鍵盤選擇失敗: {e}")
                
                # 方法3: JavaScript 搜尋和點擊
                if not search_result_clicked:
                    try:
                        print("使用 JavaScript 尋找搜尋結果...")
                        js_script = """
                        // 尋找包含"亞東"的可見元素
                        const elements = Array.from(document.querySelectorAll('*'));
                        for (let elem of elements) {
                            if (elem.offsetParent !== null) { // 檢查是否可見
                                const text = elem.textContent || '';
                                if (text.includes('亞東') && (
                                    elem.tagName === 'LI' || 
                                    elem.tagName === 'DIV' || 
                                    elem.classList.contains('pac-item') ||
                                    elem.classList.contains('autocomplete-item') ||
                                    elem.classList.contains('result')
                                )) {
                                    console.log('找到搜尋結果:', elem);
                                    elem.click();
                                    return true;
                                }
                            }
                        }
                        return false;
                        """
                        result = driver['page'].evaluate(js_script)
                        if result:
                            print("JavaScript 搜尋結果點擊成功")
                            search_result_clicked = True
                    except Exception as e:
                        print(f"JavaScript 搜尋結果點擊失敗: {e}")
            
            if search_result_clicked:
                print("搜尋結果選擇成功")
                take_screenshot("pickup_selected")
                # 等待選擇完成
                driver['page'].wait_for_timeout(2000)
            else:
                print("警告：無法選擇搜尋結果，繼續執行...")
                take_screenshot("pickup_selection_failed")
            
            # 8. 下車地點選擇「住家」
            print("選擇下車地點：住家")
            driver['page'].select_option('select', '住家')
            take_screenshot("dropoff_location")
            
            # 9. 預約日期/時段選擇
            print("選擇預約日期/時段")
            # 選擇最後一個日期選項
            date_selects = driver['page'].locator('select').all()
            if len(date_selects) >= 3:
                # 選擇最後一個日期
                last_date_option = date_selects[0].locator('option').last
                last_date_option.click()
                
                # 選擇時間 16
                time_selects = driver['page'].locator('select').all()
                if len(time_selects) >= 2:
                    time_selects[1].select_option('16')
                
                # 選擇分鐘 40
                if len(time_selects) >= 3:
                    time_selects[2].select_option('40')
            take_screenshot("datetime_selected")
            
            # 10. 於預約時間前後30分鐘到達 選擇「不同意」
            print("選擇不同意前後30分鐘到達")
            driver['page'].click('text=不同意')
            take_screenshot("time_window")
            
            # 11. 陪同人數 選擇「1人(免費)」
            print("選擇陪同人數：1人(免費)")
            driver['page'].select_option('select', '1人(免費)')
            take_screenshot("companion")
            
            # 12. 同意共乘 選擇「否」
            print("選擇不同意共乘")
            driver['page'].click('text=否')
            take_screenshot("carpool")
            
            # 13. 搭乘輪椅上車 選擇「是」
            print("選擇搭乘輪椅上車：是")
            driver['page'].click('text=是')
            take_screenshot("wheelchair")
            
            # 14. 大型輪椅 選擇「否」
            print("選擇大型輪椅：否")
            driver['page'].click('text=否')
            take_screenshot("large_wheelchair")
            
            # 15. 點擊「下一步，確認預約資訊」
            print("點擊下一步，確認預約資訊")
            driver['page'].click('text=下一步，確認預約資訊')
            driver['page'].wait_for_load_state("networkidle")
            take_screenshot("confirm_info")
            
            # 16. 點擊「送出預約」
            print("點擊送出預約")
            driver['page'].click('text=送出預約')
            driver['page'].wait_for_load_state("networkidle")
            take_screenshot("submit_reservation")
            
            # 17. 檢查「已完成預約」畫面
            print("檢查預約完成狀態...")
            try:
                driver['page'].wait_for_selector('text=已完成預約', timeout=10000)
                print("預約成功完成！")
                take_screenshot("reservation_success")
                return True
            except Exception as e:
                print(f"沒有找到預約完成訊息: {e}")
                take_screenshot("reservation_unknown")
                return False
                
        except Exception as e:
            print(f"預約過程發生錯誤: {e}")
            take_screenshot("reservation_error")
            return False
        
        return True
        
    except Exception as e:
        print(f"預約流程發生錯誤: {e}")
        if driver:
            take_screenshot("error")
        return False
        
    finally:
        # 清理資源
        if driver:
            try:
                driver['browser'].close()
                driver['playwright'].stop()
                print("WebDriver 已關閉")
            except:
                pass

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
    try:
        return send_from_directory('.', filename)
    except Exception as e:
        print(f"讀取截圖失敗: {e}")
        return f"無法讀取截圖: {filename}", 404

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

@app.route('/test')
def test():
    return jsonify({"status": "ok", "message": "Flask 應用程式正常運行"})

@app.route('/reserve')
def reservation():
    try:
        print("=== 開始執行預約流程 ===")
        result = make_reservation()
        print(f"=== 預約流程執行結果: {result} ===")
        return jsonify({"success": result, "message": "預約流程執行完成"})
    except Exception as e:
        import traceback
        error_msg = f"預約流程執行失敗: {str(e)}"
        print(error_msg)
        print("詳細錯誤資訊:")
        print(traceback.format_exc())
        return jsonify({"success": False, "error": error_msg}), 500

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                             'favicon.ico', mimetype='image/vnd.microsoft.icon')

if __name__ == '__main__':
    # Zeabur 環境變數
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port) 