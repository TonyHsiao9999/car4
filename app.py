from flask import Flask, jsonify, send_file, send_from_directory
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
import time
import os
import base64
from datetime import datetime
from dotenv import load_dotenv
from selenium.webdriver.common.action_chains import ActionChains
import tempfile
from playwright.sync_api import sync_playwright
import subprocess

app = Flask(__name__, static_folder='static')

def take_screenshot(driver, name):
    """截圖功能"""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"/app/screenshots/{name}_{timestamp}.png"
        driver.save_screenshot(filename)
        print(f"截圖已保存: {filename}")
        
        # 將截圖轉換為 base64 以便在日誌中查看
        with open(filename, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode()
            print(f"截圖 base64: data:image/png;base64,{encoded_string[:100]}...")
            
    except Exception as e:
        print(f"截圖失敗: {e}")

def setup_driver():
    """設置 Selenium WebDriver"""
    try:
        print("正在初始化 Selenium WebDriver...")
        
        # 設置 Chrome 選項
        chrome_options = Options()
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--disable-web-security')
        chrome_options.add_argument('--disable-features=VizDisplayCompositor')
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--disable-plugins')
        chrome_options.add_argument('--disable-images')
        chrome_options.add_argument('--disable-javascript')
        chrome_options.add_argument('--disable-background-timer-throttling')
        chrome_options.add_argument('--disable-backgrounding-occluded-windows')
        chrome_options.add_argument('--disable-renderer-backgrounding')
        chrome_options.add_argument('--disable-features=TranslateUI')
        chrome_options.add_argument('--disable-ipc-flooding-protection')
        chrome_options.add_argument('--memory-pressure-off')
        chrome_options.add_argument('--max_old_space_size=4096')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        # 設置 ChromeDriver 路徑
        chrome_options.binary_location = '/usr/bin/chromium-browser'
        
        # 創建 WebDriver
        driver = webdriver.Chrome(options=chrome_options)
        driver.set_window_size(1920, 1080)
        
        print("Selenium WebDriver 初始化成功")
        return driver
        
    except Exception as e:
        print(f"Selenium WebDriver 初始化失敗: {e}")
        return None

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
    driver = None
    screenshot_count = 0
    
    def take_screenshot(description):
        nonlocal screenshot_count
        try:
            screenshot_count += 1
            filename = f'step_{screenshot_count:03d}_{description}.png'
            if driver:
                driver.save_screenshot(filename)
                print(f"截圖 {screenshot_count}: {description} - {filename}")
            return filename
        except Exception as e:
            print(f"截圖失敗: {e}")
            return None
    
    try:
        print("=== 開始執行預約流程 ===")
        print("開始初始化 WebDriver...")
        driver = setup_driver()
        print("WebDriver 初始化完成")
        
        # 設置視窗大小為高解析度
        print("設置視窗大小為 1920x1080...")
        driver.set_window_size(1920, 1080)
        driver.maximize_window()
        print("視窗大小設置完成")
        
        print("正在載入網頁...")
        driver.get("https://www.ntpc.ltc-car.org/")
        print("網頁載入完成")
        take_screenshot("page_loaded")
        
        # 等待頁面完全載入
        print("等待頁面完全載入...")
        driver.implicitly_wait(10)
        print("頁面已完全載入")
        take_screenshot("page_complete")
        
        # 處理浮動視窗 - 點擊「我知道了」按鈕
        print("檢查並處理浮動視窗...")
        try:
            # 等待浮動視窗出現
            driver.find_element(By.XPATH, "//button[text()='我知道了']")
            print("找到浮動視窗，點擊「我知道了」按鈕")
            driver.find_element(By.XPATH, "//button[text()='我知道了']").click()
            print("「我知道了」按鈕點擊成功")
            take_screenshot("popup_closed")
        except Exception as e:
            print(f"沒有找到浮動視窗或點擊失敗: {e}")
            take_screenshot("no_popup_found")
        
        # 登入步驟
        print("開始登入流程...")
        try:
            # 等待登入表單載入
            driver.find_element(By.XPATH, "//input[@type='text']")
            print("登入表單已載入")
            take_screenshot("login_form")
            
            # 輸入身分證字號
            print("輸入身分證字號: A102574899")
            driver.find_element(By.XPATH, "//input[@type='text']").send_keys("A102574899")
            
            # 輸入密碼
            print("輸入密碼: visi319VISI")
            driver.find_element(By.XPATH, "//input[@type='password']").send_keys("visi319VISI")
            
            # 點擊民眾登入按鈕 - 使用更精確的選擇器
            print("點擊民眾登入按鈕")
            try:
                # 嘗試多種選擇器
                login_button = driver.find_element(By.XPATH, "//button[contains(text(), '民眾登入')]")
                if login_button.is_displayed():
                    login_button.click()
                else:
                    # 備用方法：使用 JavaScript 點擊
                    driver.execute_script("document.querySelector('button').click()")
            except Exception as e:
                print(f"點擊登入按鈕失敗，嘗試備用方法: {e}")
                # 嘗試點擊所有按鈕
                buttons = driver.find_elements(By.XPATH, "//button")
                for button in buttons:
                    if "民眾登入" in button.text:
                        button.click()
                        break
            
            print("登入按鈕點擊完成")
            take_screenshot("login_clicked")
            
            # 等待登入成功浮動視窗
            print("等待登入成功訊息...")
            try:
                driver.find_element(By.XPATH, "//div[contains(text(), '登入成功')]")
                print("找到登入成功訊息，點擊確定")
                driver.find_element(By.XPATH, "//button[contains(text(), '確定')]").click()
                print("登入成功確認完成")
                take_screenshot("login_success")
            except Exception as e:
                print(f"沒有找到登入成功訊息: {e}")
                take_screenshot("no_login_success")
            
            # 等待登入完成
            print("等待登入完成...")
            driver.implicitly_wait(10)
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
            driver.find_element(By.XPATH, "//button[contains(text(), '新增預約')]").click()
            driver.implicitly_wait(10)
            take_screenshot("new_reservation")
            
            # 6. 上車地點選擇「醫療院所」
            print("選擇上車地點：醫療院所")
            select = Select(driver.find_element(By.XPATH, "//select[@name='location']"))
            select.select_by_visible_text("醫療院所")
            take_screenshot("pickup_location")
            
            # 7. 輸入「亞東紀念醫院」並選擇第一個搜尋結果
            print("輸入上車地點：亞東紀念醫院")
            pickup_input = driver.find_element(By.XPATH, "//input[@placeholder='請輸入地點']")
            pickup_input.send_keys("亞東紀念醫院")
            driver.implicitly_wait(2000)  # 等待搜尋結果
            
            # 點擊第一個搜尋結果
            print("選擇第一個搜尋結果")
            search_results = driver.find_elements(By.XPATH, "//div[@class='search-result']")
            if search_results:
                search_results[0].click()
            take_screenshot("pickup_selected")
            
            # 8. 下車地點選擇「住家」
            print("選擇下車地點：住家")
            select = Select(driver.find_element(By.XPATH, "//select[@name='location']"))
            select.select_by_visible_text("住家")
            take_screenshot("dropoff_location")
            
            # 9. 預約日期/時段選擇
            print("選擇預約日期/時段")
            # 選擇最後一個日期選項
            date_selects = driver.find_elements(By.XPATH, "//select[@name='date']/option")
            if len(date_selects) >= 3:
                # 選擇最後一個日期
                last_date_option = date_selects[-1]
                last_date_option.click()
                
                # 選擇時間 16
                time_selects = driver.find_elements(By.XPATH, "//select[@name='time']/option")
                if len(time_selects) >= 2:
                    time_selects[1].click()
                
                # 選擇分鐘 40
                if len(time_selects) >= 3:
                    time_selects[2].click()
            take_screenshot("datetime_selected")
            
            # 10. 於預約時間前後30分鐘到達 選擇「不同意」
            print("選擇不同意前後30分鐘到達")
            driver.find_element(By.XPATH, "//button[contains(text(), '不同意')]").click()
            take_screenshot("time_window")
            
            # 11. 陪同人數 選擇「1人(免費)」
            print("選擇陪同人數：1人(免費)")
            select = Select(driver.find_element(By.XPATH, "//select[@name='companion']"))
            select.select_by_visible_text("1人(免費)")
            take_screenshot("companion")
            
            # 12. 同意共乘 選擇「否」
            print("選擇不同意共乘")
            driver.find_element(By.XPATH, "//button[contains(text(), '否')]").click()
            take_screenshot("carpool")
            
            # 13. 搭乘輪椅上車 選擇「是」
            print("選擇搭乘輪椅上車：是")
            driver.find_element(By.XPATH, "//button[contains(text(), '是')]").click()
            take_screenshot("wheelchair")
            
            # 14. 大型輪椅 選擇「否」
            print("選擇大型輪椅：否")
            driver.find_element(By.XPATH, "//button[contains(text(), '否')]").click()
            take_screenshot("large_wheelchair")
            
            # 15. 點擊「下一步，確認預約資訊」
            print("點擊下一步，確認預約資訊")
            driver.find_element(By.XPATH, "//button[contains(text(), '下一步，確認預約資訊')]").click()
            driver.implicitly_wait(10)
            take_screenshot("confirm_info")
            
            # 16. 點擊「送出預約」
            print("點擊送出預約")
            driver.find_element(By.XPATH, "//button[contains(text(), '送出預約')]").click()
            driver.implicitly_wait(10)
            take_screenshot("submit_reservation")
            
            # 17. 檢查「已完成預約」畫面
            print("檢查預約完成狀態...")
            try:
                driver.find_element(By.XPATH, "//div[contains(text(), '已完成預約')]")
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
        import traceback
        print(f"預約過程中發生錯誤: {e}")
        print("詳細錯誤資訊:")
        print(traceback.format_exc())
        
        if driver:
            try:
                take_screenshot("error")
            except:
                pass
        
        return False
    finally:
        if driver:
            try:
                driver.quit()
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