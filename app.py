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
            try:
                # 嘗試多種選擇器
                login_button = driver['page'].locator('button:has-text("民眾登入")').first
                if login_button.is_visible():
                    login_button.click()
                else:
                    # 備用方法：使用 JavaScript 點擊
                    driver['page'].evaluate('document.querySelector("button").click()')
            except Exception as e:
                print(f"點擊登入按鈕失敗，嘗試備用方法: {e}")
                # 嘗試點擊所有按鈕
                buttons = driver['page'].locator('button').all()
                for button in buttons:
                    if "民眾登入" in button.text_content():
                        button.click()
                        break
            
            print("登入按鈕點擊完成")
            take_screenshot("login_clicked")
            
            # 等待登入成功浮動視窗
            print("等待登入成功訊息...")
            try:
                # 嘗試多種可能的登入成功訊息選擇器
                success_selectors = [
                    'text=登入成功',
                    'text=登录成功', 
                    'text=Success',
                    'text=成功',
                    '.alert:has-text("登入")',
                    '.modal:has-text("登入")',
                    '.dialog:has-text("登入")',
                    '.message:has-text("登入")'
                ]
                
                success_found = False
                for selector in success_selectors:
                    try:
                        print(f"嘗試選擇器: {selector}")
                        driver['page'].wait_for_selector(selector, timeout=3000)
                        print(f"找到登入成功訊息: {selector}")
                        success_found = True
                        break
                    except Exception as e:
                        print(f"選擇器 {selector} 未找到: {e}")
                        continue
                
                if success_found:
                    # 尋找確定按鈕
                    confirm_selectors = [
                        'text=確定',
                        'text=OK',
                        'text=好的',
                        'text=知道了',
                        'button:has-text("確定")',
                        'button:has-text("OK")',
                        '.btn:has-text("確定")'
                    ]
                    
                    confirm_clicked = False
                    for confirm_selector in confirm_selectors:
                        try:
                            print(f"嘗試點擊確定按鈕: {confirm_selector}")
                            driver['page'].click(confirm_selector, timeout=3000)
                            print(f"確定按鈕點擊成功: {confirm_selector}")
                            confirm_clicked = True
                            break
                        except Exception as e:
                            print(f"確定按鈕 {confirm_selector} 點擊失敗: {e}")
                            continue
                    
                    if not confirm_clicked:
                        print("未找到確定按鈕，嘗試按 ESC 鍵")
                        driver['page'].keyboard.press('Escape')
                    
                    print("登入成功確認完成")
                    take_screenshot("login_success")
                else:
                    print("沒有找到登入成功訊息，可能已經登入成功")
                    take_screenshot("no_login_success_message")
                    
            except Exception as e:
                print(f"登入成功檢測過程發生錯誤: {e}")
                take_screenshot("login_success_error")
            
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
            print("輸入上車地點：亞東紀念醫院")
            pickup_input = driver['page'].locator('input[placeholder*="地點"]').first
            pickup_input.fill('亞東紀念醫院')
            driver['page'].wait_for_timeout(2000)  # 等待搜尋結果
            
            # 點擊第一個搜尋結果
            print("選擇第一個搜尋結果")
            search_results = driver['page'].locator('.search-result, .autocomplete-item').first
            if search_results.is_visible():
                search_results.click()
            take_screenshot("pickup_selected")
            
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