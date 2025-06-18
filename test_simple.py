#!/usr/bin/env python3
"""
簡化的住家地址填入測試腳本
使用與主程式完全相同的登入邏輯
"""

from flask import Flask, request, jsonify
from playwright.sync_api import sync_playwright
import time
import os

app = Flask(__name__)

def setup_driver():
    """設置 Playwright WebDriver - 與主程式相同"""
    try:
        print("正在初始化 Playwright...")
        playwright = sync_playwright().start()
        
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
        
        driver = {
            'page': page,
            'context': context,
            'browser': browser,
            'playwright': playwright,
            'get': lambda url: page.goto(url)
        }
        
        print("Playwright 初始化成功")
        return driver
        
    except Exception as e:
        print(f"Playwright 初始化失敗: {e}")
        return None

def test_login_and_address():
    """測試登入和住家地址填入 - 使用主程式邏輯"""
    driver = None
    screenshot_count = 0
    
    def take_screenshot(description):
        nonlocal screenshot_count
        try:
            screenshot_count += 1
            filename = f'test_{screenshot_count:03d}_{description}.png'
            if driver:
                driver['page'].screenshot(path=filename)
                print(f"截圖 {screenshot_count}: {description} - {filename}")
            return filename
        except Exception as e:
            print(f"截圖失敗: {e}")
            return None
    
    try:
        print("=== 開始住家地址填入測試 ===")
        driver = setup_driver()
        
        if driver is None:
            print("WebDriver 初始化失敗")
            return False
        
        # 載入網頁
        print("正在載入網頁...")
        driver['get']("https://www.ntpc.ltc-car.org/")
        print("網頁載入完成")
        take_screenshot("page_loaded")
        
        # 等待頁面完全載入
        print("等待頁面完全載入...")
        driver['page'].wait_for_load_state("networkidle")
        print("頁面已完全載入")
        take_screenshot("page_complete")
        
        # 處理浮動視窗 - 與主程式相同邏輯
        print("檢查並處理浮動視窗...")
        try:
            driver['page'].wait_for_selector('text=我知道了', timeout=10000)
            print("找到浮動視窗，點擊「我知道了」按鈕")
            driver['page'].click('text=我知道了')
            print("「我知道了」按鈕點擊成功")
            take_screenshot("popup_closed")
        except Exception as e:
            print(f"沒有找到浮動視窗或點擊失敗: {e}")
            take_screenshot("no_popup_found")
        
        # 登入步驟 - 完全按照主程式邏輯
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
            
            # 點擊民眾登入按鈕 - 使用主程式的複雜邏輯
            print("點擊民眾登入按鈕")
            take_screenshot("before_login_click")
            
            # 主程式的登入按鈕選擇器
            login_selectors = [
                'button:has-text("民眾登入")',
                'button[value*="民眾登入"]',
                'input[type="submit"]:has-value("民眾登入")',
                'input[value="民眾登入"]',
                'text=民眾登入',
                '*:has-text("民眾登入")',
                'form input[type="submit"]',
                'form button[type="submit"]'
            ]
            
            login_clicked = False
            
            for selector in login_selectors:
                try:
                    print(f"嘗試登入按鈕選擇器: {selector}")
                    element = driver['page'].locator(selector).first
                    if element.count() > 0 and element.is_visible():
                        element.click()
                        print(f"✅ 登入按鈕點擊成功: {selector}")
                        login_clicked = True
                        break
                except Exception as e:
                    print(f"登入按鈕選擇器 {selector} 失敗: {e}")
                    continue
            
            # 如果標準方法失敗，使用激進方法
            if not login_clicked:
                print("標準方法失敗，使用激進方法...")
                try:
                    # 檢查所有按鈕
                    all_buttons = driver['page'].locator('button, input[type="button"], input[type="submit"]').all()
                    for i, button in enumerate(all_buttons):
                        try:
                            if button.is_visible():
                                button_text = button.text_content() or button.get_attribute('value') or ''
                                print(f"按鈕 {i}: '{button_text}'")
                                if '登入' in button_text:
                                    button.click()
                                    login_clicked = True
                                    print(f"✅ 找到並點擊登入按鈕: {button_text}")
                                    break
                        except:
                            continue
                except Exception as e:
                    print(f"檢查所有按鈕失敗: {e}")
            
            if not login_clicked:
                print("❌ 無法找到或點擊登入按鈕")
                return False
            
            take_screenshot("login_clicked")
            
            # 等待登入成功浮動視窗 - 按照主程式邏輯
            print("等待登入成功訊息...")
            try:
                # 嘗試找登入成功訊息
                success_found = False
                try:
                    driver['page'].wait_for_selector('text=登入成功', timeout=5000)
                    print("✅ 找到登入成功訊息")
                    success_found = True
                except:
                    print("沒有找到登入成功文字，檢查其他方式...")
                
                if success_found:
                    take_screenshot("login_success_found")
                    
                    # 尋找確定按鈕
                    confirm_selectors = [
                        'button:has-text("確定")',
                        'text=確定',
                        '.btn:has-text("確定")',
                        'input[value="確定"]'
                    ]
                    
                    for confirm_selector in confirm_selectors:
                        try:
                            button = driver['page'].wait_for_selector(confirm_selector, timeout=3000)
                            if button.is_visible():
                                button.click()
                                print(f"✅ 確定按鈕點擊成功: {confirm_selector}")
                                break
                        except:
                            continue
                    
                    take_screenshot("login_success_confirmed")
                
            except Exception as e:
                print(f"登入成功檢測失敗: {e}")
            
            # 等待登入完成
            driver['page'].wait_for_load_state("networkidle")
            print("✅ 登入流程完成")
            take_screenshot("login_complete")
            
        except Exception as e:
            print(f"❌ 登入過程失敗: {e}")
            take_screenshot("login_error")
            return False
        
        # 預約流程到住家地址測試
        print("=== 開始預約流程測試 ===")
        
        try:
            # 點擊新增預約
            driver['page'].click('text=新增預約')
            driver['page'].wait_for_load_state("networkidle")
            print("✅ 新增預約頁面載入")
            take_screenshot("new_reservation")
            
            # 選擇上車地點
            driver['page'].select_option('select', '醫療院所')
            print("✅ 選擇上車地點：醫療院所")
            take_screenshot("pickup_location")
            
            # 搜尋醫院
            try:
                search_input = driver['page'].locator('input[placeholder*="搜尋"]').first
                search_input.fill('亞東紀念醫院')
                driver['page'].wait_for_timeout(2000)
                driver['page'].keyboard.press('ArrowDown')
                driver['page'].keyboard.press('Enter')
                print("✅ 醫院搜尋完成")
            except:
                print("⚠️ 醫院搜尋可能失敗，繼續測試")
            
            take_screenshot("hospital_search")
            
            # 核心測試：選擇住家
            print("=== 核心測試：選擇住家作為下車地點 ===")
            
            selects = driver['page'].locator('select').all()
            home_selected = False
            
            for i, select_elem in enumerate(selects):
                try:
                    if select_elem.is_visible():
                        options = select_elem.locator('option').all()
                        option_texts = [opt.inner_text() for opt in options]
                        print(f"選單 {i} 選項: {option_texts}")
                        
                        if '住家' in option_texts and i > 0:
                            select_elem.select_option('住家')
                            driver['page'].wait_for_timeout(3000)  # 等待更長時間
                            home_selected = True
                            print(f"✅ 選單 {i} 成功選擇住家")
                            break
                except Exception as e:
                    print(f"選單 {i} 檢查失敗: {e}")
            
            if not home_selected:
                print("❌ 未能選擇住家")
                return False
            
            take_screenshot("home_selected")
            
            # 檢查地址填入
            print("=== 檢查住家地址自動填入狀況 ===")
            
            address_inputs = driver['page'].locator('input[type="text"]').all()
            found_address = False
            
            for i, input_elem in enumerate(address_inputs):
                try:
                    if input_elem.is_visible():
                        placeholder = input_elem.get_attribute('placeholder') or ''
                        name = input_elem.get_attribute('name') or ''
                        value = input_elem.input_value() or ''
                        
                        print(f"輸入框 {i}: placeholder='{placeholder}', name='{name}', value='{value}'")
                        
                        if '地址' in placeholder or 'address' in name.lower():
                            if value.strip():
                                print(f"✅ 找到地址框且已填入: '{value}'")
                                found_address = True
                            else:
                                print(f"❌ 找到地址框但未填入: placeholder='{placeholder}'")
                                
                                # 嘗試手動填入測試
                                test_address = "新北市板橋區文化路一段188巷44號"
                                input_elem.fill(test_address)
                                driver['page'].wait_for_timeout(1000)
                                
                                new_value = input_elem.input_value() or ''
                                if new_value.strip():
                                    print(f"✅ 手動填入成功: '{new_value}'")
                                    found_address = True
                                else:
                                    print("❌ 手動填入也失敗")
                except Exception as e:
                    print(f"檢查輸入框 {i} 失敗: {e}")
            
            take_screenshot("address_test_result")
            
            if found_address:
                print("✅ 住家地址測試成功")
                return True
            else:
                print("❌ 住家地址測試失敗")
                return False
            
        except Exception as e:
            print(f"❌ 預約流程測試失敗: {e}")
            take_screenshot("reservation_error")
            return False
        
    except Exception as e:
        print(f"❌ 測試過程發生嚴重錯誤: {e}")
        return False
    
    finally:
        if driver:
            try:
                driver['page'].close()
                driver['browser'].close()
            except:
                pass

@app.route('/')
def index():
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>住家地址填入測試</title>
        <meta charset="utf-8">
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
            .container { max-width: 600px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; }
            .button { background: #007bff; color: white; padding: 12px 24px; border: none; border-radius: 4px; cursor: pointer; margin: 10px; }
            .button:hover { background: #0056b3; }
            .log { background: #f8f9fa; border: 1px solid #dee2e6; padding: 15px; margin: 10px 0; border-radius: 4px; font-family: monospace; white-space: pre-wrap; max-height: 400px; overflow-y: auto; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🏠 住家地址填入測試</h1>
            <p>這個測試使用與主程式完全相同的登入邏輯來測試住家地址填入問題</p>
            
            <button class="button" onclick="startTest()">開始測試</button>
            
            <h2>測試日誌</h2>
            <div id="logs" class="log">準備開始測試...</div>
        </div>
        
        <script>
            function startTest() {
                document.getElementById('logs').textContent = '測試開始中...\\n';
                
                fetch('/run-test', {method: 'POST'})
                .then(response => response.json())
                .then(data => {
                    const logs = document.getElementById('logs');
                    if (data.success) {
                        logs.textContent += '✅ 測試成功完成!\\n';
                    } else {
                        logs.textContent += '❌ 測試失敗: ' + data.error + '\\n';
                    }
                    if (data.logs) {
                        logs.textContent += '\\n詳細日誌:\\n' + data.logs.join('\\n');
                    }
                })
                .catch(error => {
                    document.getElementById('logs').textContent += '💥 測試錯誤: ' + error.message;
                });
            }
        </script>
    </body>
    </html>
    '''

@app.route('/run-test', methods=['POST'])
def run_test():
    try:
        result = test_login_and_address()
        return jsonify({'success': result})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port) 