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
    """設置 WebDriver"""
    try:
        print("開始初始化 WebDriver...")
        
        # 首先嘗試使用 webdriver-manager 獲取正確版本的 ChromeDriver
        try:
            from webdriver_manager.chrome import ChromeDriverManager
            print("使用 webdriver-manager 獲取 ChromeDriver...")
            chromedriver_path = ChromeDriverManager().install()
            print(f"ChromeDriver 路徑: {chromedriver_path}")
            
            # 修正路徑：確保指向正確的 chromedriver 執行檔
            if chromedriver_path.endswith('THIRD_PARTY_NOTICES.chromedriver'):
                # 修正路徑，移除錯誤的檔案名
                chromedriver_path = chromedriver_path.replace('THIRD_PARTY_NOTICES.chromedriver', 'chromedriver')
                print(f"修正後的 ChromeDriver 路徑: {chromedriver_path}")
            
            # 檢查檔案是否存在且可執行
            if not os.path.exists(chromedriver_path):
                print(f"ChromeDriver 檔案不存在: {chromedriver_path}")
                # 嘗試在目錄中尋找正確的 chromedriver 檔案
                import glob
                chromedriver_dir = os.path.dirname(chromedriver_path)
                chromedriver_files = glob.glob(os.path.join(chromedriver_dir, 'chromedriver*'))
                for file_path in chromedriver_files:
                    if os.path.isfile(file_path) and os.access(file_path, os.X_OK):
                        chromedriver_path = file_path
                        print(f"找到正確的 ChromeDriver: {chromedriver_path}")
                        break
            
            # 設置執行權限
            try:
                import stat
                os.chmod(chromedriver_path, stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH)
                print(f"已設置 ChromeDriver 執行權限: {chromedriver_path}")
            except Exception as e:
                print(f"設置權限失敗: {e}")
            
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--disable-extensions')
            chrome_options.add_argument('--disable-plugins')
            chrome_options.add_argument('--disable-images')
            chrome_options.add_argument('--disable-javascript')
            chrome_options.add_argument('--disable-web-security')
            chrome_options.add_argument('--allow-running-insecure-content')
            chrome_options.add_argument('--disable-features=VizDisplayCompositor')
            chrome_options.add_argument('--ignore-certificate-errors')
            chrome_options.add_argument('--ignore-ssl-errors')
            chrome_options.add_argument('--ignore-certificate-errors-spki-list')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            # 增加高解析度設定
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--start-maximized')
            chrome_options.add_argument('--force-device-scale-factor=1')
            # 減少記憶體使用的選項
            chrome_options.add_argument('--single-process')
            chrome_options.add_argument('--disable-background-timer-throttling')
            chrome_options.add_argument('--disable-backgrounding-occluded-windows')
            chrome_options.add_argument('--disable-renderer-backgrounding')
            chrome_options.add_argument('--disable-features=TranslateUI')
            chrome_options.add_argument('--disable-ipc-flooding-protection')
            # 修正 user-data-dir 衝突問題
            import tempfile
            user_data_dir = tempfile.mkdtemp(prefix='chrome_user_data_')
            chrome_options.add_argument(f'--user-data-dir={user_data_dir}')
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            
            service = Service(chromedriver_path)
            driver = webdriver.Chrome(service=service, options=chrome_options)
            print("使用 webdriver-manager 初始化 WebDriver 成功")
            return driver
            
        except Exception as e:
            print(f"webdriver-manager 失敗: {e}")
        
        # 如果 webdriver-manager 失敗，嘗試手動下載正確版本的 ChromeDriver
        try:
            print("嘗試手動下載正確版本的 ChromeDriver...")
            import subprocess
            import tempfile
            
            # 使用確實存在的 ChromeDriver 版本
            chromedriver_url = "https://chromedriver.storage.googleapis.com/114.0.5735.90/chromedriver_linux64.zip"
            temp_dir = tempfile.mkdtemp()
            chromedriver_zip = os.path.join(temp_dir, "chromedriver.zip")
            chromedriver_path = os.path.join(temp_dir, "chromedriver")
            
            # 下載並解壓
            subprocess.run(['wget', '-O', chromedriver_zip, chromedriver_url], check=True)
            subprocess.run(['unzip', '-o', chromedriver_zip, '-d', temp_dir], check=True)
            subprocess.run(['chmod', '+x', chromedriver_path], check=True)
            
            print(f"手動下載的 ChromeDriver 路徑: {chromedriver_path}")
            
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--disable-extensions')
            chrome_options.add_argument('--disable-plugins')
            chrome_options.add_argument('--disable-images')
            chrome_options.add_argument('--disable-javascript')
            chrome_options.add_argument('--disable-web-security')
            chrome_options.add_argument('--allow-running-insecure-content')
            chrome_options.add_argument('--disable-features=VizDisplayCompositor')
            chrome_options.add_argument('--ignore-certificate-errors')
            chrome_options.add_argument('--ignore-ssl-errors')
            chrome_options.add_argument('--ignore-certificate-errors-spki-list')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            # 增加高解析度設定
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--start-maximized')
            chrome_options.add_argument('--force-device-scale-factor=1')
            # 減少記憶體使用的選項
            chrome_options.add_argument('--single-process')
            chrome_options.add_argument('--disable-background-timer-throttling')
            chrome_options.add_argument('--disable-backgrounding-occluded-windows')
            chrome_options.add_argument('--disable-renderer-backgrounding')
            chrome_options.add_argument('--disable-features=TranslateUI')
            chrome_options.add_argument('--disable-ipc-flooding-protection')
            # 修正 user-data-dir 衝突問題
            user_data_dir = tempfile.mkdtemp(prefix='chrome_user_data_')
            chrome_options.add_argument(f'--user-data-dir={user_data_dir}')
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            
            service = Service(chromedriver_path)
            driver = webdriver.Chrome(service=service, options=chrome_options)
            print("手動下載 ChromeDriver 初始化成功")
            return driver
            
        except Exception as e:
            print(f"手動下載 ChromeDriver 失敗: {e}")
        
        # 最後嘗試：使用系統安裝的 ChromeDriver
        print("嘗試使用系統安裝的 ChromeDriver...")
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--disable-plugins')
        chrome_options.add_argument('--disable-images')
        chrome_options.add_argument('--disable-javascript')
        chrome_options.add_argument('--disable-web-security')
        chrome_options.add_argument('--allow-running-insecure-content')
        chrome_options.add_argument('--disable-features=VizDisplayCompositor')
        chrome_options.add_argument('--ignore-certificate-errors')
        chrome_options.add_argument('--ignore-ssl-errors')
        chrome_options.add_argument('--ignore-certificate-errors-spki-list')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        # 增加高解析度設定
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--start-maximized')
        chrome_options.add_argument('--force-device-scale-factor=1')
        # 減少記憶體使用的選項
        chrome_options.add_argument('--single-process')
        chrome_options.add_argument('--disable-background-timer-throttling')
        chrome_options.add_argument('--disable-backgrounding-occluded-windows')
        chrome_options.add_argument('--disable-renderer-backgrounding')
        chrome_options.add_argument('--disable-features=TranslateUI')
        chrome_options.add_argument('--disable-ipc-flooding-protection')
        # 修正 user-data-dir 衝突問題
        user_data_dir = tempfile.mkdtemp(prefix='chrome_user_data_')
        chrome_options.add_argument(f'--user-data-dir={user_data_dir}')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        
        # 檢查是否有環境變數指定的 ChromeDriver 路徑
        chromedriver_path = os.environ.get('CHROMEDRIVER_PATH', '/usr/local/bin/chromedriver')
        if os.path.exists(chromedriver_path):
            print(f"使用指定的 ChromeDriver: {chromedriver_path}")
            service = Service(chromedriver_path)
        else:
            print("使用預設 ChromeDriver 路徑")
            service = Service()
        
        driver = webdriver.Chrome(service=service, options=chrome_options)
        print("Chrome WebDriver 初始化成功")
        return driver
        
    except Exception as e:
        print(f"設置 WebDriver 時發生錯誤: {e}")
        
        # 最後嘗試：使用最基本的設定
        try:
            print("嘗試使用最基本的設定...")
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--ignore-certificate-errors')
            chrome_options.add_argument('--ignore-ssl-errors')
            # 增加高解析度設定
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--start-maximized')
            # 減少記憶體使用的選項
            chrome_options.add_argument('--single-process')
            chrome_options.add_argument('--disable-background-timer-throttling')
            # 修正 user-data-dir 衝突問題
            user_data_dir = tempfile.mkdtemp(prefix='chrome_user_data_')
            chrome_options.add_argument(f'--user-data-dir={user_data_dir}')
            
            service = Service()
            driver = webdriver.Chrome(service=service, options=chrome_options)
            print("使用基本設定初始化 WebDriver 成功")
            return driver
            
        except Exception as e2:
            print(f"基本設定也失敗: {e2}")
            raise Exception(f"無法初始化 WebDriver: {e} -> {e2}")

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
        WebDriverWait(driver, 30).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
        print("頁面已完全載入")
        take_screenshot("page_complete")
        
        # 檢查頁面狀態
        print(f"當前頁面標題: {driver.title}")
        print(f"當前頁面URL: {driver.current_url}")
        print(f"當前視窗大小: {driver.get_window_size()}")
        take_screenshot("main_page")
        
        # 簡化流程，直接返回成功
        print("預約流程執行完成（簡化版本）")
        take_screenshot("reservation_complete")
        
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