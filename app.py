from flask import Flask, request, jsonify, send_from_directory, render_template_string, send_file
from playwright.sync_api import sync_playwright
import time
import os
import base64
import re
from datetime import datetime
import pytz

app = Flask(__name__)

def take_screenshot(driver, name):
    """截圖功能"""
    try:
        taipei_tz = pytz.timezone('Asia/Taipei')
        timestamp = datetime.now(taipei_tz).strftime("%Y%m%d_%H%M%S")
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
        
        # 設定台北時區的上下文
        context = browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            timezone_id='Asia/Taipei',  # 設定台北時區
            locale='zh-TW'  # 設定繁體中文
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
        
        print("Playwright 初始化成功 (已設定台北時區)")
        return driver
        
    except Exception as e:
        print(f"Playwright 初始化失敗: {e}")
        return None

def fetch_dispatch_results():
    driver = None
    screenshot_count = 0
    
    def take_screenshot(description):
        nonlocal screenshot_count
        try:
            screenshot_count += 1
            filename = f'dispatch_{screenshot_count:03d}_{description}.png'
            if driver:
                driver['page'].screenshot(path=filename)
                print(f"派車截圖 {screenshot_count}: {description} - {filename}")
            return filename
        except Exception as e:
            print(f"派車截圖失敗: {e}")
            return None
    
    try:
        print("=== 開始執行派車結果抓取流程 ===")
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
        
        # 登入步驟（與預約功能相同的登入邏輯）
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
            
            # 點擊民眾登入按鈕
            print("點擊民眾登入按鈕")
            take_screenshot("before_login_click")
            
            login_selectors = [
                'a:has-text("民眾登入")',
                'button:has-text("民眾登入")',
                'text=民眾登入',
                '*:has-text("民眾登入")',
            ]
            
            login_clicked = False
            for selector in login_selectors:
                try:
                    print(f"嘗試登入按鈕選擇器: {selector}")
                    element = driver['page'].locator(selector).first
                    if element.count() > 0 and element.is_visible():
                        print(f"找到元素: {selector}")
                        element.click()
                        print(f"登入按鈕點擊成功: {selector}")
                        login_clicked = True
                        break
                except Exception as e:
                    print(f"登入按鈕選擇器 {selector} 失敗: {e}")
                    continue
            
            if login_clicked:
                print("登入按鈕點擊完成")
                take_screenshot("login_clicked")
            else:
                print("警告：無法找到或點擊登入按鈕")
                take_screenshot("login_click_failed")
            
            # 等待登入成功浮動視窗
            print("等待登入成功訊息...")
            try:
                driver['page'].wait_for_selector('text=登入成功', timeout=5000)
                take_screenshot("login_success_modal_found")
                
                # 點擊確定按鈕
                try:
                    print("🎯 使用精確的確定按鈕選擇器...")
                    precise_selector = 'span.dialog-button'
                    element = driver['page'].locator(precise_selector).first
                    if element.count() > 0 and element.is_visible():
                        print(f"找到精確的確定按鈕: {precise_selector}")
                        element.click()
                        driver['page'].wait_for_timeout(1000)
                        print("✅ 確定按鈕點擊成功")
                except Exception as e:
                    print(f"❌ 確定按鈕點擊失敗: {e}")
                
                take_screenshot("login_success_confirmed")
            except Exception as e:
                print(f"沒有找到登入成功浮動視窗: {e}")
                take_screenshot("no_login_success_modal")
            
            # 等待登入完成
            print("等待登入完成...")
            driver['page'].wait_for_load_state("networkidle")
            print("登入流程完成")
            take_screenshot("login_complete")
            
        except Exception as e:
            print(f"登入過程發生錯誤: {e}")
            take_screenshot("login_error")
            return False
        
        # 從這裡開始改為點擊「訂單查詢」
        print("=== 開始訂單查詢流程 ===")
        try:
            # 點擊「訂單查詢」- 使用精確的 CSS 選擇器
            print("點擊訂單查詢...")
            
            # 等待頁面穩定
            print("等待頁面穩定...")
            driver['page'].wait_for_load_state("networkidle")
            driver['page'].wait_for_timeout(2000)
            
            # 🎯 基於原始碼分析的訂單查詢按鈕選擇器
            # 這是一個單頁面應用程式，需要等待 JavaScript 動態載入內容
            print("等待 JavaScript 內容載入...")
            driver['page'].wait_for_timeout(3000)  # 等待 SPA 載入
            
            order_selectors = [
                # 基於 SPA 結構的選擇器
                '.page:nth-child(2) li:nth-child(2) h2:nth-child(1)',  # 原始精確選擇器
                '.page:nth-child(2) li:nth-child(2)',  # 簡化版本
                '.page li:nth-child(2)',  # 更簡化
                
                # 文字內容匹配
                'li:has-text("訂單查詢")',  # Playwright文字選擇器
                'h2:has-text("訂單查詢")',  # h2標籤文字選擇器
                'a:has-text("訂單查詢")',   # 連結文字選擇器
                '*:has-text("訂單查詢")',   # 通用文字選擇器
                
                # 導航相關選擇器
                'nav li:nth-child(2)',      # 導航第二項
                '.nav li:nth-child(2)',     # 導航類別第二項
                '.menu li:nth-child(2)',    # 選單第二項
                
                # 更寬泛的匹配
                'li:contains("訂單")',      # 包含"訂單"的列表項
                'li:contains("查詢")',      # 包含"查詢"的列表項
                '*:contains("訂單查詢")'    # 包含完整文字的任何元素
            ]
            
            order_clicked = False
            
            for selector in order_selectors:
                try:
                    print(f"嘗試訂單查詢選擇器: {selector}")
                    
                    # 檢查元素是否存在
                    elements = driver['page'].query_selector_all(selector)
                    print(f"找到 {len(elements)} 個元素使用選擇器: {selector}")
                    
                    if elements:
                        for i, element in enumerate(elements):
                            try:
                                if element.is_visible():
                                    element_text = element.inner_text().strip()
                                    print(f"元素 {i+1} 文字: '{element_text}'")
                                    
                                    # 檢查是否包含"訂單查詢"文字
                                    if "訂單查詢" in element_text:
                                        print(f"✅ 找到訂單查詢元素: {selector}")
                                        element.click()
                                        print(f"🎯 訂單查詢點擊成功")
                                        
                                        # 🔍 關鍵改進：等待頁面導航並驗證URL
                                        print("等待頁面導航...")
                                        driver['page'].wait_for_load_state("networkidle", timeout=10000)
                                        driver['page'].wait_for_timeout(3000)
                                        
                                        # 檢查當前URL是否為訂單查詢頁面
                                        current_url = driver['page'].url
                                        print(f"當前URL: {current_url}")
                                        
                                        if "ReservationOrder" in current_url:
                                            print("✅ 成功導航到訂單查詢頁面!")
                                            order_clicked = True
                                            break
                                        else:
                                            print(f"❌ URL不正確，預期包含 'ReservationOrder'，實際: {current_url}")
                                            print("繼續嘗試其他選擇器...")
                                            continue
                                            
                            except Exception as click_error:
                                print(f"點擊元素 {i+1} 失敗: {click_error}")
                                continue
                                
                    if order_clicked:
                        break
                        
                except Exception as e:
                    print(f"選擇器 {selector} 失敗: {e}")
                    continue
            
            if not order_clicked:
                print("❌ 無法找到訂單查詢按鈕，嘗試直接導航到訂單查詢頁面...")
                take_screenshot("order_query_not_found")
                
                # 🎯 直接導航到訂單查詢頁面作為備用方案
                try:
                    print("🔄 直接導航到 ReservationOrder 頁面...")
                    driver['page'].goto("https://www.ntpc.ltc-car.org/ReservationOrder/")
                    driver['page'].wait_for_load_state("networkidle", timeout=15000)
                    driver['page'].wait_for_timeout(3000)
                    
                    # 驗證導航是否成功
                    current_url = driver['page'].url
                    print(f"直接導航後的URL: {current_url}")
                    
                    if "ReservationOrder" in current_url:
                        print("✅ 直接導航成功！")
                        order_clicked = True
                        take_screenshot("direct_navigation_success")
                    else:
                        print(f"❌ 直接導航也失敗，URL: {current_url}")
                        take_screenshot("direct_navigation_failed")
                        return False
                        
                except Exception as nav_error:
                    print(f"❌ 直接導航失敗: {nav_error}")
                    take_screenshot("direct_navigation_error")
                    return False
            
            # 🔍 強化驗證：確保在正確的訂單查詢頁面
            print("驗證是否成功到達訂單查詢頁面...")
            try:
                # 再次確認URL
                final_url = driver['page'].url
                print(f"最終URL: {final_url}")
                
                if "ReservationOrder" not in final_url:
                    print(f"❌ 最終URL不正確: {final_url}")
                    take_screenshot("wrong_final_url")
                    return False
                
                # 等待頁面特定元素載入，確認這是訂單查詢頁面
                order_page_indicators = [
                    '.order_list',              # 訂單列表容器
                    'text=預約記錄',
                    'text=訂單記錄', 
                    'text=預約列表',
                    '.reservation-list',
                    '.record-list',
                    'table',
                    '.order-item',
                    '.date',                    # 日期元素
                    '.see_more'                 # 展開按鈕
                ]
                
                page_verified = False
                for indicator in order_page_indicators:
                    try:
                        driver['page'].wait_for_selector(indicator, timeout=5000)
                        print(f"✅ 訂單頁面確認: 找到 {indicator}")
                        page_verified = True
                        break
                    except:
                        continue
                
                if not page_verified:
                    print("⚠️ 無法確認訂單查詢頁面元素，但URL正確，繼續執行...")
                    take_screenshot("page_elements_uncertain")
                else:
                    print("✅ 訂單查詢頁面載入確認")
                    
            except Exception as e:
                print(f"頁面驗證失敗: {e}")
            
            # 等待訂單列表完全載入
            print("等待訂單列表完全載入...")
            driver['page'].wait_for_load_state("networkidle")
            driver['page'].wait_for_timeout(5000)  # 增加等待時間確保SPA內容載入
            take_screenshot("order_list_loaded")
            
            # 🎯 使用台北時區的當日日期 (修正格式為 2025/06/19)
            taipei_tz = pytz.timezone('Asia/Taipei')
            today = datetime.now(taipei_tz)
            target_date = today.strftime("%Y/%m/%d")  # 格式：2025/06/19
            utc_time = datetime.utcnow()
            print(f"🌏 UTC時間: {utc_time.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"🇹🇼 台北時間: {today.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"🔍 尋找預約日期為 {target_date} 的訂單 (台北時區)...")
            
            # 分析訂單記錄
            print("開始分析訂單記錄...")
            
            # 🎯 使用新的 CSS 選擇器尋找預約記錄（支援分頁和捲動）
            print("使用新的 CSS 選擇器尋找預約記錄...")
            
            # 清空結果檔案
            result_file = "search_result.txt"
            with open(result_file, 'w', encoding='utf-8') as f:
                f.write("")  # 清空檔案
            
            results = []
            total_records_checked = 0
            total_dispatch_records_found = 0  # 新增：統計已派車記錄總數
            
            print("🔍 系統分析：檢測到 Vue.js SPA 架構")
            print("💡 新策略：透過網路請求監聽和智慧等待獲取所有資料")
            
            # 🌐 設置網路請求監聽
            captured_api_data = []
            
            def handle_response(response):
                if 'Order' in response.url and response.status == 200:
                    try:
                        data = response.json()
                        captured_api_data.append(data)
                        print(f"📡 捕獲API回應: {response.url}")
                    except:
                        pass
            
            driver['page'].on('response', handle_response)
            
            # 🎯 簡化處理：直接獲取所有記錄（移除分頁邏輯）
            print("🎯 簡化處理：直接獲取所有記錄...")
            
            # 等待記錄載入並獲取所有 order_list 元素
            driver['page'].wait_for_selector('.order_list', timeout=10000)
            all_order_elements = driver['page'].query_selector_all('.order_list')
            total_elements_on_page = len(all_order_elements)
            print(f"📊 當前載入的記錄總數: {total_elements_on_page} 個")
            
            # 🔧 改進的記錄檢測邏輯：直接使用元素而非索引
            dispatch_records = []
            for i, element in enumerate(all_order_elements, 1):
                try:
                    is_visible = element.is_visible()
                    class_list = element.get_attribute('class') or ''
                    
                    # 🎯 檢查各種訂單狀態
                    is_cancelled = 'cancel' in class_list.lower()
                    is_accept = 'accept' in class_list.lower()
                    is_established = 'established' in class_list.lower()
                    is_dispatch = 'dispatch' in class_list.lower()  # 🎯 這是我們要的狀態
                    is_implement = 'implement' in class_list.lower()
                    is_finish = 'finish' in class_list.lower()
                    is_recently = 'recently' in class_list.lower()  # 新增：最近記錄
                    
                    print(f"🔍 檢查元素 {i}: 可見={is_visible}")
                    print(f"   📋 狀態分析: class='{class_list}'")
                    print(f"   🏷️ 狀態標籤: 取消={is_cancelled}, 接受={is_accept}, 確立={is_established}")
                    print(f"   🎯 派車={is_dispatch}, 執行={is_implement}, 完成={is_finish}")
                    print(f"   📅 最近={is_recently}")
                    
                    # 🎯 改進的記錄篩選邏輯
                    if is_visible:
                        if is_dispatch:
                            # 明確的已派車狀態
                            dispatch_records.append({'index': i, 'element': element})
                            total_dispatch_records_found += 1
                            print(f"✅ 元素 {i} 是已派車記錄 - 這是我們要的！")
                        elif is_recently and not is_cancelled:
                            # 最近記錄且未取消，可能是已派車但狀態未更新
                            print(f"🔍 元素 {i} 是最近記錄，需要進一步檢查...")
                            
                            # 嘗試在該元素內尋找派車相關資訊
                            try:
                                # 檢查是否有車號或司機資訊
                                car_selectors = [
                                    '.car_number',
                                    '.driver_name', 
                                    '.vehicle_info',
                                    '.dispatch_info'
                                ]
                                
                                has_dispatch_info = False
                                for car_sel in car_selectors:
                                    car_element = element.query_selector(car_sel)
                                    if car_element and car_element.is_visible():
                                        car_text = car_element.inner_text().strip()
                                        if car_text and len(car_text) > 0:
                                            print(f"   🚗 找到派車資訊: {car_text}")
                                            has_dispatch_info = True
                                            break
                                
                                if has_dispatch_info:
                                    dispatch_records.append({'index': i, 'element': element})
                                    total_dispatch_records_found += 1
                                    print(f"✅ 元素 {i} 是最近記錄但包含派車資訊 - 加入處理！")
                                else:
                                    print(f"❌ 元素 {i} 是最近記錄但沒有派車資訊，跳過")
                            except Exception as e:
                                print(f"⚠️ 檢查元素 {i} 派車資訊時發生錯誤: {e}")
                                # 如果檢查失敗，保守起見還是加入處理
                                dispatch_records.append({'index': i, 'element': element})
                                total_dispatch_records_found += 1
                                print(f"✅ 元素 {i} 檢查失敗，保守加入處理")
                        elif is_cancelled:
                            print(f"❌ 元素 {i} 是已取消記錄，跳過")
                        elif is_accept:
                            print(f"❌ 元素 {i} 是已接受記錄（尚未派車），跳過")
                        elif is_established:
                            print(f"❌ 元素 {i} 是已確立記錄（尚未派車），跳過")
                        elif is_implement:
                            print(f"❌ 元素 {i} 是執行中記錄（已過派車階段），跳過")
                        elif is_finish:
                            print(f"❌ 元素 {i} 是已完成記錄（已過派車階段），跳過")
                        else:
                            print(f"❌ 元素 {i} 是其他狀態記錄，跳過")
                    else:
                        print(f"❌ 元素 {i} 不可見，跳過")
                except Exception as e:
                    print(f"⚠️ 檢查元素 {i} 時發生錯誤: {e}")
                    continue
            
            print(f"🎯 找到已派車記錄: {[r['index'] for r in dispatch_records]}")
            print(f"📊 累計已派車記錄總數: {total_dispatch_records_found}")
            
            # 🎯 直接使用元素處理已派車狀態的記錄（移除日期篩選）
            for record_info in dispatch_records:
                record_index = record_info['index']
                order_element = record_info['element']
                try:
                    # 🔧 直接從已派車元素中找日期元素
                    print(f"🔍 處理第 {record_index} 筆已派車記錄...")
                    
                    # 在該元素內找日期元素
                    date_selectors = [
                        '.order_blocks.date .text',
                        '.date .text',
                        '.order_blocks .text'
                    ]
                    
                    date_element = None
                    for date_sel in date_selectors:
                        try:
                            date_element = order_element.query_selector(date_sel)
                            if date_element and date_element.is_visible():
                                print(f"✅ 使用選擇器 '{date_sel}' 找到日期元素")
                                break
                        except:
                            continue
                    
                    if not date_element:
                        print(f"❌ 在第 {record_index} 筆記錄中找不到日期元素")
                        continue
                    
                    # 🎯 記錄已經在前面過濾為已派車狀態，這裡直接處理（不檢查日期）
                    print(f"🚗 處理已派車記錄 {record_index}")
                    
                    # 取得日期文字
                    date_text = date_element.inner_text().strip()
                    total_records_checked += 1
                    print(f"📅 第 {record_index} 筆記錄日期: {date_text}")
                    
                    # 🎯 移除日期篩選，直接處理所有已派車記錄
                    print(f"✅ 找到已派車記錄 {record_index}，直接處理（不檢查日期）")
                    
                    # 捲動到記錄位置
                    date_element.scroll_into_view_if_needed()
                    driver['page'].wait_for_timeout(1000)
                    take_screenshot(f"record_{record_index}_found")
                    
                    # 🔧 在該元素內找展開按鈕
                    expand_selectors = [
                        '.see_more span',
                        '.see_more',
                        '.see_more i'
                    ]
                    
                    expand_button = None
                    for expand_sel in expand_selectors:
                        try:
                            expand_button = order_element.query_selector(expand_sel)
                            if expand_button and expand_button.is_visible():
                                print(f"✅ 使用選擇器 '{expand_sel}' 找到展開按鈕")
                                break
                        except:
                            continue
                    
                    if expand_button and expand_button.is_visible():
                        print(f"✅ 找到展開按鈕，準備點擊...")
                        expand_button.scroll_into_view_if_needed()
                        driver['page'].wait_for_timeout(500)
                        expand_button.click()
                        print(f"✅ 展開按鈕點擊成功")
                        
                        # 等待展開內容載入
                        driver['page'].wait_for_timeout(3000)
                        take_screenshot(f"record_{record_index}_expanded")
                        
                        # 🔧 直接在該元素內提取資訊
                        try:
                            # 車號選擇器 - 在該元素內搜尋
                            car_selectors = [
                                '.order_blocks.style2 .blocks > div:nth-child(2)',
                                '.style2 > .blocks > div:nth-child(2)',
                                '.blocks > div:nth-child(2)'
                            ]
                            
                            car_number = "未找到"
                            for car_selector in car_selectors:
                                try:
                                    car_element = order_element.query_selector(car_selector)
                                    if car_element and car_element.is_visible():
                                        car_number = car_element.inner_text().strip()
                                        print(f"🚗 車號選擇器成功: {car_selector}")
                                        break
                                except:
                                    continue
                            print(f"🚗 車號: {car_number}")
                            
                            # 指派司機選擇器 - 在該元素內搜尋
                            driver_selectors = [
                                '.order_blocks .blocks > div:nth-child(1)',
                                '.blocks > div:nth-child(1)'
                            ]
                            
                            driver_name = "未找到"
                            for driver_selector in driver_selectors:
                                try:
                                    driver_element = order_element.query_selector(driver_selector)
                                    if driver_element and driver_element.is_visible():
                                        driver_name = driver_element.inner_text().strip()
                                        print(f"👨‍✈️ 司機選擇器成功: {driver_selector}")
                                        break
                                except:
                                    continue
                            print(f"👨‍✈️ 指派司機: {driver_name}")
                            
                            # 負擔金額選擇器 - 使用精確的 CSS 選擇器（基於用戶提供的資訊）
                            amount_selectors = [
                                '.order_blocks:nth-child(6) > .blocks',  # 用戶提供的精確選擇器
                                '.order_blocks:nth-child(6) .blocks',    # 備用（不限制直接子元素）
                                '.order_blocks:nth-child(6) .text',      # 第6個區塊的文字內容
                                '.order_blocks:nth-child(5) .blocks:nth-child(2)',  # 原始選擇器
                                '*:contains("負擔金額")',  # 直接搜尋包含「負擔金額」的元素
                                '.order_blocks .blocks:contains("負擔金額")',
                                '.blocks .text:contains("負擔金額")',
                                '.order_blocks:contains("負擔金額")',  # 搜尋更大範圍
                                '.order_blocks .blocks:contains("元")',  # 備用方案
                                '.blocks .text:contains("元")',
                                '.text:contains("元")'
                            ]
                            
                            self_pay_amount = "未找到"
                            print(f"💰 開始搜尋負擔金額，共 {len(amount_selectors)} 個選擇器")
                            
                            for i, amount_selector in enumerate(amount_selectors, 1):
                                try:
                                    print(f"💰 嘗試選擇器 {i}/{len(amount_selectors)}: {amount_selector}")
                                    if ':contains(' in amount_selector:
                                        # 針對 :contains 選擇器的特殊處理
                                        # 先找到所有可能的元素，然後檢查文字內容
                                        base_selector = amount_selector.split(':contains(')[0]
            # 🔄 智慧資料收集迴圈（最多嘗試10次分頁）
            max_attempts = 10
            current_attempt = 1
            
            while current_attempt <= max_attempts:
                print(f"\n=== 嘗試 {current_attempt}/{max_attempts} ===")
                
                # 等待當前頁面載入完成
                driver['page'].wait_for_load_state("networkidle")
                driver['page'].wait_for_timeout(3000)
                
                # 🔝 強制捲動到頁面最頂部
                print("強制捲動到頁面最頂部...")
                driver['page'].evaluate("window.scrollTo(0, 0)")
                driver['page'].wait_for_timeout(2000)  # 增加等待時間確保捲動完成
                
                # 再次確保在最頂部
                driver['page'].evaluate("document.documentElement.scrollTop = 0")
                driver['page'].evaluate("document.body.scrollTop = 0")
                driver['page'].wait_for_timeout(1000)
                
                take_screenshot(f"attempt_{current_attempt}_start_top")
                
                # 📋 搜尋當前可見的所有記錄
                current_attempt_results = 0
                
                # 🎯 SPA 特化的記錄檢測邏輯
                print("📋 SPA記錄檢測：等待並收集所有可見的已派車記錄...")
                
                # 🎯 簡化處理：直接獲取所有記錄（移除分頁邏輯）
                print("🎯 簡化處理：直接獲取所有記錄...")
                
                # 等待記錄載入並獲取所有 order_list 元素
                driver['page'].wait_for_selector('.order_list', timeout=10000)
                all_order_elements = driver['page'].query_selector_all('.order_list')
                total_elements_on_page = len(all_order_elements)
                print(f"📊 當前載入的記錄總數: {total_elements_on_page} 個")
                
                # 🔧 改進的記錄檢測邏輯：直接使用元素而非索引
                dispatch_records = []
                for i, element in enumerate(all_order_elements, 1):
                    try:
                        is_visible = element.is_visible()
                        class_list = element.get_attribute('class') or ''
                        
                        # 🎯 檢查各種訂單狀態
                        is_cancelled = 'cancel' in class_list.lower()
                        is_accept = 'accept' in class_list.lower()
                        is_established = 'established' in class_list.lower()
                        is_dispatch = 'dispatch' in class_list.lower()  # 🎯 這是我們要的狀態
                        is_implement = 'implement' in class_list.lower()
                        is_finish = 'finish' in class_list.lower()
                        is_recently = 'recently' in class_list.lower()  # 新增：最近記錄
                        
                        print(f"🔍 檢查元素 {i}: 可見={is_visible}")
                        print(f"   📋 狀態分析: class='{class_list}'")
                        print(f"   🏷️ 狀態標籤: 取消={is_cancelled}, 接受={is_accept}, 確立={is_established}")
                        print(f"   🎯 派車={is_dispatch}, 執行={is_implement}, 完成={is_finish}")
                        print(f"   📅 最近={is_recently}")
                        
                        # 🎯 改進的記錄篩選邏輯
                        if is_visible:
                            if is_dispatch:
                                # 明確的已派車狀態
                                dispatch_records.append({'index': i, 'element': element})
                                total_dispatch_records_found += 1
                                print(f"✅ 元素 {i} 是已派車記錄 - 這是我們要的！")
                            elif is_recently and not is_cancelled:
                                # 最近記錄且未取消，可能是已派車但狀態未更新
                                print(f"🔍 元素 {i} 是最近記錄，需要進一步檢查...")
                                
                                # 嘗試在該元素內尋找派車相關資訊
                                try:
                                    # 檢查是否有車號或司機資訊
                                    car_selectors = [
                                        '.car_number',
                                        '.driver_name', 
                                        '.vehicle_info',
                                        '.dispatch_info'
                                    ]
                                    
                                    has_dispatch_info = False
                                    for car_sel in car_selectors:
                                        car_element = element.query_selector(car_sel)
                                        if car_element and car_element.is_visible():
                                            car_text = car_element.inner_text().strip()
                                            if car_text and len(car_text) > 0:
                                                print(f"   🚗 找到派車資訊: {car_text}")
                                                has_dispatch_info = True
                                                break
                                    
                                    if has_dispatch_info:
                                        dispatch_records.append({'index': i, 'element': element})
                                        total_dispatch_records_found += 1
                                        print(f"✅ 元素 {i} 是最近記錄但包含派車資訊 - 加入處理！")
                                    else:
                                        print(f"❌ 元素 {i} 是最近記錄但沒有派車資訊，跳過")
                                except Exception as e:
                                    print(f"⚠️ 檢查元素 {i} 派車資訊時發生錯誤: {e}")
                                    # 如果檢查失敗，保守起見還是加入處理
                                    dispatch_records.append({'index': i, 'element': element})
                                    total_dispatch_records_found += 1
                                    print(f"✅ 元素 {i} 檢查失敗，保守加入處理")
                            elif is_cancelled:
                                print(f"❌ 元素 {i} 是已取消記錄，跳過")
                            elif is_accept:
                                print(f"❌ 元素 {i} 是已接受記錄（尚未派車），跳過")
                            elif is_established:
                                print(f"❌ 元素 {i} 是已確立記錄（尚未派車），跳過")
                            elif is_implement:
                                print(f"❌ 元素 {i} 是執行中記錄（已過派車階段），跳過")
                            elif is_finish:
                                print(f"❌ 元素 {i} 是已完成記錄（已過派車階段），跳過")
                            else:
                                print(f"❌ 元素 {i} 是其他狀態記錄，跳過")
                        else:
                            print(f"❌ 元素 {i} 不可見，跳過")
                    except Exception as e:
                        print(f"⚠️ 檢查元素 {i} 時發生錯誤: {e}")
                        continue
                
                print(f"🎯 找到已派車記錄: {[r['index'] for r in dispatch_records]}")
                print(f"📊 累計已派車記錄總數: {total_dispatch_records_found}")
                
                # 🎯 直接使用元素處理已派車狀態的記錄（移除日期篩選）
                for record_info in dispatch_records:
                    record_index = record_info['index']
                    order_element = record_info['element']
                    try:
                        # 🔧 直接從已派車元素中找日期元素
                        print(f"🔍 處理第 {record_index} 筆已派車記錄...")
                        
                        # 在該元素內找日期元素
                        date_selectors = [
                            '.order_blocks.date .text',
                            '.date .text',
                            '.order_blocks .text'
                        ]
                        
                        date_element = None
                        for date_sel in date_selectors:
                            try:
                                date_element = order_element.query_selector(date_sel)
                                if date_element and date_element.is_visible():
                                    print(f"✅ 使用選擇器 '{date_sel}' 找到日期元素")
                                    break
                            except:
                                continue
                        
                        if not date_element:
                            print(f"❌ 在第 {record_index} 筆記錄中找不到日期元素")
                            continue
                        
                        # 🎯 記錄已經在前面過濾為已派車狀態，這裡直接處理（不檢查日期）
                        print(f"🚗 處理已派車記錄 {record_index}")
                        
                        # 取得日期文字
                        date_text = date_element.inner_text().strip()
                        total_records_checked += 1
                        print(f"📅 第 {record_index} 筆記錄日期: {date_text}")
                        
                        # 🎯 移除日期篩選，直接處理所有已派車記錄
                        print(f"✅ 找到已派車記錄 {record_index}，直接處理（不檢查日期）")
                        current_attempt_results += 1
                        
                        # 捲動到記錄位置
                        date_element.scroll_into_view_if_needed()
                        driver['page'].wait_for_timeout(1000)
                        take_screenshot(f"attempt_{current_attempt}_record_{record_index}_found")
                        
                        # 🔧 在該元素內找展開按鈕
                        expand_selectors = [
                            '.see_more span',
                            '.see_more',
                            '.see_more i'
                        ]
                        
                        expand_button = None
                        for expand_sel in expand_selectors:
                            try:
                                expand_button = order_element.query_selector(expand_sel)
                                if expand_button and expand_button.is_visible():
                                    print(f"✅ 使用選擇器 '{expand_sel}' 找到展開按鈕")
                                    break
                            except:
                                continue
                        
                        if expand_button and expand_button.is_visible():
                            print(f"✅ 找到展開按鈕，準備點擊...")
                            expand_button.scroll_into_view_if_needed()
                            driver['page'].wait_for_timeout(500)
                            expand_button.click()
                            print(f"✅ 展開按鈕點擊成功")
                            
                            # 等待展開內容載入
                            driver['page'].wait_for_timeout(3000)
                            take_screenshot(f"attempt_{current_attempt}_record_{record_index}_expanded")
                            
                            # 🔧 直接在該元素內提取資訊
                            try:
                                # 車號選擇器 - 在該元素內搜尋
                                car_selectors = [
                                    '.order_blocks.style2 .blocks > div:nth-child(2)',
                                    '.style2 > .blocks > div:nth-child(2)',
                                    '.blocks > div:nth-child(2)'
                                ]
                                
                                car_number = "未找到"
                                for car_selector in car_selectors:
                                    try:
                                        car_element = order_element.query_selector(car_selector)
                                        if car_element and car_element.is_visible():
                                            car_number = car_element.inner_text().strip()
                                            print(f"🚗 車號選擇器成功: {car_selector}")
                                            break
                                    except:
                                        continue
                                print(f"🚗 車號: {car_number}")
                                
                                # 指派司機選擇器 - 在該元素內搜尋
                                driver_selectors = [
                                    '.order_blocks .blocks > div:nth-child(1)',
                                    '.blocks > div:nth-child(1)'
                                ]
                                
                                driver_name = "未找到"
                                for driver_selector in driver_selectors:
                                    try:
                                        driver_element = order_element.query_selector(driver_selector)
                                        if driver_element and driver_element.is_visible():
                                            driver_name = driver_element.inner_text().strip()
                                            print(f"👨‍✈️ 司機選擇器成功: {driver_selector}")
                                            break
                                    except:
                                        continue
                                print(f"👨‍✈️ 指派司機: {driver_name}")
                                
                                # 負擔金額選擇器 - 使用精確的 CSS 選擇器（基於用戶提供的資訊）
                                amount_selectors = [
                                    '.order_blocks:nth-child(6) > .blocks',  # 用戶提供的精確選擇器
                                    '.order_blocks:nth-child(6) .blocks',    # 備用（不限制直接子元素）
                                    '.order_blocks:nth-child(6) .text',      # 第6個區塊的文字內容
                                    '.order_blocks:nth-child(5) .blocks:nth-child(2)',  # 原始選擇器
                                    '*:contains("負擔金額")',  # 直接搜尋包含「負擔金額」的元素
                                    '.order_blocks .blocks:contains("負擔金額")',
                                    '.blocks .text:contains("負擔金額")',
                                    '.order_blocks:contains("負擔金額")',  # 搜尋更大範圍
                                    '.order_blocks .blocks:contains("元")',  # 備用方案
                                    '.blocks .text:contains("元")',
                                    '.text:contains("元")'
                                ]
                                
                                self_pay_amount = "未找到"
                                print(f"💰 開始搜尋負擔金額，共 {len(amount_selectors)} 個選擇器")
                                
                                for i, amount_selector in enumerate(amount_selectors, 1):
                                    try:
                                        print(f"💰 嘗試選擇器 {i}/{len(amount_selectors)}: {amount_selector}")
                                        if ':contains(' in amount_selector:
                                            # 針對 :contains 選擇器的特殊處理
                                            # 先找到所有可能的元素，然後檢查文字內容
                                            base_selector = amount_selector.split(':contains(')[0]
                                            search_text = amount_selector.split(':contains(')[1].rstrip(')').strip('"\'')
                                            
                                            if base_selector == '*':
                                                # 搜尋所有元素
                                                possible_elements = order_element.query_selector_all('*')
                                            else:
                                                # 搜尋特定類型的元素
                                                possible_elements = order_element.query_selector_all(base_selector)
                                            
                                            for element in possible_elements:
                                                if element.is_visible():
                                                    element_text = element.inner_text().strip()
                                                    if search_text in element_text:
                                                        # 找到包含「負擔金額」的元素
                                                        if '負擔金額' in search_text:
                                                            # 嘗試從該元素或其父/子元素中提取金額
                                                            # 檢查該元素的文字
                                                            amount_match = re.search(r'(\d+)\s*元', element_text)
                                                            if amount_match:
                                                                self_pay_amount = amount_match.group(0)
                                                                print(f"💰 在「負擔金額」元素中找到金額: {self_pay_amount}")
                                                                break
                                                            
                                                            # 檢查父元素
                                                            parent = element.locator('..')
                                                            if parent:
                                                                parent_text = parent.inner_text()
                                                                amount_match = re.search(r'(\d+)\s*元', parent_text)
                                                                if amount_match:
                                                                    self_pay_amount = amount_match.group(0)
                                                                    print(f"💰 在「負擔金額」父元素中找到金額: {self_pay_amount}")
                                                                    break
                                                            
                                                            # 檢查下一個兄弟元素
                                                            try:
                                                                next_sibling = element.locator('~ *').first
                                                                if next_sibling:
                                                                    sibling_text = next_sibling.inner_text()
                                                                    amount_match = re.search(r'(\d+)\s*元', sibling_text)
                                                                    if amount_match:
                                                                        self_pay_amount = amount_match.group(0)
                                                                        print(f"💰 在「負擔金額」兄弟元素中找到金額: {self_pay_amount}")
                                                                        break
                                                            except:
                                                                pass
                                                        else:
                                                            # 包含金額相關文字的元素，直接提取
                                                            def is_valid_amount_text(text):
                                                                """檢查是否為有效的金額文字"""
                                                                if not text:
                                                                    return False
                                                                # 檢查是否包含數字
                                                                has_digit = any(c.isdigit() for c in text)
                                                                if not has_digit:
                                                                    return False
                                                                # 檢查是否包含金額相關符號或文字
                                                                amount_indicators = ['元', '$', '＄', '負擔金額', '自付', '費用', '金額']
                                                                has_amount_indicator = any(indicator in text for indicator in amount_indicators)
                                                                return has_amount_indicator
                                                            
                                                            if is_valid_amount_text(element_text):
                                                                self_pay_amount = element_text
                                                                print(f"💰 金額選擇器成功: {amount_selector}")
                                                                break
                                                
                                                if self_pay_amount != "未找到":
                                                    break
                                        else:
                                            # 普通選擇器
                                            amount_element = order_element.query_selector(amount_selector)
                                            if amount_element and amount_element.is_visible():
                                                amount_text = amount_element.inner_text().strip()
                                                print(f"💰 找到元素，文字內容: '{amount_text}'")
                                                # 檢查是否為有效的金額格式
                                                def is_valid_amount(text):
                                                    """檢查是否為有效的金額格式"""
                                                    if not text:
                                                        return False
                                                    # 檢查是否包含數字
                                                    has_digit = any(c.isdigit() for c in text)
                                                    if not has_digit:
                                                        return False
                                                    # 檢查是否包含金額相關符號或文字
                                                    amount_indicators = ['元', '$', '＄', '負擔金額', '自付', '費用', '金額']
                                                    has_amount_indicator = any(indicator in text for indicator in amount_indicators)
                                                    return has_amount_indicator
                                                
                                                if is_valid_amount(amount_text):
                                                    self_pay_amount = amount_text
                                                    print(f"💰 金額選擇器成功: {amount_selector} -> '{amount_text}'")
                                                    break
                                                else:
                                                    print(f"💰 文字內容不符合金額格式: '{amount_text}'")
                                                    print(f"💰 檢查結果: 包含數字={any(c.isdigit() for c in amount_text)}, 包含金額指示符={any(indicator in amount_text for indicator in ['元', '$', '＄', '負擔金額', '自付', '費用', '金額'])}")
                                            else:
                                                print(f"💰 元素不存在或不可見")
                                    except Exception as e:
                                        print(f"⚠️ 金額選擇器 {amount_selector} 發生錯誤: {e}")
                                        continue
                                print(f"💰 負擔金額: {self_pay_amount}")
                                
                                # 整理結果
                                result_entry = {
                                    'date_time': date_text,
                                    'car_number': car_number,
                                    'driver': driver_name,
                                    'self_pay_amount': self_pay_amount,
                                    'attempt': current_attempt
                                }
                                
                                results.append(result_entry)
                                print(f"✅ 第 {record_index} 筆記錄提取結果: {result_entry}")
                                take_screenshot(f"attempt_{current_attempt}_record_{record_index}_extracted")
                                
                            except Exception as extract_error:
                                print(f"❌ 提取第 {record_index} 筆記錄資訊時發生錯誤: {extract_error}")
                                take_screenshot(f"attempt_{current_attempt}_record_{record_index}_extract_error")
                                continue
                                
                        else:
                            print(f"❌ 未找到第 {record_index} 筆記錄的展開按鈕")
                            take_screenshot(f"attempt_{current_attempt}_record_{record_index}_no_expand")
                            
                    except Exception as record_error:
                        print(f"❌ 處理第 {record_index} 筆記錄時發生錯誤: {record_error}")
                        continue
                
                print(f"嘗試 {current_attempt} 搜尋完成")
                print(f"📊 統計: 已檢查 {total_records_checked} 個記錄，找到匹配 {current_attempt_results} 筆")
                
                # 🎯 SPA 智慧翻頁策略
                print("🎯 SPA 翻頁檢測：嘗試觸發載入更多資料...")
                
                print(f"📊 當前統計: 總共 {total_elements_on_page} 個元素，已派車記錄 {len(dispatch_records)} 個，匹配記錄 {current_attempt_results} 筆")
                
                # 🌐 嘗試使用 JavaScript 直接獲取更多資料
                print("🔧 嘗試 JavaScript 方法獲取更多頁面資料...")
                
                # 記錄當前記錄數量
                current_record_count = total_elements_on_page
                
                # 捲動到頁面底部觸發可能的無限捲動
                driver['page'].evaluate("window.scrollTo(0, document.body.scrollHeight)")
                driver['page'].wait_for_timeout(2000)
                take_screenshot(f"attempt_{current_attempt}_bottom")
                
                # 🎯 SPA 專用的下一頁處理邏輯
                next_page_attempted = False
                
                # 尋找下一頁按鈕（只使用主要的幾個選擇器）
                next_page_selectors = [
                    'i.icon-pager_next',  # 主要選擇器
                    '.icon-pager_next',
                    'button:has-text(">")',
                    '.pager .next'
                ]
                
                for selector in next_page_selectors:
                    try:
                        next_button = driver['page'].query_selector(selector)
                        if next_button and next_button.is_visible() and next_button.is_enabled():
                            button_class = next_button.get_attribute('class') or ''
                            
                            # 檢查按鈕是否被禁用
                            if 'disabled' in button_class.lower():
                                print(f"❌ 下一頁按鈕已禁用: {selector}")
                                print("✅ 已到達最後一頁，搜尋結束")
                                next_page_attempted = True
                                break
                                
                            print(f"✅ 找到可用的下一頁按鈕: {selector}")
                            
                            # 🚀 點擊下一頁按鈕
                            next_button.scroll_into_view_if_needed()
                            driver['page'].wait_for_timeout(1000)
                            next_button.click()
                            print(f"🖱️ 已點擊下一頁按鈕")
                            
                            # 等待新資料載入
                            driver['page'].wait_for_timeout(3000)
                            driver['page'].wait_for_load_state("networkidle")
                            
                            # 檢查是否載入了新資料
                            new_order_elements = driver['page'].query_selector_all('.order_list')
                            new_record_count = len(new_order_elements)
                            
                            if new_record_count > current_record_count:
                                print(f"✅ 成功載入更多資料: {current_record_count} → {new_record_count}")
                                next_page_attempted = True
                                break
                            else:
                                print(f"⚠️ 點擊後沒有新資料，可能已經是最後一頁")
                                next_page_attempted = True
                                break
                    except Exception as e:
                        print(f"⚠️ 檢查下一頁按鈕 {selector} 時發生錯誤: {e}")
                        continue
                
                # 🎯 SPA 結束條件邏輯
                if next_page_attempted:
                    # 如果已嘗試過翻頁，檢查是否有新資料
                    final_order_elements = driver['page'].query_selector_all('.order_list')
                    final_record_count = len(final_order_elements)
                    
                    if final_record_count <= current_record_count:
                        print("✅ 沒有更多資料，搜尋結束")
                        break
                    else:
                        print(f"✅ 發現新資料，繼續下一輪搜尋")
                else:
                    print("❌ 沒有找到下一頁按鈕，搜尋結束")
                    break
                
                # 增加嘗試次數
                current_attempt += 1
                
                # 防止無限迴圈
                if current_attempt > max_attempts:
                    print(f"⚠️ 已達到最大嘗試次數 ({max_attempts})，停止搜尋")
                    break
            
            print(f"✅ 處理完成，共檢查 {total_records_checked} 筆記錄")
            print(f"📊 統計: 找到已派車記錄 {total_dispatch_records_found} 筆，成功處理 {len(results)} 筆")
            
            # 🎯 寫入結果檔案
            print("將搜尋結果寫入 search_result.txt...")
            
            taipei_tz = pytz.timezone('Asia/Taipei')
            query_time = datetime.now(taipei_tz)
            result_content = f"派車結果查詢時間: {query_time.strftime('%Y-%m-%d %H:%M:%S')} (台北時區)\n"
            result_content += f"🎯 搜尋範圍: 所有「已派車」狀態的記錄 (不限制日期)\n"
            result_content += f"總共檢查記錄數: {total_records_checked}\n"
            result_content += f"累計找到已派車記錄數: {total_dispatch_records_found}\n"
            result_content += f"成功處理的已派車記錄數: {len(results)}\n"
            result_content += f"{'='*60}\n\n"
            
            if results:
                for i, result in enumerate(results, 1):
                    result_content += f"🚗 已派車記錄 {i}:\n"
                    result_content += f"預約日期/時段: {result['date_time']}\n"
                    result_content += f"車號: {result['car_number']}\n"
                    result_content += f"指派司機: {result['driver']}\n"
                    result_content += f"自付金額: {result['self_pay_amount']}\n"
                    result_content += f"狀態: 已派車 🚗\n"
                    result_content += f"{'='*50}\n\n"
                
                print(f"✅ 找到 {len(results)} 筆已派車記錄")
            else:
                result_content += "❌ 未找到符合條件的已派車記錄\n\n"
                result_content += "💡 提示: 只搜尋「已派車」狀態的記錄，其他狀態(已接受、已確立、執行中、已完成、已取消)都會被跳過\n\n"
                print(f"❌ 沒有找到已派車記錄")
            
            # 寫入檔案
            with open(result_file, 'w', encoding='utf-8') as f:
                f.write(result_content)
            
            print(f"✅ 搜尋結果已寫入 search_result.txt")
            print(f"📊 已派車記錄統計: 累計找到 {total_dispatch_records_found} 筆已派車記錄，成功處理 {len(results)} 筆")
            print(f"結果內容:\n{result_content}")
            
            take_screenshot("final_result_saved")
            return len(results) > 0
            
        except Exception as e:
            print(f"訂單查詢過程發生錯誤: {e}")
            take_screenshot("order_query_error")
            return False
            
    except Exception as e:
        print(f"派車結果抓取過程發生錯誤: {e}")
        take_screenshot("dispatch_error")
        return False
        
    finally:
        if driver:
            try:
                driver['page'].close()
                driver['browser'].close()
                print("瀏覽器已關閉")
            except Exception as e:
                print(f"關閉瀏覽器時發生錯誤: {e}")


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
            
            # 🥇 基於成功日誌優化的選擇器順序 - 將最成功的方法放在前面
            login_selectors = [
                # 🥇 最成功的登入方法 (基於成功日誌分析)
                'a:has-text("民眾登入")',
                
                # 🥈 其他高成功率方法
                'button:has-text("民眾登入")',
                'text=民眾登入',
                '*:has-text("民眾登入")',
                
                # 🥉 具體元素類型
                'input[value="民眾登入"]',
                'input[type="submit"]:has-value("民眾登入")',
                'input[type="button"]:has-value("民眾登入")',
                'button[value*="民眾登入"]',
                
                # 🔄 備用方法
                ':text("民眾登入")',
                'button[name*="login"]',
                'input[value*="登入"]',
                'a[href*="login"]',
                
                # 表單提交
                'form input[type="submit"]',
                'form button[type="submit"]',
                
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
                    # 🥇 基於成功日誌優化的浮動視窗選擇器順序
                    # 🥇 最成功的方法 (基於成功日誌分析)
                    '.dialog:has-text("登入成功")',
                    
                    # 🥈 其他高成功率方法
                    '.modal:has-text("登入成功")',
                    '.popup:has-text("登入成功")',
                    '.alert:has-text("登入成功")',
                    '[role="dialog"]:has-text("登入成功")',
                    
                    # 🔄 備用方法
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
                    
                    # 🎯 基於trace結果：使用精確的確定按鈕選擇器
                    try:
                        print("🎯 使用精確的確定按鈕選擇器...")
                        
                        # 直接使用trace到的精確選擇器
                        precise_selector = 'span.dialog-button'
                        
                        element = driver['page'].locator(precise_selector).first
                        if element.count() > 0 and element.is_visible():
                            print(f"找到精確的確定按鈕: {precise_selector}")
                            element.click()
                            driver['page'].wait_for_timeout(1000)
                            print("✅ 確定按鈕點擊成功")
                            confirm_clicked = True
                        else:
                            print("❌ 精確選擇器未找到確定按鈕")
                            confirm_clicked = False
                    
                    except Exception as e:
                        print(f"❌ 確定按鈕點擊失敗: {e}")
                        confirm_clicked = False
                    
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
            
            # 確保選擇第一個下拉選單作為上車地點
            try:
                # 尋找第一個可見的下拉選單
                first_select = driver['page'].locator('select').first
                if first_select.count() > 0 and first_select.is_visible():
                    # 檢查選項
                    options = first_select.locator('option').all()
                    option_texts = [opt.text_content() or '' for opt in options]
                    print(f"第一個選單的選項: {option_texts}")
                    
                    if '醫療院所' in option_texts:
                        first_select.select_option('醫療院所')
                        print("第一個選單成功選擇：醫療院所")
                    else:
                        print("第一個選單沒有醫療院所選項，嘗試其他方式...")
                        # 嘗試通用選擇
                        driver['page'].select_option('select', '醫療院所')
                else:
                    print("找不到第一個下拉選單，嘗試通用選擇...")
                    driver['page'].select_option('select', '醫療院所')
            except Exception as e:
                print(f"選擇上車地點失敗: {e}")
                # 後備方案
                try:
                    driver['page'].select_option('select', '醫療院所')
                except Exception as e2:
                    print(f"後備方案也失敗: {e2}")
            
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
            
            # 等待 Google 搜尋結果出現並選擇第一個
            print("等待並選擇搜尋結果...")
            driver['page'].wait_for_timeout(2000)  # 給搜尋結果時間載入
            
            # 使用最簡單可靠的方法：鍵盤導航
            success = False
            try:
                print("使用鍵盤方法選擇第一個搜尋結果...")
                
                # 確保輸入框有焦點
                pickup_input.click()
                driver['page'].wait_for_timeout(1000)
                
                # 方法1: 直接按向下箭頭和 Enter
                print("方法1: 按向下箭頭選擇第一個結果...")
                driver['page'].keyboard.press('ArrowDown')
                driver['page'].wait_for_timeout(1500)
                take_screenshot("arrow_down_pressed")
                
                # 按 Enter 確認
                driver['page'].keyboard.press('Enter')
                driver['page'].wait_for_timeout(2000)
                take_screenshot("enter_pressed")
                
                # 檢查輸入框值是否變化
                final_value = pickup_input.input_value()
                print(f"鍵盤選擇後輸入框的值: '{final_value}'")
                
                # 使用相同的寬鬆判斷條件（中英文關鍵字）
                keywords = ['亞東', '醫院', '紀念', 'Far Eastern', 'Memorial', 'Hospital', 'FEMH']
                addr_keywords = ['台北', '新北', '板橋', 'Taipei', 'New Taipei']
                if final_value and final_value.strip():
                    if (any(keyword in final_value for keyword in keywords) or
                        (len(final_value.strip()) >= len('亞東紀念醫院') and final_value.strip() != '亞東紀念醫院') or
                        any(addr_keyword in final_value for addr_keyword in addr_keywords)):
                        print("鍵盤方法成功！")
                        success = True
                    else:
                        print("鍵盤方法可能未成功，值未顯著變化")
                else:
                    print("鍵盤方法可能未成功，值為空")
                
            except Exception as e:
                print(f"鍵盤方法失敗: {e}")
            
            # 方法2: 如果鍵盤方法失敗，嘗試點擊第一個可見的搜尋結果
            if not success:
                try:
                    print("方法2: 嘗試點擊第一個可見的搜尋結果...")
                    
                    # 簡單的選擇器，按優先級排序
                    simple_selectors = [
                        '.pac-item:first-child',
                        '.autocomplete-dropdown li:first-child', 
                        '.suggestions li:first-child',
                        '[role="option"]:first-child',
                        'ul li:first-child'
                    ]
                    
                    for selector in simple_selectors:
                        try:
                            element = driver['page'].locator(selector).first
                            if element.count() > 0 and element.is_visible():
                                print(f"找到並點擊: {selector}")
                                element.click()
                                driver['page'].wait_for_timeout(2000)
                                
                                # 檢查是否成功
                                final_value = pickup_input.input_value()
                                # 使用相同的寬鬆判斷條件（中英文關鍵字）
                                if final_value and final_value.strip():
                                    keywords = ['亞東', '醫院', '紀念', 'Far Eastern', 'Memorial', 'Hospital', 'FEMH']
                                    addr_keywords = ['台北', '新北', '板橋', 'Taipei', 'New Taipei']
                                    if (any(keyword in final_value for keyword in keywords) or
                                        (len(final_value.strip()) >= len('亞東紀念醫院') and final_value.strip() != '亞東紀念醫院') or
                                        any(addr_keyword in final_value for addr_keyword in addr_keywords)):
                                        print("點擊方法成功！")
                                        success = True
                                    break
                        except Exception as e:
                            print(f"選擇器 {selector} 失敗: {e}")
                            continue
                            
                except Exception as e:
                    print(f"點擊方法失敗: {e}")
            
            # 方法3: 最後手段 - 檢查所有可見的列表項目
            if not success:
                try:
                    print("方法3: 檢查所有列表項目...")
                    all_lis = driver['page'].locator('li:visible').all()
                    for i, li in enumerate(all_lis[:5]):  # 只檢查前5個
                        try:
                            text = li.text_content() or ''
                            print(f"列表項目 {i}: '{text}'")
                            if '亞東' in text and '醫院' in text:
                                print(f"找到相關項目，點擊: {text}")
                                li.click()
                                driver['page'].wait_for_timeout(2000)
                                
                                final_value = pickup_input.input_value()
                                # 使用相同的寬鬆判斷條件（中英文關鍵字）
                                if final_value and final_value.strip():
                                    keywords = ['亞東', '醫院', '紀念', 'Far Eastern', 'Memorial', 'Hospital', 'FEMH']
                                    addr_keywords = ['台北', '新北', '板橋', 'Taipei', 'New Taipei']
                                    if (any(keyword in final_value for keyword in keywords) or
                                        (len(final_value.strip()) >= len('亞東紀念醫院') and final_value.strip() != '亞東紀念醫院') or
                                        any(addr_keyword in final_value for addr_keyword in addr_keywords)):
                                        print("列表點擊成功！")
                                        success = True
                                    break
                        except Exception as e:
                            continue
                except Exception as e:
                    print(f"列表檢查失敗: {e}")
            
            if success:
                print("✅ 搜尋結果選擇成功")
                take_screenshot("pickup_location_selected")
            else:
                print("⚠️ 搜尋結果選擇失敗，但繼續執行...")
                take_screenshot("pickup_selection_failed")
            
            # 8. 下車地點選擇「住家」
            print("=== 開始選擇下車地點：住家 ===")
            
            # 等待頁面穩定
            driver['page'].wait_for_timeout(1000)
            
            # 重新獲取所有選單，確保是最新的狀態
            all_selects = driver['page'].locator('select').all()
            total_selects = len(all_selects)
            print(f"頁面上總共有 {total_selects} 個下拉選單")
            
            # 拍照記錄當前選單狀態
            take_screenshot("before_home_selection")
            
            dropoff_success = False
            
            # 智能檢測下車地點選單的邏輯改進
            print("=== 智能檢測下車地點選單 ===")
            
            # 詳細檢查每個選單
            for i, select_elem in enumerate(all_selects):
                try:
                    if not select_elem.is_visible():
                        print(f"選單 {i}: 不可見，跳過")
                        continue
                        
                    # 獲取選單屬性
                    name = select_elem.get_attribute('name') or ''
                    id_attr = select_elem.get_attribute('id') or ''
                    class_attr = select_elem.get_attribute('class') or ''
                    
                    print(f"選單 {i}: name='{name}', id='{id_attr}', class='{class_attr}'")
                    
                    # 獲取選單的所有選項
                    options = select_elem.locator('option').all()
                    option_texts = []
                    option_values = []
                    for option in options:
                        text = option.text_content() or ''
                        value = option.get_attribute('value') or ''
                        if text.strip():  # 只記錄非空選項
                            option_texts.append(text.strip())
                            option_values.append(value)
                    
                    print(f"選單 {i} 的選項: {option_texts}")
                    print(f"選單 {i} 的值: {option_values}")
                    
                    # 改進的判斷邏輯：
                    # 1. 更精確地識別上車地點選單（跳過）
                    # 2. 更智能地識別下車地點選單
                    
                    # 檢查是否為上車地點選單（更精確的判斷）
                    is_pickup_location = False
                    pickup_indicators = ['pickup', 'origin', 'from', 'start', 'boarding']
                    pickup_options = ['醫療院所', '醫院', '診所', '衛生所']
                    
                    # 通過屬性判斷
                    for indicator in pickup_indicators:
                        if indicator in name.lower() or indicator in id_attr.lower() or indicator in class_attr.lower():
                            is_pickup_location = True
                            break
                    
                    # 通過選項內容判斷 - 如果是第一個選單且包含醫療相關選項
                    if i == 0 and any(option in option_texts for option in pickup_options):
                        is_pickup_location = True
                    
                    if is_pickup_location:
                        print(f"選單 {i}: 判斷為上車地點選單，跳過")
                        continue
                    
                    # 檢查是否為下車地點選單
                    is_dropoff_location = False
                    dropoff_indicators = ['dropoff', 'destination', 'to', 'end', 'alighting']
                    
                    # 通過屬性判斷
                    for indicator in dropoff_indicators:
                        if indicator in name.lower() or indicator in id_attr.lower() or indicator in class_attr.lower():
                            is_dropoff_location = True
                            break
                    
                    # 通過選項內容判斷 - 包含住家選項的很可能是下車地點
                    if '住家' in option_texts:
                        is_dropoff_location = True
                    
                    if is_dropoff_location and '住家' in option_texts:
                        print(f"選單 {i}: 確認為下車地點選單，包含住家選項，開始選擇...")
                        try:
                            # 先檢查當前選中的值
                            current_value = select_elem.input_value()
                            print(f"選單 {i} 當前值: '{current_value}'")
                            
                            # 如果已經選中住家，跳過
                            if current_value == '住家' or '住家' in str(current_value):
                                print(f"選單 {i} 已經選擇住家，跳過")
                                dropoff_success = True
                                break
                            
                            # 找到住家選項的索引和值
                            home_index = None
                            home_value = None
                            for j, option_text in enumerate(option_texts):
                                if option_text == '住家':
                                    home_index = j
                                    home_value = option_values[j] if j < len(option_values) else None
                                    break
                            
                            if home_index is not None:
                                print(f"住家選項在索引 {home_index}，值: '{home_value}'")
                                
                                # 嘗試多種選擇方法（改進版）
                                success = False
                                
                                # 方法1: 使用文字值選擇
                                try:
                                    print("嘗試方法1: 使用文字值選擇住家")
                                    select_elem.select_option('住家')
                                    driver['page'].wait_for_timeout(1000)  # 增加等待時間
                                    new_value = select_elem.input_value()
                                    print(f"方法1 (文字值) 選擇後的值: '{new_value}'")
                                    if new_value == '住家' or (new_value and new_value != current_value):
                                        success = True
                                        print("✅ 方法1成功")
                                except Exception as e:
                                    print(f"方法1 (文字值) 失敗: {e}")
                                
                                # 方法2: 使用value屬性選擇（優先嘗試）
                                if not success and home_value:
                                    try:
                                        print(f"嘗試方法2: 使用value屬性選擇住家 (value='{home_value}')")
                                        select_elem.select_option(value=home_value)
                                        driver['page'].wait_for_timeout(1000)
                                        new_value = select_elem.input_value()
                                        print(f"方法2 (value屬性) 選擇後的值: '{new_value}'")
                                        if new_value and new_value != current_value:
                                            success = True
                                            print("✅ 方法2成功")
                                    except Exception as e:
                                        print(f"方法2 (value屬性) 失敗: {e}")
                                
                                # 方法3: 使用索引值選擇
                                if not success:
                                    try:
                                        print(f"嘗試方法3: 使用索引值選擇住家 (index={home_index})")
                                        select_elem.select_option(index=home_index)
                                        driver['page'].wait_for_timeout(1000)
                                        new_value = select_elem.input_value()
                                        print(f"方法3 (索引值) 選擇後的值: '{new_value}'")
                                        if new_value and new_value != current_value:
                                            success = True
                                            print("✅ 方法3成功")
                                    except Exception as e:
                                        print(f"方法3 (索引值) 失敗: {e}")
                                
                                # 方法4: 直接點擊住家選項（最後手段）
                                if not success:
                                    try:
                                        print("嘗試方法4: 直接點擊住家選項")
                                        home_option = select_elem.locator('option').nth(home_index)
                                        home_option.click()
                                        driver['page'].wait_for_timeout(1000)
                                        new_value = select_elem.input_value()
                                        print(f"方法4 (直接點擊) 選擇後的值: '{new_value}'")
                                        if new_value and new_value != current_value:
                                            success = True
                                            print("✅ 方法4成功")
                                    except Exception as e:
                                        print(f"方法4 (直接點擊) 失敗: {e}")
                                
                                # 驗證最終結果
                                if success:
                                    final_value = select_elem.input_value()
                                    print(f"✅ 選單 {i} 成功選擇住家作為下車地點，最終值: '{final_value}'")
                                    dropoff_success = True
                                    take_screenshot("home_selected_success")
                                    
                                    # 觸發change事件確保系統響應
                                    try:
                                        select_elem.dispatch_event('change')
                                        driver['page'].wait_for_timeout(500)
                                        print("已觸發change事件")
                                    except:
                                        pass
                                    break
                                else:
                                    print(f"❌ 選單 {i} 所有方法都失敗，無法選擇住家")
                            else:
                                print(f"❌ 在選單 {i} 中找不到住家選項的索引")
                                
                        except Exception as e:
                            print(f"❌ 選單 {i} 選擇住家時發生錯誤: {e}")
                            continue
                    else:
                        print(f"選單 {i}: 不是下車地點選單或沒有住家選項，跳過")
                        
                except Exception as e:
                    print(f"檢查選單 {i} 時發生錯誤: {e}")
                    continue
            
            # 如果沒有成功，嘗試更具體的選擇器和智能推理
            if not dropoff_success:
                print("通過智能檢測未成功，嘗試備用選擇策略...")
                
                take_screenshot("backup_selection_attempt")
                
                # 策略1: 嘗試具體的下車地點選擇器
                specific_selectors = [
                    'select[name*="dropoff"]',  # 包含 dropoff 的 name
                    'select[name*="destination"]',  # 包含 destination 的 name  
                    'select[name*="to"]',  # 包含 to 的 name
                    'select[name*="end"]',  # 包含 end 的 name
                    'select[name*="下車"]',  # 包含"下車"的中文
                    'select[id*="dropoff"]',  # 包含 dropoff 的 id
                    'select[id*="destination"]',  # 包含 destination 的 id
                    'select[id*="下車"]',  # 包含"下車"的中文id
                ]
                
                for selector in specific_selectors:
                    try:
                        print(f"嘗試備用選擇器: {selector}")
                        element = driver['page'].locator(selector).first
                        
                        if element.count() > 0 and element.is_visible():
                            # 檢查選項
                            options = element.locator('option').all()
                            option_texts = [opt.text_content() or '' for opt in options if opt.text_content()]
                            print(f"選擇器 {selector} 的選項: {option_texts}")
                            
                            if '住家' in option_texts:
                                print(f"在選擇器 {selector} 中找到住家，嘗試選擇...")
                                
                                # 使用改進的選擇方法
                                success = False
                                for method_name, select_method in [
                                    ("文字值", lambda: element.select_option('住家')),
                                    ("索引值", lambda: element.select_option(index=option_texts.index('住家'))),
                                    ("點擊", lambda: element.locator('option').filter(has_text='住家').click())
                                ]:
                                    try:
                                        print(f"  嘗試{method_name}方法...")
                                        select_method()
                                        driver['page'].wait_for_timeout(1000)
                                        
                                        # 驗證
                                        new_value = element.input_value()
                                        if new_value == '住家' or '住家' in str(new_value):
                                            print(f"✅ 選擇器 {selector} ({method_name}方法) 成功選擇住家")
                                            dropoff_success = True
                                            success = True
                                            break
                                    except Exception as e:
                                        print(f"  {method_name}方法失敗: {e}")
                                
                                if success:
                                    break
                                    
                    except Exception as e:
                        print(f"選擇器 {selector} 失敗: {e}")
                        continue
                
                # 策略2: 如果還是失敗，嘗試序號方式（第二個、最後一個等）
                if not dropoff_success:
                    print("嘗試序號策略選擇下車地點...")
                    
                    sequence_selectors = [
                        ('select:nth-of-type(2)', '第二個 select 元素'),
                        ('select:last-of-type', '最後一個 select 元素'),
                        ('select:nth-child(2)', '第二個子元素 select'),
                        ('form select:last-child', '表單中最後一個 select')
                    ]
                    
                    for selector, description in sequence_selectors:
                        try:
                            print(f"嘗試 {description}: {selector}")
                            element = driver['page'].locator(selector).first
                            
                            if element.count() > 0 and element.is_visible():
                                # 檢查選項
                                options = element.locator('option').all()
                                option_texts = [opt.text_content() or '' for opt in options if opt.text_content()]
                                print(f"{description} 的選項: {option_texts}")
                                
                                if '住家' in option_texts:
                                    print(f"在{description}中找到住家，嘗試選擇...")
                                    element.select_option('住家')
                                    driver['page'].wait_for_timeout(1000)
                                    
                                    # 驗證
                                    new_value = element.input_value()
                                    if new_value == '住家' or '住家' in str(new_value):
                                        print(f"✅ {description} 成功選擇住家")
                                        dropoff_success = True
                                        break
                                        
                        except Exception as e:
                            print(f"{description} 失敗: {e}")
                            continue
            
            if dropoff_success:
                print("✅ 下車地點'住家'選擇成功")
                
                # 8.1 處理住家地址自動填入
                print("=== 處理住家地址自動填入 ===")
                
                # 等待頁面響應下車地點選擇
                driver['page'].wait_for_timeout(1500)
                
                # 尋找下車地點地址輸入框（注意：要避開上車地點的地址框）
                address_input = None
                
                # 更精確的下車地點地址框選擇器
                dropoff_address_selectors = [
                    # 明確的下車地點地址框
                    'input[name*="getOff"][name*="address"]',
                    'input[name*="dropoff"][name*="address"]',
                    'input[name*="destination"][name*="address"]',
                    'input[id*="getOff"][id*="address"]',
                    'input[id*="dropoff"][id*="address"]',
                    'input[id*="destination"][id*="address"]',
                    
                    # 根據位置關係找到下車地點附近的地址框
                    '#getOff_location + input',  # getOff_location 選單後面的輸入框
                    '#getOff_location ~ input',  # getOff_location 選單同級的輸入框
                    'select[name="getOff_location"] + input',
                    'select[name="getOff_location"] ~ input',
                ]
                
                print("尋找下車地點地址輸入框...")
                for selector in dropoff_address_selectors:
                    try:
                        print(f"嘗試下車地點地址選擇器: {selector}")
                        elements = driver['page'].locator(selector).all()
                        
                        for i, element in enumerate(elements):
                            if element.is_visible() and element.is_enabled():
                                placeholder = element.get_attribute('placeholder') or ''
                                name = element.get_attribute('name') or ''
                                id_attr = element.get_attribute('id') or ''
                                
                                print(f"找到地址輸入框 {selector}[{i}]: placeholder='{placeholder}', name='{name}', id='{id_attr}'")
                                
                                # 確保不是上車地點的地址框
                                if not any(keyword in (name + id_attr).lower() 
                                          for keyword in ['pickup', 'pickUp', 'origin', 'from', 'start']):
                                    address_input = element
                                    print(f"✅ 確認為下車地點地址框: {selector}[{i}]")
                                    break
                                else:
                                    print(f"❌ 跳過上車地點地址框: {selector}[{i}]")
                        
                        if address_input:
                            break
                            
                    except Exception as e:
                        print(f"檢查下車地點地址選擇器 {selector} 失敗: {e}")
                        continue
                
                # 如果沒找到明確的下車地點地址框，使用通用方法但更謹慎
                if not address_input:
                    print("未找到明確的下車地點地址框，檢查所有可見地址輸入框...")
                    
                    all_inputs = driver['page'].locator('input[type="text"]').all()
                    for i, element in enumerate(all_inputs):
                        try:
                            if element.is_visible() and element.is_enabled():
                                placeholder = element.get_attribute('placeholder') or ''
                                name = element.get_attribute('name') or ''
                                id_attr = element.get_attribute('id') or ''
                                
                                print(f"輸入框 {i}: placeholder='{placeholder}', name='{name}', id='{id_attr}'")
                                
                                # 檢查是否可能是地址框，但不是上車地點的
                                is_address_like = any(keyword in (placeholder + name + id_attr).lower() 
                                                    for keyword in ['地址', '住址', 'address'])
                                is_pickup_related = any(keyword in (name + id_attr).lower() 
                                                      for keyword in ['pickup', 'pickUp', 'origin', 'from', 'start'])
                                
                                if is_address_like and not is_pickup_related:
                                    # 額外檢查：如果是第二個或之後的地址框，更可能是下車地點
                                    if i > 0:  # 不是第一個輸入框
                                        address_input = element
                                        print(f"✅ 選擇第 {i} 個地址框作為下車地點地址框")
                                        break
                        except Exception as e:
                            print(f"檢查輸入框 {i} 失敗: {e}")
                            continue
                
                if address_input:
                    print("找到下車地點地址輸入框，檢查自動填入狀態...")
                    
                    # 只檢查自動填入狀態，不手動填入
                    max_wait_attempts = 8
                    auto_filled = False
                    
                    for attempt in range(max_wait_attempts):
                        try:
                            current_value = address_input.input_value() or ''
                            print(f"檢查自動填入 {attempt+1}/{max_wait_attempts}: 當前值='{current_value}'")
                            
                            # 如果有值且長度合理，認為是自動填入成功
                            if current_value.strip() and len(current_value.strip()) > 3:
                                print(f"✅ 下車地點地址已自動填入: '{current_value}'")
                                auto_filled = True
                                break
                            
                            # 輕微觸發檢查（但不填入值）
                            if attempt < 3:
                                try:
                                    address_input.click()
                                    driver['page'].wait_for_timeout(500)
                                except:
                                    pass
                                
                            driver['page'].wait_for_timeout(1000)
                            
                        except Exception as e:
                            print(f"檢查自動填入狀態失敗: {e}")
                            driver['page'].wait_for_timeout(1000)
                    
                    if auto_filled:
                        print("✅ 下車地點地址自動填入正常")
                        take_screenshot("dropoff_address_auto_filled")
                    else:
                        print("⚠️ 下車地點地址未自動填入，嘗試替代方案...")
                        take_screenshot("dropoff_address_empty")
                        
                        # 替代方案1：重新選擇住家選項觸發自動填入
                        print("替代方案1：重新選擇住家選項")
                        try:
                            home_select = driver['page'].locator('select').filter(has_text='住家').first
                            if home_select.is_visible():
                                home_select.select_option('住家')
                                driver['page'].wait_for_timeout(2000)
                                
                                # 再次檢查地址是否填入
                                current_value = address_input.input_value() or ''
                                if current_value.strip():
                                    print(f"✅ 重新選擇後地址自動填入: '{current_value}'")
                                    auto_filled = True
                        except Exception as e:
                            print(f"替代方案1失敗: {e}")
                        
                        # 替代方案2：點擊地址框並等待自動完成
                        if not auto_filled:
                            print("替代方案2：點擊地址框觸發自動完成")
                            try:
                                address_input.click()
                                driver['page'].wait_for_timeout(1000)
                                address_input.focus()
                                driver['page'].wait_for_timeout(2000)
                                
                                current_value = address_input.input_value() or ''
                                if current_value.strip():
                                    print(f"✅ 點擊觸發後地址自動填入: '{current_value}'")
                                    auto_filled = True
                            except Exception as e:
                                print(f"替代方案2失敗: {e}")
                        
                        # 替代方案3：檢查是否有「使用住家地址」按鈕
                        if not auto_filled:
                            print("替代方案3：尋找使用住家地址按鈕")
                            try:
                                use_home_buttons = [
                                    'button:has-text("使用住家地址")',
                                    'button:has-text("使用預設地址")',
                                    'a:has-text("使用住家地址")',
                                    'a:has-text("使用預設地址")',
                                    '[data-action*="home"]',
                                    '[data-action*="default"]'
                                ]
                                
                                for selector in use_home_buttons:
                                    try:
                                        button = driver['page'].locator(selector).first
                                        if button.is_visible():
                                            print(f"找到使用住家地址按鈕: {selector}")
                                            button.click()
                                            driver['page'].wait_for_timeout(2000)
                                            
                                            current_value = address_input.input_value() or ''
                                            if current_value.strip():
                                                print(f"✅ 使用住家地址按鈕後地址填入: '{current_value}'")
                                                auto_filled = True
                                                break
                                    except:
                                        continue
                            except Exception as e:
                                print(f"替代方案3失敗: {e}")
                        
                        # 替代方案4：手動填入常見的住家地址
                        if not auto_filled:
                            print("替代方案4：手動填入預設住家地址")
                            try:
                                # 常見的預設住家地址
                                default_home_addresses = [
                                    "新北市板橋區文化路一段188巷44號",
                                    "新北市新莊區中正路1號",
                                    "新北市三重區重新路1號"
                                ]
                                
                                # 先嘗試填入第一個地址
                                test_address = default_home_addresses[0]
                                address_input.fill(test_address)
                                driver['page'].wait_for_timeout(1000)
                                
                                current_value = address_input.input_value() or ''
                                if current_value.strip():
                                    print(f"✅ 手動填入住家地址: '{current_value}'")
                                    auto_filled = True
                            except Exception as e:
                                print(f"替代方案4失敗: {e}")
                        
                        # 替代方案5：檢查系統是否有地址選擇下拉選單
                        if not auto_filled:
                            print("替代方案5：尋找住家地址選擇下拉選單")
                            try:
                                # 尋找可能的地址選擇下拉選單
                                address_selects = driver['page'].locator('select').all()
                                for i, select_elem in enumerate(address_selects):
                                    if select_elem.is_visible():
                                        options = select_elem.locator('option').all()
                                        option_texts = [opt.inner_text() for opt in options if opt.is_visible()]
                                        
                                        print(f"地址選擇器 {i} 選項: {option_texts}")
                                        
                                        # 如果包含地址相關選項
                                        for option_text in option_texts:
                                            if any(keyword in option_text for keyword in ['地址', '住址', '新北市', '板橋', '新莊']):
                                                print(f"找到住家地址選項: {option_text}")
                                                select_elem.select_option(option_text)
                                                driver['page'].wait_for_timeout(2000)
                                                
                                                current_value = address_input.input_value() or ''
                                                if current_value.strip():
                                                    print(f"✅ 選擇地址選項後填入: '{current_value}'")
                                                    auto_filled = True
                                                
                                        if auto_filled:
                                            break
                            except Exception as e:
                                print(f"替代方案5失敗: {e}")
                        
                        # 替代方案6：使用JavaScript觸發事件和表單驗證
                        if not auto_filled:
                            print("替代方案6：使用JavaScript觸發住家地址填入")
                            try:
                                # JavaScript 程式碼來觸發住家地址自動填入的多種方法
                                js_trigger_script = """
                                // 嘗試觸發住家地址自動填入的多種方法
                                function triggerHomeAddressFill() {
                                    // 方法1: 找到住家選項並觸發change事件
                                    const homeSelects = document.querySelectorAll('select option[value*="住家"], select option[text*="住家"]');
                                    homeSelects.forEach(option => {
                                        if (option.textContent.includes('住家')) {
                                            const select = option.parentElement;
                                            select.value = option.value;
                                            select.dispatchEvent(new Event('change', {bubbles: true}));
                                            console.log('觸發住家選項change事件');
                                        }
                                    });
                                    
                                    // 方法2: 尋找並填入已保存的住家地址
                                    const addressInputs = document.querySelectorAll('input[type="text"]');
                                    addressInputs.forEach((input, index) => {
                                        const name = (input.name || '').toLowerCase();
                                        const id = (input.id || '').toLowerCase();
                                        const placeholder = (input.placeholder || '').toLowerCase();
                                        
                                        // 檢查是否是地址相關輸入框且不是上車地點
                                        const isAddressInput = ['地址', '住址', 'address'].some(keyword => 
                                            name.includes(keyword) || id.includes(keyword) || placeholder.includes(keyword)
                                        );
                                        const isPickupInput = ['pickup', 'origin', 'from', 'start'].some(keyword => 
                                            name.includes(keyword) || id.includes(keyword)
                                        );
                                        
                                        if (isAddressInput && !isPickupInput && index > 0) {
                                            // 嘗試從localStorage或sessionStorage獲取住家地址
                                            const savedAddress = localStorage.getItem('homeAddress') || 
                                                               sessionStorage.getItem('homeAddress') ||
                                                               '新北市板橋區文化路一段188巷44號';
                                            
                                            if (!input.value.trim()) {
                                                input.value = savedAddress;
                                                input.dispatchEvent(new Event('input', {bubbles: true}));
                                                input.dispatchEvent(new Event('change', {bubbles: true}));
                                                console.log('填入住家地址:', savedAddress);
                                                return savedAddress;
                                            }
                                        }
                                    });
                                    
                                    // 方法3: 觸發表單驗證事件
                                    const forms = document.querySelectorAll('form');
                                    forms.forEach(form => {
                                        form.dispatchEvent(new Event('validate', {bubbles: true}));
                                    });
                                    
                                    return '嘗試JavaScript觸發完成';
                                }
                                
                                return triggerHomeAddressFill();
                                """
                                
                                # 執行JavaScript
                                result = driver['page'].evaluate(js_trigger_script)
                                print(f"JavaScript執行結果: {result}")
                                
                                driver['page'].wait_for_timeout(3000)  # 等待處理
                                
                                # 檢查地址是否已填入
                                current_value = address_input.input_value() or ''
                                if current_value.strip():
                                    print(f"✅ JavaScript觸發後地址填入: '{current_value}'")
                                    auto_filled = True
                            except Exception as e:
                                print(f"替代方案6失敗: {e}")
                        
                        if auto_filled:
                            print("✅ 替代方案成功，下車地點地址已填入")
                            take_screenshot("dropoff_address_alternative_success")
                        else:
                            print("⚠️ 所有替代方案都失敗，但預約可能仍可繼續")
                            take_screenshot("dropoff_address_all_failed")
                            
                            # 檢查是否真的需要地址（有些情況下選擇住家就夠了）
                            final_value = address_input.input_value() or ''
                            print(f"最終地址框狀態: '{final_value}'")
                            
                            # 嘗試繼續預約流程，看看系統是否會報錯
                            print("嘗試繼續預約流程（地址可能不是必填）")
                            
                            # 替代方案7：檢查表單驗證要求
                            print("替代方案7：檢查表單驗證要求")
                            try:
                                # 檢查地址框是否有required屬性
                                is_required = address_input.get_attribute('required') is not None
                                has_asterisk = '*' in (address_input.get_attribute('placeholder') or '')
                                
                                print(f"地址框是否必填: required={is_required}, 有星號={has_asterisk}")
                                
                                if not is_required and not has_asterisk:
                                    print("✅ 地址框非必填，可以繼續預約流程")
                                else:
                                    print("⚠️ 地址框可能是必填，但嘗試強制填入最基本地址")
                                    # 最後嘗試：填入最簡單的地址
                                    simple_address = "新北市"
                                    address_input.fill(simple_address)
                                    driver['page'].wait_for_timeout(1000)
                                    
                                    final_check = address_input.input_value() or ''
                                    if final_check.strip():
                                        print(f"✅ 強制填入基本地址成功: '{final_check}'")
                                        auto_filled = True
                                    
                            except Exception as e:
                                print(f"替代方案7失敗: {e}")
                            
                            # 記錄最終狀態
                            if auto_filled:
                                print("✅ 最終成功填入住家地址")
                                take_screenshot("final_address_success")
                            else:
                                print("❌ 所有方法都無法填入地址，但繼續預約流程")
                                print("   系統可能不需要地址，或會在後續步驟要求填入")
                                take_screenshot("final_address_failed")
                                
                                # 檢查是否可以找到跳過地址的選項
                                try:
                                    skip_options = [
                                        'button:has-text("跳過")',
                                        'button:has-text("略過")',
                                        'a:has-text("稍後填入")',
                                        'input[type="checkbox"]:has(~ label:has-text("暫不填入"))'
                                    ]
                                    
                                    for skip_selector in skip_options:
                                        try:
                                            skip_element = driver['page'].locator(skip_selector).first
                                            if skip_element.is_visible():
                                                print(f"找到跳過選項: {skip_selector}")
                                                skip_element.click()
                                                print("✅ 已點擊跳過地址填入")
                                                break
                                        except:
                                            continue
                                except:
                                    pass
                
                else:
                    print("⚠️ 未找到下車地點地址輸入框，可能系統不需要手動輸入地址")
                    take_screenshot("no_dropoff_address_input_found")
            
            take_screenshot("dropoff_location_final")
            
            # 9. 預約日期/時段選擇
            print("=== 開始選擇預約日期/時段 ===")
            
            # 等待頁面穩定
            driver['page'].wait_for_timeout(2000)
            
            # 重新獲取所有選單
            all_selects = driver['page'].locator('select').all()
            print(f"日期時段頁面總共有 {len(all_selects)} 個下拉選單")
            
            # 詳細檢查每個選單
            for i, select_elem in enumerate(all_selects):
                try:
                    if select_elem.is_visible():
                        name = select_elem.get_attribute('name') or ''
                        id_attr = select_elem.get_attribute('id') or ''
                        options = select_elem.locator('option').all()
                        option_texts = [opt.text_content() or '' for opt in options if opt.text_content()]
                        current_value = select_elem.input_value() or ''
                        
                        print(f"選單 {i}: name='{name}', id='{id_attr}', 當前值='{current_value}'")
                        print(f"選單 {i} 選項: {option_texts}")
                except Exception as e:
                    print(f"檢查選單 {i} 失敗: {e}")
            
            take_screenshot("before_datetime_selection")
            
            # 智能選擇日期時段
            datetime_success = False
            
            try:
                # 策略1: 智能尋找日期相關的選單
                print("=== 策略1: 智能尋找日期選單 ===")
                
                date_selectors = [
                    'select[name*="date"]',
                    'select[name*="日期"]', 
                    'select[id*="date"]',
                    'select[id*="日期"]',
                    'select:has(option[value*="2024"])',  # 包含年份的選單
                    'select:has(option[text*="月"])',     # 包含月份的選單
                    'select:has(option[text*="/"])',      # 包含日期格式的選單
                ]
                
                for selector in date_selectors:
                    try:
                        date_select = driver['page'].locator(selector).first
                        if date_select.count() > 0 and date_select.is_visible():
                            print(f"檢查潛在日期選單: {selector}")
                            
                            # 獲取選項並驗證是否真的是日期選單
                            date_options = date_select.locator('option').all()
                            date_texts = [opt.text_content() or '' for opt in date_options if opt.text_content()]
                            print(f"選項內容: {date_texts}")
                            
                            # 驗證：排除地點選單（包含住家、醫療院所等）
                            location_keywords = ['住家', '醫療院所', '醫院', '診所', '衛生所', '車站', '捷運']
                            is_location_menu = any(keyword in ' '.join(date_texts) for keyword in location_keywords)
                            
                            if is_location_menu:
                                print(f"跳過地點選單: {date_texts}")
                                continue
                            
                            # 驗證：確認包含日期相關內容
                            date_keywords = ['2024', '2025', '月', '日', '/', '-', '今天', '明天']
                            has_date_content = any(keyword in ' '.join(date_texts) for keyword in date_keywords)
                            
                            if has_date_content and len(date_texts) > 1:
                                print(f"✅ 確認為日期選單: {date_texts}")
                                
                                # 選擇最後一個可用日期（排除空白選項）
                                valid_options = [opt for opt in date_texts if opt.strip() and opt != '請選擇']
                                if valid_options:
                                    target_date = valid_options[-1]  # 最後一個日期
                                    print(f"選擇日期: {target_date}")
                                    date_select.select_option(target_date)
                                    driver['page'].wait_for_timeout(1000)
                                    
                                    # 驗證選擇
                                    new_value = date_select.input_value()
                                    if new_value and new_value != '請選擇':
                                        print(f"✅ 日期選擇成功: {new_value}")
                                        break
                            else:
                                print(f"不是日期選單，跳過: {date_texts}")
                    except Exception as e:
                        print(f"日期選擇器 {selector} 失敗: {e}")
                        continue
                
                # 策略2: 智能尋找時間相關的選單
                print("=== 策略2: 智能尋找時間選單 ===")
                
                time_selectors = [
                    'select[name*="time"]',
                    'select[name*="時間"]',
                    'select[name*="hour"]',
                    'select[name*="小時"]',
                    'select[id*="time"]',
                    'select[id*="時間"]',
                    'select[id*="hour"]',
                    'select:has(option[value="16"])',     # 包含16小時的選單
                    'select:has(option[text*="16"])',     # 包含16的選單
                ]
                
                for selector in time_selectors:
                    try:
                        time_select = driver['page'].locator(selector).first
                        if time_select.count() > 0 and time_select.is_visible():
                            print(f"檢查潛在時間選單: {selector}")
                            
                            # 獲取選項並驗證是否真的是時間選單
                            time_options = time_select.locator('option').all()
                            time_texts = [opt.text_content() or '' for opt in time_options if opt.text_content()]
                            print(f"選項內容: {time_texts}")
                            
                            # 驗證：排除地點選單
                            location_keywords = ['住家', '醫療院所', '醫院', '診所', '衛生所', '車站', '捷運']
                            is_location_menu = any(keyword in ' '.join(time_texts) for keyword in location_keywords)
                            
                            if is_location_menu:
                                print(f"跳過地點選單: {time_texts}")
                                continue
                            
                            # 驗證：排除日期選單（精確排除）
                            date_indicators = ['2024', '2025', '/', '月', '日', '今天', '明天']
                            is_date_menu = any(indicator in ' '.join(time_texts) for indicator in date_indicators)
                            
                            if is_date_menu:
                                print(f"跳過日期選單: {time_texts}")
                                continue
                            
                            # 驗證：確認為純時間選單（只包含小時，不包含日期）
                            has_hour_format = False
                            for text in time_texts:
                                # 檢查是否包含明顯的小時標示
                                if text.endswith('時') and text[:-1].isdigit():
                                    has_hour_format = True
                                    break
                                # 檢查是否包含時間符號
                                if ':' in text and len(text) <= 5:  # 如 "16:00"
                                    has_hour_format = True
                                    break
                                # 檢查是否為典型的小時格式（8-19的營業時間，且不是標準分鐘格式）
                                if text.isdigit():
                                    hour_val = int(text)
                                    if hour_val >= 8 and hour_val <= 19:  # 典型的營業時間範圍
                                        # 檢查是否不是標準分鐘（分鐘應該都是5的倍數且<=55）
                                        if hour_val % 5 != 0 or hour_val > 55:
                                            has_hour_format = True
                                            break
                            
                            if has_hour_format and len(time_texts) > 1:
                                print(f"✅ 確認為時間選單: {time_texts}")
                                
                                # 精確尋找16點時間
                                target_time = None
                                for time_text in time_texts:
                                    # 精確匹配16，避免選到04、14等
                                    if '16' in time_text:
                                        target_time = time_text
                                        print(f"找到精確的16點選項: {time_text}")
                                        break
                                
                                # 如果找不到16點，選擇一個可用時間
                                if not target_time:
                                    valid_times = [t for t in time_texts if t.strip() and t != '請選擇']
                                    if valid_times:
                                        target_time = valid_times[0]  # 選擇第一個可用時間
                                        print(f"找不到16點，選擇第一個可用時間: {target_time}")
                                
                                if target_time:
                                    print(f"選擇時間: {target_time}")
                                    time_select.select_option(target_time)
                                    driver['page'].wait_for_timeout(1000)
                                    
                                    # 驗證選擇
                                    new_value = time_select.input_value()
                                    if new_value and new_value != '請選擇':
                                        print(f"✅ 時間選擇成功: {new_value}")
                                        break
                            else:
                                print(f"不是時間選單，跳過: {time_texts}")
                    except Exception as e:
                        print(f"時間選擇器 {selector} 失敗: {e}")
                        continue
                
                # 策略3: 智能尋找分鐘選單
                print("=== 策略3: 智能尋找分鐘選單 ===")
                
                minute_selectors = [
                    'select[name*="minute"]',
                    'select[name*="分鐘"]',
                    'select[name*="分"]',
                    'select[id*="minute"]',
                    'select[id*="分鐘"]',
                    'select:has(option[value="40"])',     # 包含40分鐘的選單
                    'select:has(option[text*="40"])',     # 包含40的選單
                ]
                
                for selector in minute_selectors:
                    try:
                        minute_select = driver['page'].locator(selector).first
                        if minute_select.count() > 0 and minute_select.is_visible():
                            print(f"檢查潛在分鐘選單: {selector}")
                            
                            # 獲取選項並驗證是否真的是分鐘選單
                            minute_options = minute_select.locator('option').all()
                            minute_texts = [opt.text_content() or '' for opt in minute_options if opt.text_content()]
                            print(f"選項內容: {minute_texts}")
                            
                            # 驗證：排除地點選單
                            location_keywords = ['住家', '醫療院所', '醫院', '診所', '衛生所', '車站', '捷運']
                            is_location_menu = any(keyword in ' '.join(minute_texts) for keyword in location_keywords)
                            
                            if is_location_menu:
                                print(f"跳過地點選單: {minute_texts}")
                                continue
                            
                            # 驗證：排除日期選單（精確排除）
                            date_indicators = ['2024', '2025', '/', '月', '日', '今天', '明天']
                            is_date_menu = any(indicator in ' '.join(minute_texts) for indicator in date_indicators)
                            
                            if is_date_menu:
                                print(f"跳過日期選單: {minute_texts}")
                                continue
                            
                            # 驗證：排除時間選單（小時格式）
                            has_hour_format = False
                            for text in minute_texts:
                                # 檢查是否包含明顯的小時標示
                                if text.endswith('時') and text[:-1].isdigit():
                                    has_hour_format = True
                                    break
                                # 檢查是否包含時間符號
                                if ':' in text and len(text) <= 5:
                                    has_hour_format = True
                                    break
                                # 檢查是否為典型的小時格式（特定的小時值：8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19）
                                if text.isdigit():
                                    hour_val = int(text)
                                    if hour_val >= 8 and hour_val <= 19:  # 典型的營業時間範圍
                                        # 但要確保不是分鐘（分鐘應該都是5的倍數）
                                        if hour_val % 5 != 0 or hour_val > 55:
                                            has_hour_format = True
                                            break
                            
                            if has_hour_format:
                                print(f"跳過時間選單: {minute_texts}")
                                continue
                            
                            # 驗證：確認為純分鐘選單（00, 05, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55）
                            has_minute_format = False
                            for text in minute_texts:
                                # 檢查是否為標準分鐘格式
                                if text.isdigit():
                                    minute_val = int(text)
                                    if 0 <= minute_val <= 59 and minute_val % 5 == 0:  # 標準分鐘間隔
                                        has_minute_format = True
                                        break
                                # 檢查是否包含「分」字
                                if text.endswith('分') and text[:-1].isdigit():
                                    has_minute_format = True
                                    break
                            
                            if has_minute_format and len(minute_texts) > 1:
                                print(f"✅ 確認為分鐘選單: {minute_texts}")
                                
                                # 尋找40分或接近的分鐘
                                target_minute = None
                                for minute_text in minute_texts:
                                    if '40' in minute_text:
                                        target_minute = minute_text
                                        print(f"找到40分選項: {minute_text}")
                                        break
                                
                                # 如果找不到40分，選擇第一個可用分鐘
                                if not target_minute:
                                    valid_minutes = [m for m in minute_texts if m.strip() and m != '請選擇']
                                    if valid_minutes:
                                        target_minute = valid_minutes[0]
                                        print(f"找不到40分，選擇第一個可用分鐘: {target_minute}")
                                
                                if target_minute:
                                    print(f"選擇分鐘: {target_minute}")
                                    minute_select.select_option(target_minute)
                                    driver['page'].wait_for_timeout(1000)
                                    
                                    # 驗證選擇
                                    new_value = minute_select.input_value()
                                    if new_value and new_value != '請選擇':
                                        print(f"✅ 分鐘選擇成功: {new_value}")
                                        break
                            else:
                                print(f"不是分鐘選單，跳過: {minute_texts}")
                    except Exception as e:
                        print(f"分鐘選擇器 {selector} 失敗: {e}")
                        continue
                
                # 策略4: 強化的序號方法（主要策略）
                print("=== 策略4: 強化序號方法 ===")
                
                # 等待並重新獲取選單
                driver['page'].wait_for_timeout(1000)
                all_selects_fresh = driver['page'].locator('select').all()
                print(f"重新掃描到 {len(all_selects_fresh)} 個選單")
                
                # 詳細檢查每個選單的當前狀態
                for i, select_elem in enumerate(all_selects_fresh):
                    try:
                        if select_elem.is_visible():
                            options = select_elem.locator('option').all()
                            option_texts = [opt.text_content() or '' for opt in options if opt.text_content()]
                            current_value = select_elem.input_value() or ''
                            print(f"選單{i}: 當前值='{current_value}', 選項數={len(option_texts)}")
                    except:
                        continue
                
                if len(all_selects_fresh) >= 1:
                    print("開始按序號方法選擇...")
                    
                    # 第1步：智能找到真正的日期選單
                    try:
                        print("第1步：🎯 基於成功日誌直接使用選單4（日期選單）")
                        
                        date_select = None
                        date_select_index = 4
                        
                        # 直接使用第4個選單（基於日誌分析）
                        if len(all_selects_fresh) > 4:
                            select_elem = all_selects_fresh[4]
                            if select_elem.is_visible():
                                options = select_elem.locator('option').all()
                                option_texts = [opt.text_content() or '' for opt in options if opt.text_content()]
                                print(f"✅ 找到日期選單 4: {option_texts}")
                                date_select = select_elem
                            else:
                                print("選單4不可見，退回到智能搜尋...")
                                # 退回到智能搜尋
                                for i, select_elem in enumerate(all_selects_fresh):
                                    if not select_elem.is_visible():
                                        continue
                                        
                                    options = select_elem.locator('option').all()
                                    option_texts = [opt.text_content() or '' for opt in options if opt.text_content()]
                                    print(f"檢查選單 {i}: {option_texts}")
                                    
                                    # 排除地點選單
                                    location_keywords = ['住家', '醫療院所', '醫院', '診所', '衛生所', '車站', '捷運']
                                    is_location_menu = any(keyword in ' '.join(option_texts) for keyword in location_keywords)
                                    
                                    if is_location_menu:
                                        print(f"跳過地點選單 {i}: {option_texts}")
                                        continue
                                    
                                    # 檢查是否為日期選單
                                    date_keywords = ['2024', '2025', '月', '日', '/', '-', '今天', '明天']
                                    has_date_content = any(keyword in ' '.join(option_texts) for keyword in date_keywords)
                                    
                                    if has_date_content and len(option_texts) > 1:
                                        print(f"✅ 找到日期選單 {i}: {option_texts}")
                                        date_select = select_elem
                                        date_select_index = i
                                        break
                        else:
                            print(f"選單總數不足5個（當前{len(all_selects_fresh)}個），退回到智能搜尋...")
                            # 退回到智能搜尋
                            for i, select_elem in enumerate(all_selects_fresh):
                                if not select_elem.is_visible():
                                    continue
                                    
                                options = select_elem.locator('option').all()
                                option_texts = [opt.text_content() or '' for opt in options if opt.text_content()]
                                print(f"檢查選單 {i}: {option_texts}")
                                
                                # 排除地點選單
                                location_keywords = ['住家', '醫療院所', '醫院', '診所', '衛生所', '車站', '捷運']
                                is_location_menu = any(keyword in ' '.join(option_texts) for keyword in location_keywords)
                                
                                if is_location_menu:
                                    print(f"跳過地點選單 {i}: {option_texts}")
                                    continue
                                
                                # 檢查是否為日期選單
                                date_keywords = ['2024', '2025', '月', '日', '/', '-', '今天', '明天']
                                has_date_content = any(keyword in ' '.join(option_texts) for keyword in date_keywords)
                                
                                if has_date_content and len(option_texts) > 1:
                                    print(f"✅ 找到日期選單 {i}: {option_texts}")
                                    date_select = select_elem
                                    date_select_index = i
                                    break
                        
                        if date_select and date_select.is_visible():
                            options = date_select.locator('option').all()
                            option_texts = [opt.text_content() or '' for opt in options if opt.text_content()]
                            print(f"日期選單選項: {option_texts}")
                            
                            if len(options) > 1:  # 有選項可選
                                # 🎯 方法0: 基於日誌優化，使用select_option選擇最後選項（跳過容易失敗的click方法）
                                try:
                                    valid_options = [opt for opt in option_texts if opt.strip() and opt != '請選擇']
                                    if valid_options:
                                        target_date = valid_options[-1]
                                        print(f"嘗試選擇最後日期: {target_date}")
                                        date_select.select_option(target_date)
                                        driver['page'].wait_for_timeout(1000)
                                        new_value = date_select.input_value()
                                        print(f"✅ 序號方法0：選擇最後日期成功，值: '{new_value}'")
                                    else:
                                        print("沒有有效的日期選項")
                                except Exception as e:
                                    print(f"方法0失敗: {e}")
                                    
                                    # 方法1: 點擊最後一個選項（備用）
                                    try:
                                        last_option = options[-1]
                                        last_option.click()
                                        driver['page'].wait_for_timeout(1000)
                                        new_value = date_select.input_value()
                                        print(f"✅ 序號方法1：點擊最後日期成功，值: '{new_value}'")
                                    except Exception as e:
                                        print(f"方法1也失敗: {e}")
                        else:
                            print("未找到有效的日期選單")
                    except Exception as e:
                        print(f"序號方法選擇日期失敗: {e}")
                    
                    # 第2步：智能找到真正的時間選單
                    try:
                        print("第2步：智能尋找時間選單（排除地點選單）")
                        
                        time_select = None
                        time_select_index = -1
                        
                        # 遍歷所有選單，找到真正的時間選單
                        for i, select_elem in enumerate(all_selects_fresh):
                            if not select_elem.is_visible():
                                continue
                                
                            options = select_elem.locator('option').all()
                            option_texts = [opt.text_content() or '' for opt in options if opt.text_content()]
                            print(f"檢查時間選單 {i}: {option_texts}")
                            
                            # 排除地點選單
                            location_keywords = ['住家', '醫療院所', '醫院', '診所', '衛生所', '車站', '捷運']
                            is_location_menu = any(keyword in ' '.join(option_texts) for keyword in location_keywords)
                            
                            if is_location_menu:
                                print(f"跳過地點選單 {i}: {option_texts}")
                                continue
                            
                            # 排除日期選單（精確排除）
                            date_indicators = ['2024', '2025', '/', '月', '日', '今天', '明天']
                            is_date_menu = any(indicator in ' '.join(option_texts) for indicator in date_indicators)
                            
                            if is_date_menu:
                                print(f"跳過日期選單 {i}: {option_texts}")
                                continue
                            
                            # 檢查是否為純時間選單（只包含小時，不包含日期）
                            has_hour_format = False
                            for text in option_texts:
                                # 檢查是否包含明顯的小時標示
                                if text.endswith('時') and text[:-1].isdigit():
                                    has_hour_format = True
                                    break
                                # 檢查是否包含時間符號
                                if ':' in text and len(text) <= 5:  # 如 "16:00"
                                    has_hour_format = True
                                    break
                                # 檢查是否為典型的小時格式（8-19的營業時間，且不是標準分鐘格式）
                                if text.isdigit():
                                    hour_val = int(text)
                                    if hour_val >= 8 and hour_val <= 19:  # 典型的營業時間範圍
                                        # 檢查是否不是標準分鐘（分鐘應該都是5的倍數且<=55）
                                        if hour_val % 5 != 0 or hour_val > 55:
                                            has_hour_format = True
                                            break
                            
                            if has_hour_format and len(option_texts) > 1:
                                print(f"✅ 找到時間選單 {i}: {option_texts}")
                                time_select = select_elem
                                time_select_index = i
                                break
                        
                        if time_select and time_select.is_visible():
                            options = time_select.locator('option').all()
                            option_texts = [opt.text_content() or '' for opt in options if opt.text_content()]
                            option_values = [opt.get_attribute('value') or '' for opt in options]
                            print(f"時間選單選項: {option_texts}")
                            print(f"時間選單值: {option_values}")
                            
                            # 嘗試多種方法選擇16
                            success = False
                            
                            # 方法1: 直接用值'16'
                            try:
                                time_select.select_option('16')
                                driver['page'].wait_for_timeout(1000)
                                new_value = time_select.input_value()
                                if '16' in str(new_value):
                                    print(f"✅ 時間方法1成功，值: '{new_value}'")
                                    success = True
                            except Exception as e:
                                print(f"時間方法1失敗: {e}")
                            
                            # 方法2: 精確尋找包含16的選項文字
                            if not success:
                                try:
                                    for i, text in enumerate(option_texts):
                                        # 精確匹配16，確保不會選到04、14等
                                        if '16' in text and not any(x in text for x in ['04', '14', '24']):
                                            print(f"找到精確的16點選項: '{text}'")
                                            time_select.select_option(text)
                                            driver['page'].wait_for_timeout(1000)
                                            new_value = time_select.input_value()
                                            print(f"✅ 時間方法2成功，選擇: '{text}', 值: '{new_value}'")
                                            success = True
                                            break
                                except Exception as e:
                                    print(f"時間方法2失敗: {e}")
                            
                            # 方法3: 使用索引選擇（也要精確匹配16）
                            if not success:
                                try:
                                    for i, text in enumerate(option_texts):
                                        # 精確匹配16，確保不會選到04、14等
                                        if '16' in text and not any(x in text for x in ['04', '14', '24']):
                                            print(f"用索引選擇精確的16點選項: '{text}' (索引{i})")
                                            time_select.select_option(index=i)
                                            driver['page'].wait_for_timeout(1000)
                                            new_value = time_select.input_value()
                                            print(f"✅ 時間方法3成功，索引: {i}, 值: '{new_value}'")
                                            success = True
                                            break
                                except Exception as e:
                                    print(f"時間方法3失敗: {e}")
                            
                            # 方法4: 如果還是沒找到16，顯示警告但繼續
                            if not success:
                                print("⚠️ 警告：未能找到16點選項，可能時間格式不同")
                                print(f"可用時間選項: {option_texts}")
                                print(f"可用時間值: {option_values}")
                                
                                # 嘗試通過值來匹配16
                                for i, value in enumerate(option_values):
                                    if '16' in str(value):
                                        try:
                                            print(f"嘗試通過值選擇16: value='{value}'")
                                            time_select.select_option(value=value)
                                            driver['page'].wait_for_timeout(1000)
                                            new_value = time_select.input_value()
                                            print(f"✅ 時間方法4成功，通過值選擇: '{new_value}'")
                                            success = True
                                            break
                                        except Exception as e:
                                            print(f"通過值選擇失敗: {e}")
                                            continue
                        else:
                            print("未找到有效的時間選單")
                    except Exception as e:
                        print(f"序號方法選擇時間失敗: {e}")
                    
                    # 第3步：智能找到真正的分鐘選單
                    try:
                        print("第3步：智能尋找分鐘選單（排除地點選單）")
                        
                        minute_select = None
                        minute_select_index = -1
                        
                        # 遍歷所有選單，找到真正的分鐘選單
                        for i, select_elem in enumerate(all_selects_fresh):
                            if not select_elem.is_visible():
                                continue
                                
                            options = select_elem.locator('option').all()
                            option_texts = [opt.text_content() or '' for opt in options if opt.text_content()]
                            print(f"檢查分鐘選單 {i}: {option_texts}")
                            
                            # 排除地點選單
                            location_keywords = ['住家', '醫療院所', '醫院', '診所', '衛生所', '車站', '捷運']
                            is_location_menu = any(keyword in ' '.join(option_texts) for keyword in location_keywords)
                            
                            if is_location_menu:
                                print(f"跳過地點選單 {i}: {option_texts}")
                                continue
                            
                            # 排除日期選單（精確排除）
                            date_indicators = ['2024', '2025', '/', '月', '日', '今天', '明天']
                            is_date_menu = any(indicator in ' '.join(option_texts) for indicator in date_indicators)
                            
                            if is_date_menu:
                                print(f"跳過日期選單 {i}: {option_texts}")
                                continue
                            
                            # 排除時間選單（小時格式）
                            has_hour_format = False
                            for text in option_texts:
                                # 檢查是否包含明顯的小時標示
                                if text.endswith('時') and text[:-1].isdigit():
                                    has_hour_format = True
                                    break
                                # 檢查是否包含時間符號
                                if ':' in text and len(text) <= 5:
                                    has_hour_format = True
                                    break
                                # 檢查是否為典型的小時格式（8-19的營業時間，且不是標準分鐘格式）
                                if text.isdigit():
                                    hour_val = int(text)
                                    if hour_val >= 8 and hour_val <= 19:  # 典型的營業時間範圍
                                        # 檢查是否不是標準分鐘（分鐘應該都是5的倍數且<=55）
                                        if hour_val % 5 != 0 or hour_val > 55:
                                            has_hour_format = True
                                            break
                            
                            if has_hour_format:
                                print(f"跳過時間選單 {i}: {option_texts}")
                                continue
                            
                            # 檢查是否為純分鐘選單（00, 05, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55）
                            has_minute_format = False
                            for text in option_texts:
                                # 檢查是否為標準分鐘格式
                                if text.isdigit():
                                    minute_val = int(text)
                                    if 0 <= minute_val <= 59 and minute_val % 5 == 0:  # 標準分鐘間隔
                                        has_minute_format = True
                                        break
                                # 檢查是否包含「分」字
                                if text.endswith('分') and text[:-1].isdigit():
                                    has_minute_format = True
                                    break
                            
                            if has_minute_format and len(option_texts) > 1:
                                print(f"✅ 找到分鐘選單 {i}: {option_texts}")
                                minute_select = select_elem
                                minute_select_index = i
                                break
                        
                        if minute_select and minute_select.is_visible():
                            options = minute_select.locator('option').all()
                            option_texts = [opt.text_content() or '' for opt in options if opt.text_content()]
                            option_values = [opt.get_attribute('value') or '' for opt in options]
                            print(f"分鐘選單選項: {option_texts}")
                            print(f"分鐘選單值: {option_values}")
                            
                            # 嘗試多種方法選擇40
                            success = False
                            
                            # 方法1: 直接用值'40'
                            try:
                                minute_select.select_option('40')
                                driver['page'].wait_for_timeout(1000)
                                new_value = minute_select.input_value()
                                if '40' in str(new_value):
                                    print(f"✅ 分鐘方法1成功，值: '{new_value}'")
                                    success = True
                            except Exception as e:
                                print(f"分鐘方法1失敗: {e}")
                            
                            # 方法2: 尋找包含40的選項文字
                            if not success:
                                try:
                                    for i, text in enumerate(option_texts):
                                        if '40' in text:
                                            minute_select.select_option(text)
                                            driver['page'].wait_for_timeout(1000)
                                            new_value = minute_select.input_value()
                                            print(f"✅ 分鐘方法2成功，選擇: '{text}', 值: '{new_value}'")
                                            success = True
                                            break
                                except Exception as e:
                                    print(f"分鐘方法2失敗: {e}")
                            
                            # 方法3: 使用索引選擇
                            if not success:
                                try:
                                    for i, text in enumerate(option_texts):
                                        if '40' in text:
                                            minute_select.select_option(index=i)
                                            driver['page'].wait_for_timeout(1000)
                                            new_value = minute_select.input_value()
                                            print(f"✅ 分鐘方法3成功，索引: {i}, 值: '{new_value}'")
                                            break
                                except Exception as e:
                                    print(f"分鐘方法3失敗: {e}")
                        else:
                            print("未找到有效的分鐘選單")
                    except Exception as e:
                        print(f"序號方法選擇分鐘失敗: {e}")
                
                print("序號方法執行完成")
                
                datetime_success = True
                print("✅ 日期時段選擇完成")
                
            except Exception as e:
                print(f"日期時段選擇失敗: {e}")
                datetime_success = False
            
            take_screenshot("datetime_selected")
            
            # 10. 於預約時間前後30分鐘到達 選擇「不同意」
            print("=== 第10步：選擇不同意前後30分鐘到達 ===")
            
            # 等待頁面穩定
            driver['page'].wait_for_timeout(1500)
            
            try:
                # 先向下捲動頁面，確保不同意按鈕可見
                print("向下捲動頁面尋找不同意按鈕...")
                driver['page'].evaluate("window.scrollBy(0, 300)")
                driver['page'].wait_for_timeout(1000)
                take_screenshot("after_scroll_disagree")
                
                # 🥇 基於成功日誌優化的不同意選擇器順序
                disagree_selectors = [
                    # 🥇 最有效的方法 - 快速識別不浪費時間
                    'input[value="不同意"]',
                    'button:has-text("不同意")',
                    '[type="radio"][value="不同意"]',
                    
                    # 🥈 備用方法
                    'label:has-text("不同意")',
                    '[type="radio"][value*="不同意"]',
                    '[name*="agree"]:not([value*="同意"])',
                    'input[type="radio"]:has-text("不同意")',
                    
                    # 🔄 最後備案 - 容易timeout的放最後
                    'text=不同意',
                ]
                
                clicked = False
                for selector in disagree_selectors:
                    try:
                        # 🥇 快速檢查元素是否存在，避免長時間等待
                        elements = driver['page'].locator(selector).all()
                        if len(elements) > 0:
                            element = elements[0]
                            if element.is_visible():
                                print(f"找到不同意按鈕，選擇器: {selector}")
                                # 確保按鈕在視窗內
                                element.scroll_into_view_if_needed()
                                driver['page'].wait_for_timeout(500)
                                element.click()
                                print(f"✅ 使用選擇器 {selector} 點擊不同意成功")
                                clicked = True
                                break
                    except Exception as e:
                        print(f"選擇器 {selector} 失敗: {e}")
                        continue
                
                # 如果還是找不到，嘗試更廣泛的搜尋
                if not clicked:
                    print("⚠️ 直接方法失敗，嘗試智能遍歷所有radio按鈕...")
                    
                    # 最後手段：檢查所有radio按鈕
                    radio_buttons = driver['page'].locator('input[type="radio"]').all()
                    for i, radio in enumerate(radio_buttons):
                        try:
                            if radio.is_visible():
                                value = radio.get_attribute('value') or ''
                                name = radio.get_attribute('name') or ''
                                print(f"Radio {i}: name='{name}', value='{value}'")
                                
                                # 如果value包含拒絕相關詞彙
                                if any(word in value.lower() for word in ['不同意', '否', 'no', 'disagree']):
                                    radio.scroll_into_view_if_needed()
                                    driver['page'].wait_for_timeout(300)
                                    radio.click()
                                    print(f"✅ 點擊radio按鈕 {i} (value='{value}') 成功")
                                    clicked = True
                                    break
                        except Exception as e:
                            print(f"檢查radio {i} 失敗: {e}")
                            continue
                
                if not clicked:
                    print("⚠️ 所有方法都失敗，可能不同意已經是預設值或該選項不存在")
                    
            except Exception as e:
                print(f"選擇不同意選項失敗: {e}")
            
            take_screenshot("time_window")
            
            # 11. 陪同人數 選擇「1人(免費)」
            print("=== 第11步：選擇陪同人數 1人(免費) ===")
            
            # 等待頁面響應
            driver['page'].wait_for_timeout(1000)
            
            try:
                # 智能尋找陪同人數選單
                companion_selectors = [
                    'select[name*="companion"]',
                    'select[name*="陪同"]',
                    'select[name*="人數"]',
                    'select[id*="companion"]',
                    'select[id*="陪同"]',
                    'select:has(option[text*="1人(免費)"])',
                    'select:has(option[text*="免費"])',
                ]
                
                companion_selected = False
                
                for selector in companion_selectors:
                    try:
                        select_elem = driver['page'].locator(selector).first
                        if select_elem.count() > 0 and select_elem.is_visible():
                            # 檢查選項
                            options = select_elem.locator('option').all()
                            option_texts = [opt.text_content() or '' for opt in options if opt.text_content()]
                            print(f"找到陪同人數選單，選項: {option_texts}")
                            
                            # 嘗試選擇1人(免費)
                            if '1人(免費)' in option_texts:
                                select_elem.select_option('1人(免費)')
                                driver['page'].wait_for_timeout(1000)
                                
                                # 驗證選擇
                                new_value = select_elem.input_value()
                                print(f"✅ 陪同人數選擇成功，值: '{new_value}'")
                                companion_selected = True
                                break
                            else:
                                print(f"選單中沒有1人(免費)選項: {option_texts}")
                    except Exception as e:
                        print(f"陪同人數選擇器 {selector} 失敗: {e}")
                        continue
                
                # 如果智能方法失敗，謹慎使用備用方法
                if not companion_selected:
                    print("智能方法失敗，嘗試備用方法...")
                    
                    # 獲取所有選單並謹慎選擇
                    all_selects = driver['page'].locator('select').all()
                    print(f"頁面上有 {len(all_selects)} 個選單")
                    
                    for i, select_elem in enumerate(all_selects):
                        try:
                            if select_elem.is_visible():
                                options = select_elem.locator('option').all()
                                option_texts = [opt.text_content() or '' for opt in options if opt.text_content()]
                                name = select_elem.get_attribute('name') or ''
                                id_attr = select_elem.get_attribute('id') or ''
                                
                                print(f"選單 {i}: name='{name}', id='{id_attr}', 選項={option_texts}")
                                
                                # 只處理包含陪同相關選項的選單
                                if '1人(免費)' in option_texts or any('免費' in opt for opt in option_texts):
                                    print(f"選單 {i} 看起來是陪同人數選單，嘗試選擇...")
                                    select_elem.select_option('1人(免費)')
                                    driver['page'].wait_for_timeout(1000)
                                    
                                    new_value = select_elem.input_value()
                                    print(f"✅ 備用方法成功，選單 {i} 選擇陪同人數: '{new_value}'")
                                    companion_selected = True
                                    break
                        except Exception as e:
                            print(f"檢查選單 {i} 失敗: {e}")
                            continue
                
                if not companion_selected:
                    print("⚠️ 陪同人數選擇失敗，繼續執行...")
                    
            except Exception as e:
                print(f"陪同人數選擇過程失敗: {e}")
            
            take_screenshot("companion")
            
            # 12. 同意共乘 選擇「否」
            print("=== 第12步：選擇不同意共乘 ===")
            
            try:
                # 先向下捲動確保按鈕可見
                print("向下捲動頁面尋找共乘選項...")
                driver['page'].evaluate("window.scrollBy(0, 300)")
                driver['page'].wait_for_timeout(1000)
                
                # 🥇 基於成功日誌優化的共乘選擇器順序
                carpool_selectors = [
                    # 🥇 最有效的方法 - 快速識別不浪費時間
                    'input[value="否"]',
                    'button:has-text("否")',
                    '[type="radio"][value="否"]',
                    '[type="radio"][value="no"]',
                    
                    # 🥈 備用方法
                    'label:has-text("否")',
                    
                    # 🔄 最後備案 - 容易timeout的放最後
                    'text=否',
                ]
                
                clicked = False
                for selector in carpool_selectors:
                    try:
                        # 🥇 快速檢查元素是否存在，避免長時間等待
                        elements = driver['page'].locator(selector).all()
                        if len(elements) > 0:
                            element = elements[0]
                            if element.is_visible():
                                print(f"找到共乘「否」按鈕，選擇器: {selector}")
                                element.scroll_into_view_if_needed()
                                driver['page'].wait_for_timeout(500)
                                element.click()
                                print(f"✅ 點擊共乘「否」成功")
                                clicked = True
                                break
                    except Exception as e:
                        print(f"共乘選擇器 {selector} 失敗: {e}")
                        continue
                
                if not clicked:
                    print("⚠️ 未找到共乘「否」選項，可能已經是預設值")
                    
            except Exception as e:
                print(f"選擇共乘「否」失敗: {e}")
                
            take_screenshot("carpool")
            
            # 13. 搭乘輪椅上車 選擇「是」
            print("=== 第13步：選擇搭乘輪椅上車：是 ===")
            
            try:
                # 向下捲動確保按鈕可見
                driver['page'].evaluate("window.scrollBy(0, 300)")
                driver['page'].wait_for_timeout(1000)
                take_screenshot("before_wheelchair_selection")
                
                clicked = False
                
                # 🎯 策略0：使用精確CSS選擇器（基於網頁trace結果）
                try:
                    print("🎯 策略0：使用精確CSS選擇器...")
                    
                    # 直接使用trace到的精確選擇器
                    precise_selector = '.form_item:nth-child(11) .cus_checkbox_type1:nth-child(1) > div'
                    
                    element = driver['page'].locator(precise_selector).first
                    if element.count() > 0:
                        print(f"找到精確的輪椅上車「是」按鈕: {precise_selector}")
                        element.scroll_into_view_if_needed()
                        driver['page'].wait_for_timeout(500)
                        element.click()
                        driver['page'].wait_for_timeout(1000)
                        
                        print("✅ 策略0成功：精確CSS選擇器")
                        clicked = True
                    else:
                        print("❌ 精確選擇器未找到元素")
                
                except Exception as e:
                    print(f"❌ 策略0執行失敗: {e}")

                # 最終驗證
                if clicked:
                    take_screenshot("after_wheelchair_selection_success")
                    print("✅ 搭乘輪椅上車選擇「是」成功")
                else:
                    print("❌ 輪椅選擇失敗")
                    take_screenshot("wheelchair_selection_failed")
            
            except Exception as e:
                print(f"選擇搭乘輪椅上車失敗: {e}")
                take_screenshot("wheelchair_selection_error")
            
            take_screenshot("wheelchair")
            
            # 14. 大型輪椅 選擇「否」
            print("=== 第14步：選擇大型輪椅：否 ===")
            
            try:
                # 向下捲動確保按鈕可見
                driver['page'].evaluate("window.scrollBy(0, 300)")
                driver['page'].wait_for_timeout(1000)
                take_screenshot("before_large_wheelchair_selection")
                
                clicked = False
                
                # 🎯 策略0：使用精確CSS選擇器（基於網頁trace結果）
                try:
                    print("🎯 策略0：使用精確CSS選擇器...")
                    
                    # 直接使用trace到的精確選擇器
                    precise_selector = '.form_item:nth-child(12) .cus_checkbox_type1:nth-child(2) > div'
                    
                    element = driver['page'].locator(precise_selector).first
                    if element.count() > 0:
                        print(f"找到精確的大型輪椅「否」按鈕: {precise_selector}")
                        element.scroll_into_view_if_needed()
                        driver['page'].wait_for_timeout(500)
                        element.click()
                        driver['page'].wait_for_timeout(1000)
                        
                        print("✅ 策略0成功：精確CSS選擇器")
                        clicked = True
                    else:
                        print("❌ 精確選擇器未找到元素")
                
                except Exception as e:
                    print(f"❌ 策略0執行失敗: {e}")
                
                if clicked:
                    print("✅ 大型輪椅「否」選擇成功")
                    take_screenshot("after_large_wheelchair_selection_success")
                else:
                    print("❌ 大型輪椅選擇失敗")
                    take_screenshot("large_wheelchair_selection_failed")
                
            except Exception as e:
                print(f"選擇大型輪椅「否」失敗: {e}")
                
            take_screenshot("large_wheelchair")
            
            # 15. 點擊「下一步，確認預約資訊」
            print("=== 第15步：點擊下一步，確認預約資訊 ===")
            
            try:
                # 向下捲動確保按鈕可見
                driver['page'].evaluate("window.scrollBy(0, 300)")
                driver['page'].wait_for_timeout(1000)
                
                next_selectors = [
                    'text=下一步，確認預約資訊',
                    'button:has-text("下一步")',
                    'input[value*="下一步"]',
                    '[type="submit"]:has-text("下一步")',
                    'button:has-text("確認預約資訊")'
                ]
                
                clicked = False
                for selector in next_selectors:
                    try:
                        element = driver['page'].locator(selector).first
                        if element.count() > 0 and element.is_visible():
                            print(f"找到下一步按鈕，選擇器: {selector}")
                            element.scroll_into_view_if_needed()
                            driver['page'].wait_for_timeout(500)
                            element.click()
                            print(f"✅ 點擊下一步成功")
                            clicked = True
                            break
                    except Exception as e:
                        print(f"下一步選擇器 {selector} 失敗: {e}")
                        continue
                
                if not clicked:
                    print("⚠️ 未找到下一步按鈕")
                else:
                    driver['page'].wait_for_load_state("networkidle")
                    
            except Exception as e:
                print(f"點擊下一步失敗: {e}")
                
            take_screenshot("confirm_info")
            
            # 16. 點擊「送出預約」
            print("=== 第16步：點擊送出預約 ===")
            
            try:
                # 等待頁面載入
                driver['page'].wait_for_timeout(2000)
                
                # 向下捲動確保按鈕可見
                driver['page'].evaluate("window.scrollBy(0, 300)")
                driver['page'].wait_for_timeout(1000)
                
                submit_selectors = [
                    'text=送出預約',
                    'button:has-text("送出預約")',
                    'input[value*="送出預約"]',
                    '[type="submit"]:has-text("送出")',
                    'button:has-text("送出")',
                    '[type="submit"]'
                ]
                
                clicked = False
                for selector in submit_selectors:
                    try:
                        element = driver['page'].locator(selector).first
                        if element.count() > 0 and element.is_visible():
                            print(f"找到送出預約按鈕，選擇器: {selector}")
                            element.scroll_into_view_if_needed()
                            driver['page'].wait_for_timeout(500)
                            element.click()
                            print(f"✅ 點擊送出預約成功")
                            clicked = True
                            break
                    except Exception as e:
                        print(f"送出預約選擇器 {selector} 失敗: {e}")
                        continue
                
                if not clicked:
                    print("⚠️ 未找到送出預約按鈕")
                else:
                    driver['page'].wait_for_load_state("networkidle")
                    
            except Exception as e:
                print(f"點擊送出預約失敗: {e}")
                
            take_screenshot("submit_reservation")
            
            # 17. 檢查「已完成預約」浮動視窗
            print("=== 第17步：檢查預約完成狀態（浮動視窗） ===")
            
            try:
                # 等待頁面處理完成
                print("等待預約處理完成...")
                driver['page'].wait_for_timeout(3000)
                
                # 拍照記錄當前狀態
                take_screenshot("after_submit_waiting")
                
                # 多種方法檢測預約完成的浮動視窗
                success_detected = False
                
                # 方法1: 檢測浮動視窗選擇器
                modal_selectors = [
                    '.modal:has-text("已完成預約")',
                    '.popup:has-text("已完成預約")',
                    '.dialog:has-text("已完成預約")',
                    '[role="dialog"]:has-text("已完成預約")',
                    '.overlay:has-text("已完成預約")',
                    '.modal-content:has-text("已完成預約")'
                ]
                
                print("檢查浮動視窗...")
                for selector in modal_selectors:
                    try:
                        element = driver['page'].locator(selector).first
                        if element.count() > 0 and element.is_visible():
                            print(f"✅ 找到預約完成浮動視窗: {selector}")
                            success_detected = True
                            break
                    except Exception as e:
                        print(f"浮動視窗選擇器 {selector} 失敗: {e}")
                        continue
                
                # 方法2: 使用 wait_for_selector 等待浮動視窗出現
                if not success_detected:
                    print("等待「已完成預約」文字出現...")
                    try:
                        driver['page'].wait_for_selector('text=已完成預約', timeout=10000)
                        print("✅ 找到「已完成預約」文字")
                        success_detected = True
                    except Exception as e:
                        print(f"等待「已完成預約」文字失敗: {e}")
                
                # 方法3: 檢查所有可見元素中是否包含成功訊息
                if not success_detected:
                    print("檢查所有可見元素...")
                    
                    success_keywords = ['已完成預約', '預約成功', '預約完成', '預約已提交', '預約已送出']
                    
                    for keyword in success_keywords:
                        try:
                            elements = driver['page'].locator(f'*:has-text("{keyword}")').all()
                            print(f"找到 {len(elements)} 個包含「{keyword}」的元素")
                            
                            for i, elem in enumerate(elements):
                                try:
                                    if elem.is_visible():
                                        text = elem.text_content() or ''
                                        print(f"成功元素 {i}: {text[:100]}")
                                        success_detected = True
                                        break
                                except:
                                    continue
                            
                            if success_detected:
                                break
                        except Exception as e:
                            print(f"檢查關鍵字「{keyword}」失敗: {e}")
                            continue
                
                # 方法4: 檢查浮動視窗的常見類別
                if not success_detected:
                    print("檢查常見的浮動視窗類別...")
                    
                    common_modal_classes = [
                        '.modal',
                        '.popup',
                        '.dialog',
                        '.overlay',
                        '.modal-dialog',
                        '.alert',
                        '.notification'
                    ]
                    
                    for class_selector in common_modal_classes:
                        try:
                            modals = driver['page'].locator(class_selector).all()
                            for i, modal in enumerate(modals):
                                try:
                                    if modal.is_visible():
                                        content = modal.text_content() or ''
                                        print(f"浮動視窗 {class_selector}[{i}]: {content[:100]}")
                                        
                                        # 檢查內容是否包含成功訊息
                                        if any(keyword in content for keyword in success_keywords):
                                            print(f"✅ 在 {class_selector}[{i}] 中找到預約成功訊息")
                                            success_detected = True
                                            break
                                except:
                                    continue
                            
                            if success_detected:
                                break
                        except Exception as e:
                            print(f"檢查 {class_selector} 失敗: {e}")
                            continue
                
                # 最終拍照記錄
                if success_detected:
                    print("🎉 預約成功完成！")
                    take_screenshot("reservation_success")
                    return True
                else:
                    print("⚠️ 未檢測到明確的預約完成訊息")
                    take_screenshot("reservation_status_unclear")
                    
                    # 額外等待時間，再次檢查
                    print("額外等待5秒後再次檢查...")
                    driver['page'].wait_for_timeout(5000)
                    take_screenshot("reservation_final_check")
                    
                    # 最後一次嘗試
                    try:
                        final_check = driver['page'].locator('text=已完成預約').first
                        if final_check.count() > 0:
                            print("✅ 最終檢查：找到預約完成訊息")
                            return True
                    except:
                        pass
                    
                    print("⚠️ 最終未能確認預約狀態")
                    return False
                    
            except Exception as e:
                print(f"檢查預約完成狀態失敗: {e}")
                take_screenshot("reservation_check_error")
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
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body { 
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
                margin: 0; 
                padding: 20px; 
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
            }
            .container { 
                max-width: 1200px; 
                margin: 0 auto; 
                background: white; 
                border-radius: 16px; 
                padding: 30px; 
                box-shadow: 0 10px 30px rgba(0,0,0,0.3);
            }
            .header {
                text-align: center;
                margin-bottom: 40px;
                padding-bottom: 20px;
                border-bottom: 3px solid #f0f0f0;
            }
            .header h1 {
                color: #2c3e50;
                margin: 0;
                font-size: 2.5em;
                font-weight: 300;
            }
            .header p {
                color: #7f8c8d;
                margin: 10px 0 0 0;
                font-size: 1.1em;
            }
            .section {
                margin-bottom: 40px;
                padding: 25px;
                border-radius: 12px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            }
            .section-reservation {
                background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);
                border-left: 5px solid #2196f3;
            }
            .section-dispatch {
                background: linear-gradient(135deg, #f3e5f5 0%, #e1bee7 100%);
                border-left: 5px solid #9c27b0;
            }
            .section-logs {
                background: linear-gradient(135deg, #fff3e0 0%, #ffe0b2 100%);
                border-left: 5px solid #ff9800;
            }
            .section h2 {
                margin: 0 0 20px 0;
                font-size: 1.6em;
                font-weight: 500;
            }
            .section-reservation h2 { color: #1976d2; }
            .section-dispatch h2 { color: #7b1fa2; }
            .section-logs h2 { color: #f57c00; }
            .section p {
                margin: 0 0 20px 0;
                color: #5a6c7d;
                line-height: 1.5;
            }
            .buttons {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
                gap: 15px;
            }
            .button { 
                background: white;
                color: #2c3e50;
                padding: 18px 24px; 
                text-align: center; 
                text-decoration: none; 
                display: block; 
                font-size: 16px; 
                font-weight: 500;
                border: 2px solid transparent;
                border-radius: 10px; 
                transition: all 0.3s ease;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            }
            .button:hover {
                transform: translateY(-2px);
                box-shadow: 0 6px 20px rgba(0,0,0,0.15);
            }
            .section-reservation .button:hover {
                border-color: #2196f3;
                background: #e3f2fd;
            }
            .section-dispatch .button:hover {
                border-color: #9c27b0;
                background: #f3e5f5;
            }
            .section-logs .button:hover {
                border-color: #ff9800;
                background: #fff3e0;
            }
            .icon {
                font-size: 1.2em;
                margin-right: 8px;
            }
            .status-bar {
                background: #ecf0f1;
                padding: 15px;
                border-radius: 8px;
                margin-bottom: 30px;
                text-align: center;
                color: #34495e;
            }
            @media (max-width: 768px) {
                .container { 
                    margin: 10px; 
                    padding: 20px; 
                }
                .header h1 { 
                    font-size: 2em; 
                }
                .buttons {
                    grid-template-columns: 1fr;
                }
                .section {
                    padding: 20px;
                }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🚗 長照交通接送預約系統</h1>
                <p>新北市長期照護交通預約服務 - 智能自動化管理平台</p>
            </div>
            
            <div class="status-bar">
                <strong>🕒 排程狀態：</strong>
                每週一、四 00:01（台灣時間）自動執行預約 |
                每週一、四 00:10（台灣時間）自動查詢派車結果
                <span style="color:#888;font-size:0.95em;">（伺服器為 UTC+0，台灣時間為 UTC+8）</span>
            </div>
            
            <!-- 第一區：預約功能 -->
            <div class="section section-reservation">
                <h2><span class="icon">📋</span>預約功能</h2>
                <p>執行長照交通預約作業，包含完整的預約流程和過程記錄</p>
                <div class="buttons">
                    <a href="/reserve" class="button">
                        <span class="icon">🚗</span>開始預約
                    </a>
                    <a href="/screenshots" class="button">
                        <span class="icon">📸</span>查看預約時截圖
                    </a>
                </div>
            </div>
            
            <!-- 第二區：派車查詢 -->
            <div class="section section-dispatch">
                <h2><span class="icon">🔍</span>派車查詢</h2>
                <p>查詢和管理派車結果，提供多種檢視和匯出功能</p>
                <div class="buttons">
                    <a href="/fetch-dispatch" class="button">
                        <span class="icon">🔄</span>抓取派車結果
                    </a>
                    <a href="/latest-dispatch" class="button">
                        <span class="icon">📋</span>看最新派車結果
                    </a>
                    <a href="/dispatch-screenshots" class="button">
                        <span class="icon">🔍</span>查看尋找派車結果截圖
                    </a>
                    <a href="/dispatch-result-file" class="button">
                        <span class="icon">📄</span>查看派車結果本地檔案
                    </a>
                </div>
            </div>
            
            <!-- 第三區：日誌類 -->
            <div class="section section-logs">
                <h2><span class="icon">📊</span>系統日誌</h2>
                <p>監控系統執行狀況，查看排程任務和操作記錄</p>
                <div class="status-bar" style="margin-bottom:18px; background:#f8f9fa; color:#333; font-size:1em;">
                    <strong>📅 目前系統排程：</strong>
                    <ul style="margin:8px 0 0 20px; padding:0; list-style:disc inside; font-size:0.98em;">
                        <li>每週一、四 00:01（台灣時間）自動執行預約</li>
                        <li>每週一、四 00:10（台灣時間）自動查詢派車結果</li>
                        <li>（Zeabur 伺服器為 UTC+0，台灣時間為 UTC+8）</li>
                    </ul>
                </div>
                <div class="buttons">
                    <a href="/cron-logs" class="button">
                        <span class="icon">📊</span>查看預約日誌
                    </a>
                    <a href="/dispatch-cron-logs" class="button">
                        <span class="icon">📈</span>查看派車查詢日誌
                    </a>
                </div>
            </div>
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

@app.route('/dispatch-screenshots')
def dispatch_screenshots():
    """查看尋找派車結果截圖"""
    import os
    import glob
    
    # 獲取所有派車截圖檔案（以 dispatch_ 開頭）
    screenshot_files = glob.glob('dispatch_*.png')
    screenshot_files.sort()
    
    html = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>尋找派車結果截圖</title>
        <meta charset="utf-8">
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
            .container { max-width: 1200px; margin: 0 auto; }
            .header { background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
            .screenshot { margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 8px; background: white; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
            .screenshot img { max-width: 100%; height: auto; border: 1px solid #eee; border-radius: 4px; }
            .screenshot h3 { margin: 5px 0 15px 0; color: #333; font-size: 18px; }
            .back-button { 
                background-color: #2196F3; 
                color: white; 
                padding: 10px 20px; 
                text-decoration: none; 
                border-radius: 4px; 
                display: inline-block; 
                margin-bottom: 20px; 
            }
            .back-button:hover { background-color: #1976D2; }
            .no-screenshots { text-align: center; color: #666; padding: 40px; background: white; border-radius: 8px; }
            .stats { background: #e3f2fd; padding: 15px; border-radius: 8px; margin-bottom: 20px; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <a href="/" class="back-button">返回首頁</a>
                <h1>🔍 尋找派車結果截圖歷程</h1>
                <p>這裡顯示抓取派車結果過程中的所有截圖，幫助了解執行流程和除錯。</p>
            </div>
    '''
    
    if screenshot_files:
        html += f'''
            <div class="stats">
                <strong>📊 統計資訊：</strong>共找到 {len(screenshot_files)} 張派車抓取截圖
            </div>
        '''
        
        for file_path in screenshot_files:
            filename = os.path.basename(file_path)
            # 解析檔名，移除 dispatch_ 前綴和 .png 後綴
            description = filename.replace('.png', '').replace('dispatch_', '').replace('_', ' ')
            
            # 美化描述文字
            description_map = {
                '001 page loaded': '步驟 1: 頁面載入完成',
                '002 page complete': '步驟 2: 頁面完全載入',
                '003 popup closed': '步驟 3: 關閉彈窗',
                '003 no popup found': '步驟 3: 未找到彈窗',
                '004 login form': '步驟 4: 登入表單載入',
                '005 before login click': '步驟 5: 準備點擊登入',
                '006 login clicked': '步驟 6: 登入按鈕已點擊',
                '007 login success modal found': '步驟 7: 發現登入成功彈窗',
                '008 login success confirmed': '步驟 8: 確認登入成功',
                '009 login complete': '步驟 9: 登入流程完成',
                'order query not found': '❌ 未找到訂單查詢按鈕',
                'order list loaded': '✅ 訂單列表載入完成',
                'records found': '🔍 找到訂單記錄',
                'matching record found': '🎯 找到匹配的預約記錄',
                'result saved': '💾 結果已儲存',
                'no matching record': '❌ 未找到匹配記錄',
                'extraction failed': '❌ 信息提取失敗',
                'order query error': '❌ 訂單查詢錯誤',
                'dispatch error': '❌ 派車抓取錯誤'
            }
            
            display_description = description_map.get(description, description.title())
            
            html += f'''
            <div class="screenshot">
                <h3>{display_description}</h3>
                <img src="/screenshot/{filename}" alt="{display_description}" loading="lazy">
            </div>
            '''
    else:
        html += '''
        <div class="no-screenshots">
            <h2>📭 暫無派車抓取截圖</h2>
            <p>目前沒有派車抓取過程的截圖。</p>
            <p>請先執行「🔄 抓取派車結果」功能來生成截圖。</p>
        </div>
        '''
    
    html += '''
        </div>
    </body>
    </html>
    '''
    
    return html

@app.route('/dispatch-result-file')
def dispatch_result_file():
    """查看派車結果本地檔案"""
    import os
    from datetime import datetime
    
    html = '''
    <!DOCTYPE html>
    <html lang="zh-TW">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>派車結果本地檔案</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
            .container { max-width: 1000px; margin: 0 auto; }
            .header { background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
            .content { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
            .back-button { 
                background-color: #2196F3; 
                color: white; 
                padding: 10px 20px; 
                text-decoration: none; 
                border-radius: 4px; 
                display: inline-block; 
                margin-bottom: 20px; 
            }
            .back-button:hover { background-color: #1976D2; }
            .file-content { 
                background: #f8f9fa; 
                border: 1px solid #e9ecef; 
                border-radius: 6px; 
                padding: 20px; 
                font-family: 'Courier New', monospace; 
                white-space: pre-wrap; 
                word-wrap: break-word;
                line-height: 1.6;
            }
            .no-file { 
                text-align: center; 
                color: #666; 
                padding: 40px; 
                background: #fff3cd; 
                border: 1px solid #ffeaa7; 
                border-radius: 8px; 
            }
            .file-info {
                background: #e3f2fd; 
                padding: 15px; 
                border-radius: 8px; 
                margin-bottom: 20px;
                font-size: 14px;
            }
            .controls {
                text-align: center;
                margin-bottom: 20px;
            }
            .btn {
                background-color: #28a745;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 4px;
                cursor: pointer;
                margin: 0 5px;
                text-decoration: none;
                display: inline-block;
            }
            .btn:hover { background-color: #218838; }
            .btn-download { background-color: #17a2b8; }
            .btn-download:hover { background-color: #138496; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <a href="/" class="back-button">返回首頁</a>
                <h1>📄 派車結果本地檔案</h1>
                <p>顯示 search_result.txt 檔案的內容，包含最新的派車查詢結果。</p>
            </div>
            
            <div class="controls">
                <button class="btn" onclick="window.location.reload()">🔄 重新整理</button>
                <a href="/download-dispatch-result" class="btn btn-download">📥 下載檔案</a>
            </div>
    '''
    
    try:
        file_path = 'search_result.txt'
        
        if os.path.exists(file_path):
            # 獲取檔案資訊
            file_stat = os.stat(file_path)
            file_size = file_stat.st_size
            file_mtime = datetime.fromtimestamp(file_stat.st_mtime)
            
            html += f'''
            <div class="file-info">
                <strong>📋 檔案資訊：</strong><br>
                檔案名稱: search_result.txt<br>
                檔案大小: {file_size} bytes<br>
                最後修改時間: {file_mtime.strftime('%Y-%m-%d %H:%M:%S')}<br>
                檔案路徑: {os.path.abspath(file_path)}
            </div>
            '''
            
            # 讀取檔案內容
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if content.strip():
                html += f'''
                <div class="content">
                    <h2>📝 檔案內容</h2>
                    <div class="file-content">{content}</div>
                </div>
                '''
            else:
                html += '''
                <div class="no-file">
                    <h2>📭 檔案內容為空</h2>
                    <p>search_result.txt 檔案存在但內容為空。</p>
                    <p>請執行「🔄 抓取派車結果」功能來生成內容。</p>
                </div>
                '''
        else:
            html += '''
            <div class="no-file">
                <h2>📭 檔案不存在</h2>
                <p>search_result.txt 檔案尚未建立。</p>
                <p>請先執行「🔄 抓取派車結果」功能來生成檔案。</p>
            </div>
            '''
            
    except Exception as e:
        html += f'''
        <div class="no-file">
            <h2>❌ 讀取檔案失敗</h2>
            <p>無法讀取 search_result.txt 檔案。</p>
            <p>錯誤訊息: {str(e)}</p>
        </div>
        '''
    
    html += '''
        </div>
        
        <script>
            // 每30秒自動重新整理
            setInterval(function() {
                window.location.reload();
            }, 30000);
        </script>
    </body>
    </html>
    '''
    
    return html



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

@app.route('/latest-dispatch')
def latest_dispatch():
    """查看最新派車結果"""
    try:
        import re
        
        # 讀取 search_result.txt 檔案
        result_file = 'search_result.txt'
        results = []
        file_info = {
            'exists': False,
            'query_time': '未知',
            'search_date': '未知',
            'total_attempts': 0,
            'total_records': 0,
            'matched_records': 0
        }
        
        if os.path.exists(result_file):
            file_info['exists'] = True
            
            with open(result_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if content.strip():
                # 解析檔案標題資訊
                lines = content.split('\n')
                for line in lines:
                    if '派車結果查詢時間:' in line:
                        file_info['query_time'] = line.split(':', 1)[1].strip()
                    elif '搜尋目標日期:' in line:
                        file_info['search_date'] = line.split(':', 1)[1].strip()
                    elif '總共嘗試次數:' in line:
                        try:
                            file_info['total_attempts'] = int(re.search(r'\d+', line).group())
                        except:
                            pass
                    elif '總共檢查記錄數:' in line:
                        try:
                            file_info['total_records'] = int(re.search(r'\d+', line).group())
                        except:
                            pass
                    elif '符合條件的已派車記錄數:' in line:
                        try:
                            file_info['matched_records'] = int(re.search(r'\d+', line).group())
                        except:
                            pass
                
                # 解析派車記錄
                # 尋找以 "🚗 已派車記錄" 開頭的區塊
                record_pattern = r'🚗 已派車記錄 \d+.*?\n(.*?)(?=🚗 已派車記錄|\Z)'
                record_matches = re.findall(record_pattern, content, re.DOTALL)
                
                for match in record_matches:
                    record_data = {'date_time': '', 'car_number': '', 'driver': '', 'amount': ''}
                    
                    # 解析每個欄位
                    for line in match.split('\n'):
                        line = line.strip()
                        if '預約日期/時段:' in line:
                            record_data['date_time'] = line.split(':', 1)[1].strip()
                        elif '車號:' in line:
                            record_data['car_number'] = line.split(':', 1)[1].strip()
                        elif '指派司機:' in line:
                            record_data['driver'] = line.split(':', 1)[1].strip()
                        elif '自付金額:' in line:
                            record_data['amount'] = line.split(':', 1)[1].strip()
                    
                    # 只有當至少有日期時間資訊時才加入結果
                    if record_data['date_time']:
                        results.append(record_data)
        
        return render_template_string('''
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>最新派車結果</title>
    <style>
        body { 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            margin: 0; 
            padding: 20px; 
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            min-height: 100vh;
        }
        .container { 
            max-width: 1200px; 
            margin: 0 auto; 
            background: white; 
            border-radius: 16px; 
            padding: 30px; 
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }
        .header {
            text-align: center;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 3px solid #f0f0f0;
        }
        .header h1 {
            color: #2c3e50;
            margin: 0;
            font-size: 2.2em;
            font-weight: 400;
        }
        .back-button { 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white; 
            padding: 12px 24px; 
            text-decoration: none; 
            border-radius: 25px; 
            display: inline-block; 
            margin-bottom: 20px; 
            font-weight: 500;
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
        }
        .back-button:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
        }
        .info-panel {
            background: linear-gradient(135deg, #e8f5e8 0%, #d4edda 100%);
            border-left: 5px solid #28a745;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 30px;
        }
        .info-panel h3 {
            margin: 0 0 15px 0;
            color: #155724;
            font-size: 1.3em;
        }
        .info-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 15px;
        }
        .info-item {
            background: white;
            padding: 15px;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        .info-label {
            font-weight: 600;
            color: #495057;
            margin-bottom: 5px;
        }
        .info-value {
            color: #6c757d;
            font-size: 1.1em;
        }
        .table-container {
            overflow-x: auto;
            margin-top: 20px;
            border-radius: 12px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }
        .results-table {
            width: 100%;
            border-collapse: collapse;
            background: white;
            border-radius: 12px;
            overflow: hidden;
        }
        .results-table th {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 18px;
            text-align: left;
            font-weight: 600;
            font-size: 1.1em;
            border: none;
            line-height: 1.3;
        }
        .results-table th small {
            display: block;
            font-size: 0.8em;
            font-weight: 400;
            opacity: 0.9;
            margin-top: 4px;
        }
        .results-table td {
            padding: 16px 18px;
            border-bottom: 1px solid #e9ecef;
            color: #495057;
        }
        .results-table tr:nth-child(even) {
            background-color: #f8f9fa;
        }
        .results-table tr:hover {
            background-color: #e3f2fd;
            transition: background-color 0.3s ease;
        }
        .mobile-cards {
            display: none;
        }
        .card {
            background: white;
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            border-left: 4px solid #667eea;
        }
        .card-header {
            display: flex;
            align-items: center;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 1px solid #f0f0f0;
        }
        .card-icon {
            font-size: 1.5em;
            margin-right: 10px;
            color: #667eea;
        }
        .card-title {
            font-size: 1.1em;
            font-weight: 600;
            color: #2c3e50;
        }
        .card-field {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 12px;
            padding: 8px 0;
        }
        .card-field:last-child {
            margin-bottom: 0;
        }
        .field-label {
            font-weight: 600;
            color: #495057;
            margin-right: 15px;
            flex-shrink: 0;
            min-width: 40%;
            font-size: 0.95em;
        }
        .field-label small {
            display: block;
            font-size: 0.8em;
            font-weight: 400;
            color: #6c757d;
            margin-top: 2px;
        }
        .field-value {
            color: #2c3e50;
            text-align: right;
            word-break: break-word;
        }
        .no-data {
            text-align: center;
            padding: 60px 20px;
            color: #6c757d;
        }
        .no-data .icon {
            font-size: 4em;
            margin-bottom: 20px;
            opacity: 0.5;
        }
        .no-data h3 {
            margin: 0 0 10px 0;
            font-size: 1.5em;
            color: #495057;
        }
        .no-data p {
            margin: 0;
            font-size: 1.1em;
        }
        .actions {
            text-align: center;
            margin-top: 30px;
        }
        .action-btn {
            background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
            color: white;
            padding: 12px 24px;
            text-decoration: none;
            border-radius: 25px;
            margin: 0 10px;
            font-weight: 500;
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(40, 167, 69, 0.3);
        }
        .action-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(40, 167, 69, 0.4);
        }
        .status-badge {
            background: #28a745;
            color: white;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.9em;
            font-weight: 500;
        }
        @media (max-width: 768px) {
            .container { 
                margin: 10px; 
                padding: 20px; 
            }
            .header h1 { 
                font-size: 1.8em; 
            }
            .info-grid {
                grid-template-columns: 1fr;
            }
            .table-container {
                display: none;
            }
            .mobile-cards {
                display: block;
            }
            .actions {
                margin-top: 20px;
            }
            .action-btn {
                display: block;
                margin: 10px 0;
                text-align: center;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <a href="/" class="back-button">← 返回首頁</a>
        
        <div class="header">
            <h1>📋 最新派車結果</h1>
        </div>
        
        {% if file_info.exists %}
            <div class="info-panel">
                <h3>📊 查詢資訊摘要</h3>
                <div class="info-grid">
                    <div class="info-item">
                        <div class="info-label">🕒 查詢時間</div>
                        <div class="info-value">{{ file_info.query_time }}</div>
                    </div>
                    <div class="info-item">
                        <div class="info-label">📅 搜尋日期</div>
                        <div class="info-value">{{ file_info.search_date }}</div>
                    </div>
                    <div class="info-item">
                        <div class="info-label">🔄 嘗試次數</div>
                        <div class="info-value">{{ file_info.total_attempts }} 次</div>
                    </div>
                    <div class="info-item">
                        <div class="info-label">📝 檢查記錄</div>
                        <div class="info-value">{{ file_info.total_records }} 筆</div>
                    </div>
                    <div class="info-item">
                        <div class="info-label">✅ 派車記錄</div>
                        <div class="info-value">{{ file_info.matched_records }} 筆</div>
                    </div>
                    <div class="info-item">
                        <div class="info-label">🎯 搜尋狀態</div>
                        <div class="info-value">
                            <span class="status-badge">已派車記錄</span>
                        </div>
                    </div>
                </div>
            </div>
            
            {% if results %}
                <!-- 桌面版表格 -->
                <div class="table-container">
                    <table class="results-table">
                        <thead>
                            <tr>
                                <th>🕒 搭車日期時間<br><small>Tanggal dan waktu naik kendaraan</small></th>
                                <th>🚗 車號<br><small>Nomor kendaraan</small></th>
                                <th>👨‍✈️ 司機電話<br><small>Nomor telepon sopir</small></th>
                                <th>💰 搭車金額<br><small>Jumlah biaya naik kendaraan</small></th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for result in results %}
                            <tr>
                                <td>{{ result.date_time or '未提供' }}</td>
                                <td>{{ result.car_number or '未提供' }}</td>
                                <td>{{ result.driver or '未提供' }}</td>
                                <td>{{ result.amount or '未提供' }}</td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
                
                <!-- 手機版卡片 -->
                <div class="mobile-cards">
                    {% for result in results %}
                    <div class="card">
                        <div class="card-header">
                            <div class="card-icon">🚗</div>
                            <div class="card-title">派車記錄 {{ loop.index }}</div>
                        </div>
                        <div class="card-field">
                            <div class="field-label">
                                🕒 搭車日期時間
                                <small>Tanggal dan waktu naik kendaraan</small>
                            </div>
                            <div class="field-value">{{ result.date_time or '未提供' }}</div>
                        </div>
                        <div class="card-field">
                            <div class="field-label">
                                🚗 車號
                                <small>Nomor kendaraan</small>
                            </div>
                            <div class="field-value">{{ result.car_number or '未提供' }}</div>
                        </div>
                        <div class="card-field">
                            <div class="field-label">
                                👨‍✈️ 司機電話
                                <small>Nomor telepon sopir</small>
                            </div>
                            <div class="field-value">{{ result.driver or '未提供' }}</div>
                        </div>
                        <div class="card-field">
                            <div class="field-label">
                                💰 搭車金額
                                <small>Jumlah biaya naik kendaraan</small>
                            </div>
                            <div class="field-value">{{ result.amount or '未提供' }}</div>
                        </div>
                    </div>
                    {% endfor %}
                </div>
            {% else %}
                <div class="no-data">
                    <div class="icon">📭</div>
                    <h3>未找到派車記錄</h3>
                    <p>在指定日期內沒有找到已派車的記錄<br><span style='color:#888;font-size:0.98em;'>(Tidak ada catatan penugasan mobil yang ditemukan pada tanggal yang ditentukan)</span></p>
                </div>
            {% endif %}
        {% else %}
            <div class="no-data">
                <div class="icon">📄</div>
                <h3>尚未查詢派車結果</h3>
                <p>請先執行「抓取派車結果」功能來獲取最新資料</p>
            </div>
        {% endif %}
        
        <div class="actions">
            <a href="/fetch-dispatch" class="action-btn">🔄 重新抓取派車結果</a>
            <a href="/dispatch-result-file" class="action-btn">📄 查看完整檔案</a>
        </div>
    </div>
</body>
</html>
        ''', 
        file_info=file_info,
        results=results
        )
        
    except Exception as e:
        print(f"讀取派車結果時發生錯誤: {e}")
        return f'''
        <!DOCTYPE html>
        <html lang="zh-TW">
        <head>
            <meta charset="UTF-8">
            <title>錯誤</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .error {{ background: #f8d7da; color: #721c24; padding: 20px; border-radius: 8px; }}
            </style>
        </head>
        <body>
            <a href="/">← 返回首頁</a>
            <div class="error">
                <h2>讀取派車結果時發生錯誤</h2>
                <p>錯誤訊息: {str(e)}</p>
            </div>
        </body>
        </html>
        '''

@app.route('/fetch-dispatch')
def fetch_dispatch():
    """抓取派車結果"""
    try:
        print("=== 開始執行派車結果抓取流程 ===")
        result = fetch_dispatch_results()
        print(f"=== 派車結果抓取流程執行結果: {result} ===")
        return jsonify({"success": result, "message": "派車結果抓取流程執行完成"})
    except Exception as e:
        import traceback
        error_msg = f"派車結果抓取流程執行失敗: {str(e)}"
        print(error_msg)
        print("詳細錯誤資訊:")
        print(traceback.format_exc())
        return jsonify({"success": False, "error": error_msg}), 500

@app.route('/cron-logs')
def cron_logs():
    """查看 Cron Job 日誌"""
    try:
        logs = []
        log_file = 'cron_reservation.log'
        
        if os.path.exists(log_file):
            with open(log_file, 'r', encoding='utf-8') as f:
                logs = f.readlines()
        
        # 取得最後 100 行日誌
        recent_logs = logs[-100:] if len(logs) > 100 else logs
        
        return render_template_string('''
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Cron Job 日誌查看</title>
    <style>
        body {
            font-family: 'Courier New', monospace;
            margin: 20px;
            background-color: #1e1e1e;
            color: #d4d4d4;
        }
        .header {
            background-color: #2d2d30;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            border-left: 4px solid #007acc;
        }
        .header h1 {
            margin: 0;
            color: #ffffff;
        }
        .log-container {
            background-color: #2d2d30;
            padding: 20px;
            border-radius: 8px;
            max-height: 70vh;
            overflow-y: auto;
            border: 1px solid #3e3e42;
        }
        .log-line {
            margin: 2px 0;
            padding: 4px 8px;
            border-radius: 3px;
            white-space: pre-wrap;
            word-wrap: break-word;
        }
        .log-info { color: #4ec9b0; }
        .log-error { color: #f44747; background-color: rgba(244, 71, 71, 0.1); }
        .log-success { color: #b5cea8; }
        .log-warning { color: #dcdcaa; }
        .log-timestamp { color: #9cdcfe; }
        .controls {
            margin-bottom: 20px;
            text-align: center;
        }
        .btn {
            background-color: #007acc;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 4px;
            cursor: pointer;
            margin: 0 5px;
            font-size: 14px;
        }
        .btn:hover {
            background-color: #005a9e;
        }
        .stats {
            display: flex;
            justify-content: space-around;
            background-color: #252526;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
        }
        .stat-item {
            text-align: center;
        }
        .stat-number {
            font-size: 24px;
            font-weight: bold;
            color: #007acc;
        }
        .stat-label {
            font-size: 12px;
            color: #cccccc;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🚗 新北市長照交通預約系統 - Cron Job 日誌</h1>
        <p>日誌檔案: cron_reservation.log | 顯示最新 100 行</p>
    </div>
    
    <div class="stats">
        <div class="stat-item">
            <div class="stat-number">{{ total_lines }}</div>
            <div class="stat-label">總日誌行數</div>
        </div>
        <div class="stat-item">
            <div class="stat-number">{{ success_count }}</div>
            <div class="stat-label">成功執行次數</div>
        </div>
        <div class="stat-item">
            <div class="stat-number">{{ error_count }}</div>
            <div class="stat-label">錯誤次數</div>
        </div>
        <div class="stat-item">
            <div class="stat-number">{{ last_execution }}</div>
            <div class="stat-label">最後執行</div>
        </div>
    </div>
    
    <div class="controls">
        <button class="btn" onclick="window.location.reload()">🔄 重新整理</button>
        <button class="btn" onclick="downloadLogs()">📥 下載完整日誌</button>
        <button class="btn" onclick="clearLogs()">🗑️ 清空日誌</button>
        <button class="btn" onclick="window.location.href='/'">🏠 返回首頁</button>
    </div>
    
    <div class="log-container">
        {% if logs %}
            {% for log in logs %}
                <div class="log-line {{ get_log_class(log) }}">{{ log.strip() }}</div>
            {% endfor %}
        {% else %}
            <div class="log-line">暫無日誌記錄</div>
        {% endif %}
    </div>
    
    <script>
        function downloadLogs() {
            window.open('/cron-logs/download', '_blank');
        }
        
        function clearLogs() {
            if (confirm('確定要清空所有日誌嗎？此操作無法復原。')) {
                fetch('/cron-logs/clear', { method: 'POST' })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        alert('日誌已清空');
                        window.location.reload();
                    } else {
                        alert('清空失敗: ' + data.error);
                    }
                });
            }
        }
        
        // 自動滾動到底部
        document.addEventListener('DOMContentLoaded', function() {
            const container = document.querySelector('.log-container');
            container.scrollTop = container.scrollHeight;
        });
        
        // 每30秒自動重新整理
        setInterval(function() {
            window.location.reload();
        }, 30000);
    </script>
</body>
</html>
        ''', 
        logs=recent_logs,
        total_lines=len(logs),
        success_count=sum(1 for log in logs if '成功' in log or 'SUCCESS' in log),
        error_count=sum(1 for log in logs if '失敗' in log or 'ERROR' in log or '錯誤' in log),
        last_execution='剛才' if logs else '從未執行',
        get_log_class=get_log_class
        )
        
    except Exception as e:
        return f"讀取日誌失敗: {e}"

def get_log_class(log_line):
    """根據日誌內容返回對應的 CSS 類別"""
    log_lower = log_line.lower()
    if 'error' in log_lower or '錯誤' in log_lower or '失敗' in log_lower:
        return 'log-error'
    elif 'success' in log_lower or '成功' in log_lower or '✅' in log_line:
        return 'log-success'
    elif 'warning' in log_lower or '警告' in log_lower or '⚠️' in log_line:
        return 'log-warning'
    elif any(char.isdigit() for char in log_line[:20]):  # 包含時間戳
        return 'log-timestamp'
    else:
        return 'log-info'

@app.route('/dispatch-cron-logs')
def dispatch_cron_logs():
    """顯示派車查詢的 cron job 日誌"""
    try:
        log_file = 'cron_dispatch.log'
        
        if not os.path.exists(log_file):
            # 如果日誌檔案不存在，創建一個空的
            with open(log_file, 'w', encoding='utf-8') as f:
                f.write("派車查詢日誌檔案 - 等待首次執行\n")
        
        # 讀取日誌檔案
        with open(log_file, 'r', encoding='utf-8') as f:
            logs = f.readlines()
        
        # 只顯示最新的100行
        recent_logs = logs[-100:]
        
        return render_template_string('''
<!DOCTYPE html>
<html>
<head>
    <title>派車查詢 Cron Job 日誌</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {
            font-family: 'Segoe UI', Consolas, monospace;
            background-color: #1e1e1e;
            color: #d4d4d4;
            margin: 0;
            padding: 20px;
            line-height: 1.6;
        }
        .header {
            background-color: #2d2d30;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            text-align: center;
        }
        .header h1 {
            color: #00d7ff;
            margin: 0 0 10px 0;
        }
        .header p {
            color: #cccccc;
            margin: 0;
        }
        .log-container {
            background-color: #252526;
            border: 1px solid #3c3c3c;
            border-radius: 8px;
            padding: 20px;
            font-family: 'Courier New', Consolas, monospace;
            font-size: 14px;
            max-height: 600px;
            overflow-y: auto;
        }
        .log-line {
            margin: 5px 0;
            padding: 5px;
            border-radius: 3px;
            word-wrap: break-word;
        }
        .log-info { color: #d4d4d4; }
        .log-success { color: #4ec9b0; background-color: rgba(78, 201, 176, 0.1); }
        .log-error { color: #f44747; background-color: rgba(244, 71, 71, 0.1); }
        .log-warning { color: #dcdcaa; }
        .log-timestamp { color: #9cdcfe; }
        .controls {
            margin-bottom: 20px;
            text-align: center;
        }
        .btn {
            background-color: #007acc;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 4px;
            cursor: pointer;
            margin: 0 5px;
            font-size: 14px;
        }
        .btn:hover {
            background-color: #005a9e;
        }
        .stats {
            display: flex;
            justify-content: space-around;
            background-color: #252526;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
        }
        .stat-item {
            text-align: center;
        }
        .stat-number {
            font-size: 24px;
            font-weight: bold;
            color: #00d7ff;
        }
        .stat-label {
            font-size: 12px;
            color: #cccccc;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🔍 派車查詢 Cron Job 日誌</h1>
        <p>日誌檔案: cron_dispatch.log | 顯示最新 100 行</p>
        <p>排程時間: 每週一和週四 00:10 (台北時區)</p>
    </div>
    
    <div class="stats">
        <div class="stat-item">
            <div class="stat-number">{{ total_lines }}</div>
            <div class="stat-label">總日誌行數</div>
        </div>
        <div class="stat-item">
            <div class="stat-number">{{ success_count }}</div>
            <div class="stat-label">成功執行次數</div>
        </div>
        <div class="stat-item">
            <div class="stat-number">{{ error_count }}</div>
            <div class="stat-label">錯誤次數</div>
        </div>
        <div class="stat-item">
            <div class="stat-number">{{ last_execution }}</div>
            <div class="stat-label">最後執行</div>
        </div>
    </div>
    
    <div class="controls">
        <button class="btn" onclick="window.location.reload()">🔄 重新整理</button>
        <button class="btn" onclick="downloadLogs()">📥 下載完整日誌</button>
        <button class="btn" onclick="clearLogs()">🗑️ 清空日誌</button>
        <button class="btn" onclick="window.location.href='/'">🏠 返回首頁</button>
    </div>
    
    <div class="log-container">
        {% if logs %}
            {% for log in logs %}
                <div class="log-line {{ get_log_class(log) }}">{{ log.strip() }}</div>
            {% endfor %}
        {% else %}
            <div class="log-line">暫無日誌記錄</div>
        {% endif %}
    </div>
    
    <script>
        function downloadLogs() {
            window.open('/dispatch-cron-logs/download', '_blank');
        }
        
        function clearLogs() {
            if (confirm('確定要清空所有派車查詢日誌嗎？此操作無法復原。')) {
                fetch('/dispatch-cron-logs/clear', { method: 'POST' })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        alert('日誌已清空');
                        window.location.reload();
                    } else {
                        alert('清空失敗: ' + data.error);
                    }
                });
            }
        }
        
        // 自動滾動到底部
        document.addEventListener('DOMContentLoaded', function() {
            const container = document.querySelector('.log-container');
            container.scrollTop = container.scrollHeight;
        });
        
        // 每30秒自動重新整理
        setInterval(function() {
            window.location.reload();
        }, 30000);
    </script>
</body>
</html>
        ''', 
        logs=recent_logs,
        total_lines=len(logs),
        success_count=sum(1 for log in logs if '成功' in log or 'SUCCESS' in log),
        error_count=sum(1 for log in logs if '失敗' in log or 'ERROR' in log or '錯誤' in log),
        last_execution='剛才' if logs else '從未執行',
        get_log_class=get_log_class
        )
        
    except Exception as e:
        return f"讀取派車查詢日誌失敗: {e}"

@app.route('/dispatch-cron-logs/download')
def download_dispatch_cron_logs():
    """下載完整派車查詢日誌檔案"""
    try:
        log_file = 'cron_dispatch.log'
        if os.path.exists(log_file):
            taipei_tz = pytz.timezone('Asia/Taipei')
            timestamp = datetime.now(taipei_tz).strftime("%Y%m%d_%H%M%S")
            return send_file(
                log_file,
                as_attachment=True,
                download_name=f'cron_dispatch_{timestamp}.log',
                mimetype='text/plain'
            )
        else:
            return "派車查詢日誌檔案不存在", 404
    except Exception as e:
        return f"下載失敗: {e}", 500

@app.route('/dispatch-cron-logs/clear', methods=['POST'])
def clear_dispatch_cron_logs():
    """清空派車查詢日誌檔案"""
    try:
        log_file = 'cron_dispatch.log'
        if os.path.exists(log_file):
            taipei_tz = pytz.timezone('Asia/Taipei')
            current_time = datetime.now(taipei_tz)
            with open(log_file, 'w', encoding='utf-8') as f:
                f.write(f"{current_time} - 派車查詢日誌已清空\n")
        return {'success': True}
    except Exception as e:
        return {'success': False, 'error': str(e)}

@app.route('/cron-logs/download')
def download_cron_logs():
    """下載完整日誌檔案"""
    try:
        log_file = 'cron_reservation.log'
        if os.path.exists(log_file):
            taipei_tz = pytz.timezone('Asia/Taipei')
            timestamp = datetime.now(taipei_tz).strftime("%Y%m%d_%H%M%S")
            return send_file(
                log_file,
                as_attachment=True,
                download_name=f'cron_reservation_{timestamp}.log',
                mimetype='text/plain'
            )
        else:
            return "日誌檔案不存在", 404
    except Exception as e:
        return f"下載失敗: {e}", 500

@app.route('/cron-logs/clear', methods=['POST'])
def clear_cron_logs():
    """清空日誌檔案"""
    try:
        log_file = 'cron_reservation.log'
        if os.path.exists(log_file):
            taipei_tz = pytz.timezone('Asia/Taipei')
            current_time = datetime.now(taipei_tz)
            with open(log_file, 'w', encoding='utf-8') as f:
                f.write(f"{current_time} - 日誌已清空\n")
        return {'success': True}
    except Exception as e:
        return {'success': False, 'error': str(e)}

@app.route('/download-dispatch-result')
def download_dispatch_result():
    """下載派車結果檔案"""
    try:
        file_path = 'search_result.txt'
        if os.path.exists(file_path):
            from datetime import datetime
            taipei_tz = pytz.timezone('Asia/Taipei')
            timestamp = datetime.now(taipei_tz).strftime("%Y%m%d_%H%M%S")
            return send_file(
                file_path,
                as_attachment=True,
                download_name=f'search_result_{timestamp}.txt',
                mimetype='text/plain'
            )
        else:
            return "派車結果檔案不存在", 404
    except Exception as e:
        return f"下載失敗: {e}", 500



if __name__ == '__main__':
    # Zeabur 環境變數
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port) 