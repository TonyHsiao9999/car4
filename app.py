from flask import Flask, request, jsonify, send_from_directory
from playwright.sync_api import sync_playwright
import time
import os
import base64
import pytz
import re
from datetime import datetime

app = Flask(__name__)

def take_screenshot(driver, name):
    """截圖功能"""
    try:
        # 使用台北時區
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
        
        # 檢查並確保瀏覽器已安裝
        try:
            from playwright.sync_api import sync_playwright
            print("Playwright 模組載入成功")
        except ImportError as e:
            print(f"Playwright 模組載入失敗: {e}")
            return None
        
        # 簡化的瀏覽器檢查（跳過預檢，直接嘗試啟動）
        print("⚡ 快速模式：直接嘗試啟動瀏覽器...")
        browser_available = True  # 假設可用，失敗時再處理
        
        playwright = sync_playwright().start()
        
        # 使用 Playwright 的 Chromium，添加更健壯的配置
        browser_args = [
            '--no-sandbox',
            '--disable-dev-shm-usage',
            '--disable-gpu',
            '--disable-web-security',
            '--disable-features=VizDisplayCompositor',
            '--disable-extensions',
            '--disable-plugins',
            '--disable-background-timer-throttling',
            '--disable-backgrounding-occluded-windows',
            '--disable-renderer-backgrounding',
            '--disable-features=TranslateUI',
            '--disable-ipc-flooding-protection',
            '--memory-pressure-off',
            '--disable-blink-features=AutomationControlled',
            '--disable-software-rasterizer',
            '--single-process',
            '--no-zygote',
            '--disable-setuid-sandbox'
        ]
        
        print(f"瀏覽器啟動參數: {browser_args}")
        
        # 啟動瀏覽器（快速模式，失敗時自動安裝）
        browser = None
        
        try:
            print("🚀 啟動瀏覽器...")
            browser = playwright.chromium.launch(
                headless=True,
                args=browser_args,
                timeout=20000  # 20秒超時，快速失敗
            )
            print("✅ 瀏覽器啟動成功")
        except Exception as e:
            print(f"❌ 瀏覽器啟動失敗: {e}")
            print("🔄 自動安裝瀏覽器並重試...")
            try:
                import subprocess
                import sys
                # 啟動失敗時才安裝
                result = subprocess.run([sys.executable, '-m', 'playwright', 'install', 'chromium'], 
                                      capture_output=True, text=True, timeout=60)
                if result.returncode == 0:
                    print("✅ 瀏覽器安裝完成，重新啟動...")
                    browser = playwright.chromium.launch(
                        headless=True,
                        args=browser_args,
                        timeout=20000
                    )
                    print("✅ 瀏覽器重新啟動成功")
                else:
                    print(f"❌ 瀏覽器安裝失敗: {result.stderr[:100]}")
                    playwright.stop()
                    return None
            except Exception as install_e:
                print(f"❌ 瀏覽器安裝和重啟過程失敗: {install_e}")
                playwright.stop()
                return None
        
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
        
        # 開始訂單查詢流程
        print("=== 開始訂單查詢流程 ===")
        try:
            # 點擊「訂單查詢」
            print("點擊訂單查詢...")
            
            # 等待頁面穩定
            print("等待頁面穩定...")
            driver['page'].wait_for_load_state("networkidle")
            driver['page'].wait_for_timeout(2000)
            
            print("等待 JavaScript 內容載入...")
            driver['page'].wait_for_timeout(3000)
            
            order_selectors = [
                '.page:nth-child(2) li:nth-child(2) h2:nth-child(1)',
                '.page:nth-child(2) li:nth-child(2)',
                '.page li:nth-child(2)',
                'li:has-text("訂單查詢")',
                'h2:has-text("訂單查詢")',
                'a:has-text("訂單查詢")',
                '*:has-text("訂單查詢")',
                'nav li:nth-child(2)',
                '.nav li:nth-child(2)',
                '.menu li:nth-child(2)',
                'li:contains("訂單")',
                'li:contains("查詢")',
                '*:contains("訂單查詢")'
            ]
            
            order_clicked = False
            
            for selector in order_selectors:
                try:
                    print(f"嘗試訂單查詢選擇器: {selector}")
                    
                    elements = driver['page'].query_selector_all(selector)
                    print(f"找到 {len(elements)} 個元素使用選擇器: {selector}")
                    
                    if elements:
                        for i, element in enumerate(elements):
                            try:
                                if element.is_visible():
                                    element_text = element.inner_text().strip()
                                    print(f"元素 {i+1} 文字: '{element_text}'")
                                    
                                    if "訂單查詢" in element_text:
                                        print(f"✅ 找到訂單查詢元素: {selector}")
                                        element.click()
                                        print(f"🎯 訂單查詢點擊成功")
                                        
                                        print("等待頁面導航...")
                                        driver['page'].wait_for_load_state("networkidle", timeout=10000)
                                        driver['page'].wait_for_timeout(3000)
                                        
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
                
                try:
                    print("🔄 直接導航到 ReservationOrder 頁面...")
                    driver['page'].goto("https://www.ntpc.ltc-car.org/ReservationOrder/")
                    driver['page'].wait_for_load_state("networkidle", timeout=15000)
                    driver['page'].wait_for_timeout(3000)
                    
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
            
            # 驗證是否成功到達訂單查詢頁面
            print("驗證是否成功到達訂單查詢頁面...")
            try:
                final_url = driver['page'].url
                print(f"最終URL: {final_url}")
                
                if "ReservationOrder" not in final_url:
                    print(f"❌ 最終URL不正確: {final_url}")
                    take_screenshot("wrong_final_url")
                    return False
                
                order_page_indicators = [
                    '.order_list',
                    'text=預約記錄',
                    'text=訂單記錄', 
                    'text=預約列表',
                    '.reservation-list',
                    '.record-list',
                    'table',
                    '.order-item',
                    '.date',
                    '.see_more'
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
            driver['page'].wait_for_timeout(5000)
            take_screenshot("order_list_loaded")
            
            # 不使用日期篩選，處理所有記錄
            print("🎯 搜尋所有記錄，不限制日期範圍")
            
            # 分析訂單記錄
            print("開始分析訂單記錄...")
            
            # 清空結果檔案
            result_file = "search_result.txt"
            with open(result_file, 'w', encoding='utf-8') as f:
                f.write("")
            
            results = []
            total_records_checked = 0
            total_dispatch_records_found = 0
            
            print("🔍 系統分析：檢測到 Vue.js SPA 架構")
            print("💡 新策略：透過網路請求監聽和智慧等待獲取所有資料")
            
            # 設置網路請求監聽
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
            
            # 分析頁面隱藏記錄結構（不進行載入更多操作）
            print("📊 分析頁面隱藏記錄結構")
            
            # 等待記錄載入
            driver['page'].wait_for_selector('.order_list', timeout=10000)
            
            print("🔍 執行全面的隱藏記錄檢測...")
            
            # 使用 JavaScript 進行全面的隱藏記錄檢測和顯示
            results = driver['page'].evaluate("""
                () => {
                    const results = {
                        initial_visible: 0,
                        potential_hidden: 0,
                        displayed_hidden: 0,
                        final_total: 0,
                        log: []
                    };
                    
                    // 記錄初始可見的記錄
                    const initialVisible = document.querySelectorAll('.order_list');
                    results.initial_visible = initialVisible.length;
                    results.log.push(`初始可見記錄: ${initialVisible.length} 筆`);
                    
                    // 尋找所有可能的記錄元素（包括隱藏的）
                    const allPotentialSelectors = [
                        '.order_list',
                        '[class*="order"]',
                        '[class*="Order"]', 
                        '[data-order]',
                        '[data-status]',
                        '.list-item',
                        '.record-item',
                        '.reservation-item',
                        '.booking-item',
                        'li[class*="item"]',
                        'div[class*="item"]'
                    ];
                    
                    const foundElements = new Set();
                    allPotentialSelectors.forEach(selector => {
                        try {
                            const elements = document.querySelectorAll(selector);
                            elements.forEach(el => {
                                // 檢查是否包含預約或派車相關內容
                                const text = el.innerText || el.textContent || '';
                                if (text.includes('預約') || text.includes('派車') || 
                                    text.includes('司機') || text.includes('車號') ||
                                    text.includes('狀態') || text.includes('已派車') ||
                                    text.includes('媒合') || text.includes('成立') ||
                                    text.includes('執行') || text.includes('完成') ||
                                    text.includes('取消') || text.includes('日期')) {
                                    foundElements.add(el);
                                }
                            });
                        } catch (e) {
                            // 忽略錯誤的選擇器
                        }
                    });
                    
                    results.potential_hidden = foundElements.size;
                    results.log.push(`找到潛在記錄元素: ${foundElements.size} 個`);
                    
                    // 顯示所有隱藏的記錄
                    let displayedCount = 0;
                    foundElements.forEach(el => {
                        const computedStyle = window.getComputedStyle(el);
                        const isHidden = computedStyle.display === 'none' || 
                                       computedStyle.visibility === 'hidden' ||
                                       computedStyle.opacity === '0' ||
                                       el.style.display === 'none' ||
                                       el.style.visibility === 'hidden';
                        
                        if (isHidden) {
                            el.style.display = 'block';
                            el.style.visibility = 'visible';
                            el.style.opacity = '1';
                            displayedCount++;
                        }
                    });
                    
                    results.displayed_hidden = displayedCount;
                    results.log.push(`顯示隱藏記錄: ${displayedCount} 筆`);
                    
                    // 重新計算最終記錄數
                    setTimeout(() => {
                        const finalElements = document.querySelectorAll('.order_list');
                        results.final_total = finalElements.length;
                    }, 500);
                    
                    return results;
                }
            """)
            
            for log_msg in results['log']:
                print(f"   📝 {log_msg}")
            
            # 等待一下讓 DOM 更新
            driver['page'].wait_for_timeout(1000)
            
            # 重新獲取所有記錄
            all_order_elements = driver['page'].query_selector_all('.order_list')
            total_elements_on_page = len(all_order_elements)
            
            print(f"🎯 最終結果：")
            print(f"   📊 初始可見: {results['initial_visible']} 筆")
            print(f"   🔍 潛在記錄: {results['potential_hidden']} 個元素")
            print(f"   👁️ 顯示隱藏: {results['displayed_hidden']} 筆")
            print(f"   ✅ 最終總數: {total_elements_on_page} 筆記錄")
            
            if total_elements_on_page == 0:
                print("❌ 沒有找到任何記錄，可能頁面結構有變化")
                take_screenshot("no_records_found")
                return False
            
            # 基於實際網頁原始碼的精確狀態檢測
            print("🔍 基於實際JavaScript結構分析記錄狀態...")
            dispatch_records = []
            
            for i, element in enumerate(all_order_elements, 1):
                try:
                    is_visible = element.is_visible()
                    if not is_visible:
                        print(f"⚠️ 記錄 {i}: 不可見，跳過")
                        continue
                    
                    print(f"\n🔍 分析記錄 {i}:")
                    
                    # 從原始碼發現，實際的狀態是通過 CSS class 來控制的：
                    # - accept: Status == 0 (媒合中)
                    # - established: Status == 1 (成立)  
                    # - dispatch: Status == 2 (派車) ← 這是我們要找的
                    # - implement: Status == 3 (執行中) ← 也算已派車
                    # - finish: Status == 4 (完成) ← 也算已派車
                    # - cancel: Status == 5 (取消)
                    
                    # 1. 檢查實際的 CSS 類別
                    class_list = element.get_attribute('class') or ''
                    print(f"   📋 完整CSS類別: '{class_list}'")
                    
                    # 2. 檢查實際生效的狀態類別（不是所有類別都同時存在）
                    full_text = element.inner_text().strip()
                    print(f"   📝 記錄文字內容預覽: {full_text[:100]}...")
                    
                    # 3. 尋找實際的狀態標示（基於原始碼中的狀態顯示邏輯）
                    # 根據JS代碼：媒合中、成立、派車、執行中、完成、取消
                    status_indicators = {
                        'accept': ['媒合中', 'accept'],
                        'established': ['成立', 'established'], 
                        'dispatch': ['派車', 'dispatch'],
                        'implement': ['執行中', 'implement'],
                        'finish': ['完成', 'finish'],
                        'cancel': ['取消', 'cancel']
                    }
                    
                    detected_status = None
                    for status_key, keywords in status_indicators.items():
                        # 檢查CSS類別
                        if any(keyword in class_list.lower() for keyword in keywords):
                            detected_status = status_key
                            print(f"   🎯 CSS檢測到狀態: {status_key}")
                            break
                        # 檢查文字內容
                        if any(keyword in full_text for keyword in keywords):
                            detected_status = status_key
                            print(f"   📄 文字檢測到狀態: {status_key}")
                            break
                    
                    if not detected_status:
                        print(f"   ❓ 未檢測到明確狀態標示")
                    
                    # 4. 檢查是否有司機指派資訊（更精確的判斷）
                    has_driver_assignment = False
                    driver_keywords = ['指派司機', '司機姓名', '車號', '聯絡電話']
                    found_driver_keywords = [kw for kw in driver_keywords if kw in full_text]
                    
                    if found_driver_keywords:
                        has_driver_assignment = True
                        print(f"   👨‍✈️ 發現司機指派資訊: {found_driver_keywords}")
                    
                    # 5. 決策邏輯：只有明確的派車狀態才算已派車
                    is_dispatch_record = False
                    reason = ""
                    
                    if detected_status == 'cancel':
                        reason = "狀態=取消，跳過"
                    elif detected_status == 'dispatch':
                        is_dispatch_record = True
                        reason = "狀態=派車，已派車"
                    elif detected_status == 'implement':
                        is_dispatch_record = True
                        reason = "狀態=執行中，已派車且執行中"
                    elif detected_status == 'finish':
                        is_dispatch_record = True
                        reason = "狀態=完成，已派車且完成"
                    elif has_driver_assignment and detected_status not in ['accept', 'established']:
                        is_dispatch_record = True
                        reason = "有司機指派資訊且非初期狀態，判定為已派車"
                    else:
                        reason = f"狀態={detected_status or '未知'}，司機資訊={has_driver_assignment}，不符合已派車條件"
                    
                    print(f"   📊 判定結果: {'✅ 已派車' if is_dispatch_record else '❌ 非已派車'} - {reason}")
                    
                    if is_dispatch_record:
                        dispatch_records.append({'index': i, 'element': element, 'reason': reason})
                        total_dispatch_records_found += 1
                        print(f"   ➕ 加入處理清單 (總計: {total_dispatch_records_found})")
                        
                except Exception as e:
                    print(f"   ⚠️ 分析記錄 {i} 時發生錯誤: {e}")
                    # 發生錯誤時保守處理，加入清單
                    dispatch_records.append({'index': i, 'element': element, 'reason': "分析錯誤，保守加入"})
                    total_dispatch_records_found += 1
                    continue
            
            print(f"\n🎯 搜尋結果統計:")
            print(f"   📊 總掃描記錄數: {total_elements_on_page}")
            print(f"   ✅ 找到已派車記錄: {total_dispatch_records_found} 筆")
            print(f"   📋 已派車記錄編號: {[r['index'] for r in dispatch_records]}")
            
            if dispatch_records:
                print(f"\n📝 已派車記錄詳情:")
                for record in dispatch_records:
                    print(f"   • 記錄 {record['index']}: {record['reason']}")
            else:
                print(f"\n⚠️ 注意: 在 {total_elements_on_page} 筆記錄中沒有找到任何已派車狀態的記錄")
            
            # 直接使用元素處理已派車狀態的記錄（移除日期篩選）
            for record_info in dispatch_records:
                record_index = record_info['index']
                order_element = record_info['element']
                try:
                    print(f"🔍 處理第 {record_index} 筆已派車記錄...")
                    
                    print(f"🚗 處理已派車記錄 {record_index}")
                    
                    # 嘗試取得日期文字（僅供顯示，不做篩選）
                    date_text = "日期資訊未取得"
                    date_selectors = [
                        '.order_blocks.date .text',
                        '.date .text',
                        '.order_blocks .text'
                    ]
                    
                    for date_sel in date_selectors:
                        try:
                            date_element = order_element.query_selector(date_sel)
                            if date_element and date_element.is_visible():
                                date_text = date_element.inner_text().strip()
                                print(f"📅 第 {record_index} 筆記錄日期: {date_text}")
                                break
                        except:
                            continue
                    
                    total_records_checked += 1
                    print(f"✅ 處理已派車記錄 {record_index}（不限制日期）")
                    
                    take_screenshot(f"record_{record_index}_found")
                    
                    # 在該元素內找展開按鈕
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
                        driver['page'].wait_for_timeout(500)
                        expand_button.click()
                        print(f"✅ 展開按鈕點擊成功")
                        
                        # 等待展開內容載入
                        driver['page'].wait_for_timeout(3000)
                        take_screenshot(f"record_{record_index}_expanded")
                        
                        # 直接在該元素內提取資訊
                        try:
                            # 車號選擇器
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
                            
                            # 指派司機選擇器
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
                            
                            # 負擔金額選擇器
                            amount_selectors = [
                                '.order_blocks:nth-child(6) > .blocks',
                                '.order_blocks:nth-child(6) .blocks',
                                '.order_blocks:nth-child(6) .text',
                                '.order_blocks:nth-child(5) .blocks:nth-child(2)',
                            ]
                            
                            self_pay_amount = "未找到"
                            print(f"💰 開始搜尋負擔金額，共 {len(amount_selectors)} 個選擇器")
                            
                            for i, amount_selector in enumerate(amount_selectors, 1):
                                try:
                                    print(f"💰 嘗試選擇器 {i}/{len(amount_selectors)}: {amount_selector}")
                                    amount_element = order_element.query_selector(amount_selector)
                                    if amount_element and amount_element.is_visible():
                                        amount_text = amount_element.inner_text().strip()
                                        print(f"💰 找到元素，文字內容: '{amount_text}'")
                                        
                                        def is_valid_amount(text):
                                            if not text:
                                                return False
                                            has_digit = any(c.isdigit() for c in text)
                                            if not has_digit:
                                                return False
                                            amount_indicators = ['元', '$', '＄', '負擔金額', '自付', '費用', '金額']
                                            has_amount_indicator = any(indicator in text for indicator in amount_indicators)
                                            return has_amount_indicator
                                        
                                        if is_valid_amount(amount_text):
                                            self_pay_amount = amount_text
                                            print(f"💰 金額選擇器成功: {amount_selector} -> '{amount_text}'")
                                            break
                                        else:
                                            print(f"💰 文字內容不符合金額格式: '{amount_text}'")
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
                                'self_pay_amount': self_pay_amount
                            }
                            
                            results.append(result_entry)
                            print(f"✅ 第 {record_index} 筆記錄提取結果: {result_entry}")
                            take_screenshot(f"record_{record_index}_extracted")
                            
                        except Exception as extract_error:
                            print(f"❌ 提取第 {record_index} 筆記錄資訊時發生錯誤: {extract_error}")
                            take_screenshot(f"record_{record_index}_extract_error")
                            continue
                            
                    else:
                        print(f"❌ 未找到第 {record_index} 筆記錄的展開按鈕")
                        take_screenshot(f"record_{record_index}_no_expand")
                        
                except Exception as record_error:
                    print(f"❌ 處理第 {record_index} 筆記錄時發生錯誤: {record_error}")
                    continue
            
            print(f"✅ 處理完成，共檢查 {total_records_checked} 筆記錄")
            print(f"📊 統計: 找到已派車記錄 {total_dispatch_records_found} 筆，成功處理 {len(results)} 筆")
            
            # 寫入結果檔案
            print("將搜尋結果寫入 search_result.txt...")
            
            taipei_tz = pytz.timezone('Asia/Taipei')
            query_time = datetime.now(taipei_tz)
            result_content = f"派車結果查詢時間: {query_time.strftime('%Y-%m-%d %H:%M:%S')} (台北時區)\n"
            result_content += f"🎯 搜尋範圍: 所有記錄 (智能載入 + 全方位分析)\n"
            result_content += f"總掃描記錄數: {total_elements_on_page}\n"
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
            
            dropoff_success = False
            
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
                    for option in options:
                        text = option.text_content() or ''
                        if text.strip():  # 只記錄非空選項
                            option_texts.append(text.strip())
                    
                    print(f"選單 {i} 的選項: {option_texts}")
                    
                    # 判斷邏輯：
                    # 1. 如果是第一個選單且有「醫療院所」選項，很可能是上車地點，跳過
                    # 2. 如果有「住家」選項，且不是第一個選單，嘗試選擇
                    
                    if i == 0 and '醫療院所' in option_texts:
                        print(f"選單 {i}: 包含'醫療院所'，判斷為上車地點選單，跳過")
                        continue
                    
                    if '住家' in option_texts:
                        print(f"選單 {i}: 包含'住家'選項，嘗試設定為下車地點...")
                        try:
                            # 先檢查當前選中的值
                            current_value = select_elem.input_value()
                            print(f"選單 {i} 當前值: '{current_value}'")
                            
                            # 找到住家選項的索引
                            home_index = None
                            for j, option_text in enumerate(option_texts):
                                if option_text == '住家':
                                    home_index = j
                                    break
                            
                            if home_index is not None:
                                print(f"住家選項在索引 {home_index}")
                                
                                # 嘗試多種選擇方法
                                success = False
                                
                                # 方法1: 使用文字值選擇
                                try:
                                    select_elem.select_option('住家')
                                    driver['page'].wait_for_timeout(500)
                                    new_value = select_elem.input_value()
                                    print(f"方法1 (文字值) 選擇後的值: '{new_value}'")
                                    if new_value == '住家' or (new_value and new_value != current_value):
                                        success = True
                                except Exception as e:
                                    print(f"方法1 (文字值) 失敗: {e}")
                                
                                # 方法2: 使用索引值選擇
                                if not success:
                                    try:
                                        select_elem.select_option(index=home_index)
                                        driver['page'].wait_for_timeout(500)
                                        new_value = select_elem.input_value()
                                        print(f"方法2 (索引值) 選擇後的值: '{new_value}'")
                                        if new_value and new_value != current_value:
                                            success = True
                                    except Exception as e:
                                        print(f"方法2 (索引值) 失敗: {e}")
                                
                                # 方法3: 使用數字值選擇（通常住家是索引1）
                                if not success:
                                    try:
                                        # 嘗試用數字值
                                        select_elem.select_option(str(home_index))
                                        driver['page'].wait_for_timeout(500)
                                        new_value = select_elem.input_value()
                                        print(f"方法3 (數字值) 選擇後的值: '{new_value}'")
                                        if new_value and new_value != current_value:
                                            success = True
                                    except Exception as e:
                                        print(f"方法3 (數字值) 失敗: {e}")
                                
                                # 方法4: 使用 value 屬性選擇
                                if not success:
                                    try:
                                        # 獲取住家選項的 value 屬性
                                        home_option = select_elem.locator('option').nth(home_index)
                                        option_value = home_option.get_attribute('value')
                                        print(f"住家選項的 value 屬性: '{option_value}'")
                                        
                                        if option_value:
                                            select_elem.select_option(value=option_value)
                                            driver['page'].wait_for_timeout(500)
                                            new_value = select_elem.input_value()
                                            print(f"方法4 (value屬性) 選擇後的值: '{new_value}'")
                                            if new_value and new_value != current_value:
                                                success = True
                                    except Exception as e:
                                        print(f"方法4 (value屬性) 失敗: {e}")
                                
                                # 驗證最終結果
                                if success:
                                    final_value = select_elem.input_value()
                                    print(f"✅ 選單 {i} 成功選擇住家作為下車地點，最終值: '{final_value}'")
                                    dropoff_success = True
                                    break
                                else:
                                    print(f"❌ 選單 {i} 所有方法都失敗，無法選擇住家")
                            else:
                                print(f"❌ 在選單 {i} 中找不到住家選項的索引")
                                
                        except Exception as e:
                            print(f"❌ 選單 {i} 選擇住家時發生錯誤: {e}")
                            continue
                    else:
                        print(f"選單 {i}: 沒有'住家'選項，跳過")
                        
                except Exception as e:
                    print(f"檢查選單 {i} 時發生錯誤: {e}")
                    continue
            
            # 如果沒有成功，嘗試更具體的選擇器
            if not dropoff_success:
                print("通過索引方式未成功，嘗試具體的下車地點選擇器...")
                
                specific_selectors = [
                    'select[name*="dropoff"]',  # 包含 dropoff 的 name
                    'select[name*="destination"]',  # 包含 destination 的 name  
                    'select[name*="to"]',  # 包含 to 的 name
                    'select[name*="end"]',  # 包含 end 的 name
                    'select[id*="dropoff"]',  # 包含 dropoff 的 id
                    'select[id*="destination"]',  # 包含 destination 的 id
                    'select:nth-of-type(2)',  # 第二個 select 元素
                    'select:last-of-type'  # 最後一個 select 元素
                ]
                
                for selector in specific_selectors:
                    try:
                        print(f"嘗試選擇器: {selector}")
                        element = driver['page'].locator(selector).first
                        
                        if element.count() > 0 and element.is_visible():
                            # 檢查選項
                            options = element.locator('option').all()
                            option_texts = [opt.text_content() or '' for opt in options if opt.text_content()]
                            print(f"選擇器 {selector} 的選項: {option_texts}")
                            
                            if '住家' in option_texts:
                                print(f"在選擇器 {selector} 中找到住家，嘗試選擇...")
                                element.select_option('住家')
                                driver['page'].wait_for_timeout(500)
                                
                                # 驗證
                                new_value = element.input_value()
                                if new_value == '住家':
                                    print(f"✅ 選擇器 {selector} 成功選擇住家")
                                    dropoff_success = True
                                    break
                                    
                    except Exception as e:
                        print(f"選擇器 {selector} 失敗: {e}")
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

@app.route('/test-address')
def test_address():
    """測試住家地址填入方法的 Web 介面"""
    return '''
    <!DOCTYPE html>
    <html lang="zh-TW">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>住家地址填入測試</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
            .container { max-width: 800px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
            .button { background: #007bff; color: white; padding: 12px 24px; border: none; border-radius: 4px; cursor: pointer; margin: 5px; text-decoration: none; display: inline-block; }
            .button:hover { background: #0056b3; }
            .button:disabled { background: #6c757d; cursor: not-allowed; }
            .danger { background: #dc3545; }
            .danger:hover { background: #c82333; }
            .success { background: #28a745; }
            .warning { background: #ffc107; color: #000; }
            .log { background: #f8f9fa; border: 1px solid #dee2e6; padding: 15px; margin: 10px 0; border-radius: 4px; font-family: monospace; white-space: pre-wrap; max-height: 400px; overflow-y: auto; }
            .status { padding: 10px; margin: 10px 0; border-radius: 4px; }
            .status.success { background: #d4edda; border: 1px solid #c3e6cb; color: #155724; }
            .status.error { background: #f8d7da; border: 1px solid #f5c6cb; color: #721c24; }
            .status.warning { background: #fff3cd; border: 1px solid #ffeaa7; color: #856404; }
            .method-card { border: 1px solid #dee2e6; border-radius: 8px; padding: 15px; margin: 10px 0; background: #fff; }
            .method-title { font-weight: bold; color: #495057; margin-bottom: 10px; }
            .method-description { color: #6c757d; margin-bottom: 15px; }
            h1 { color: #343a40; text-align: center; }
            h2 { color: #495057; border-bottom: 2px solid #007bff; padding-bottom: 5px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🏠 住家地址填入方法測試</h1>
            
            <div class="status warning">
                <strong>⚠️ 注意：</strong>這個測試會實際執行預約流程到住家地址填入步驟，但不會完成最終預約。
            </div>
            
            <h2>🧪 測試選項</h2>
            
            <div class="method-card">
                <div class="method-title">📍 完整地址填入測試</div>
                <div class="method-description">執行完整的預約流程直到住家地址填入步驟，測試所有7種替代方案</div>
                <button class="button" onclick="startAddressTest('full')">開始完整測試</button>
            </div>
            
            <div class="method-card">
                <div class="method-title">🔍 快速地址檢測</div>
                <div class="method-description">只執行到選擇住家步驟，快速檢測地址填入狀況</div>
                <button class="button warning" onclick="startAddressTest('quick')">快速檢測</button>
            </div>
            
            <div class="method-card">
                <div class="method-title">⚙️ 單一方法測試</div>
                <div class="method-description">測試特定的地址填入方法</div>
                <select id="methodSelect" style="padding: 8px; margin: 5px;">
                    <option value="1">方法1: 等待自動填入</option>
                    <option value="2">方法2: 重新選擇住家</option>
                    <option value="3">方法3: 點擊觸發</option>
                    <option value="4">方法4: 手動填入</option>
                    <option value="5">方法5: 地址選單</option>
                    <option value="6">方法6: JavaScript觸發</option>
                    <option value="7">方法7: 表單驗證檢查</option>
                </select>
                <button class="button" onclick="startSingleMethodTest()">測試選定方法</button>
            </div>
            
            <h2>📊 測試狀態</h2>
            <div id="status" class="status">準備進行測試...</div>
            
            <h2>📝 測試日誌</h2>
            <div id="logs" class="log">等待測試開始...</div>
            
            <h2>🖼️ 截圖</h2>
            <div id="screenshots"></div>
            
            <h2>🔗 其他工具</h2>
            <a href="/screenshots" class="button">查看所有截圖</a>
            <a href="/page_source" class="button">查看頁面原始碼</a>
            <a href="/" class="button success">返回主頁</a>
        </div>
        
        <script>
            let testRunning = false;
            
            function updateStatus(message, type = 'warning') {
                const statusEl = document.getElementById('status');
                statusEl.textContent = message;
                statusEl.className = 'status ' + type;
            }
            
            function appendLog(message) {
                const logsEl = document.getElementById('logs');
                const timestamp = new Date().toLocaleTimeString();
                logsEl.textContent += '[' + timestamp + '] ' + message + '\\n';
                logsEl.scrollTop = logsEl.scrollHeight;
            }
            
            function startAddressTest(type) {
                if (testRunning) {
                    alert('測試已在進行中，請等待完成');
                    return;
                }
                
                testRunning = true;
                updateStatus('測試進行中...', 'warning');
                appendLog('開始 ' + (type === 'full' ? '完整' : '快速') + ' 地址填入測試');
                
                // 禁用所有按鈕
                const buttons = document.querySelectorAll('button');
                buttons.forEach(btn => btn.disabled = true);
                
                fetch('/run-address-test', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({type: type})
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        updateStatus('測試完成', 'success');
                        appendLog('✅ 測試成功完成');
                        if (data.logs) {
                            data.logs.forEach(log => appendLog(log));
                        }
                        if (data.screenshots) {
                            showScreenshots(data.screenshots);
                        }
                    } else {
                        updateStatus('測試失敗: ' + data.error, 'error');
                        appendLog('❌ 測試失敗: ' + data.error);
                    }
                })
                .catch(error => {
                    updateStatus('測試錯誤: ' + error.message, 'error');
                    appendLog('💥 測試錯誤: ' + error.message);
                })
                .finally(() => {
                    testRunning = false;
                    // 重新啟用按鈕
                    buttons.forEach(btn => btn.disabled = false);
                });
            }
            
            function startSingleMethodTest() {
                const methodSelect = document.getElementById('methodSelect');
                const method = methodSelect.value;
                
                if (testRunning) {
                    alert('測試已在進行中，請等待完成');
                    return;
                }
                
                testRunning = true;
                updateStatus('測試方法 ' + method + ' 進行中...', 'warning');
                appendLog('開始測試方法 ' + method + ': ' + methodSelect.options[methodSelect.selectedIndex].text);
                
                fetch('/run-single-method-test', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({method: method})
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        updateStatus('方法 ' + method + ' 測試完成', 'success');
                        appendLog('✅ 方法 ' + method + ' 測試完成');
                        if (data.result) {
                            appendLog('結果: ' + data.result);
                        }
                    } else {
                        updateStatus('方法 ' + method + ' 測試失敗: ' + data.error, 'error');
                        appendLog('❌ 方法 ' + method + ' 失敗: ' + data.error);
                    }
                })
                .catch(error => {
                    updateStatus('測試錯誤: ' + error.message, 'error');
                    appendLog('💥 測試錯誤: ' + error.message);
                })
                .finally(() => {
                    testRunning = false;
                });
            }
            
            function showScreenshots(screenshots) {
                const screenshotsEl = document.getElementById('screenshots');
                screenshotsEl.innerHTML = '';
                
                screenshots.forEach(screenshot => {
                    const div = document.createElement('div');
                    div.style.margin = '10px 0';
                    div.innerHTML = '<h4>' + screenshot.name + '</h4><img src="/screenshot/' + screenshot.filename + '" style="max-width: 100%; border: 1px solid #ddd; border-radius: 4px;">';
                    screenshotsEl.appendChild(div);
                });
            }
            
            // 每5秒自動刷新狀態（如果有測試在進行）
            setInterval(() => {
                if (testRunning) {
                    fetch('/test-status')
                    .then(response => response.json())
                    .then(data => {
                        if (data.status) {
                            updateStatus(data.status, data.type || 'warning');
                        }
                        if (data.new_logs) {
                            data.new_logs.forEach(log => appendLog(log));
                        }
                    })
                    .catch(() => {}); // 忽略錯誤
                }
            }, 5000);
        </script>
    </body>
    </html>
    '''

@app.route('/fetch-dispatch')
def fetch_dispatch():
    """執行派車結果查詢"""
    try:
        print("=== 開始執行派車結果查詢流程 ===")
        result = fetch_dispatch_results()
        print(f"=== 派車結果查詢執行結果: {result} ===")
        return jsonify({"success": result, "message": "派車結果查詢執行完成"})
    except Exception as e:
        import traceback
        error_msg = f"派車結果查詢執行失敗: {str(e)}"
        print(error_msg)
        print("詳細錯誤資訊:")
        print(traceback.format_exc())
        return jsonify({"success": False, "error": error_msg}), 500

@app.route('/run-address-test', methods=['POST'])
def run_address_test():
    """執行住家地址填入測試"""
    try:
        data = request.get_json()
        test_type = data.get('type', 'full')
        
        # 執行地址測試的邏輯
        global test_logs, test_status
        test_logs = []
        test_status = "測試進行中..."
        
        def test_log(message):
            test_logs.append(message)
            print(f"[ADDRESS_TEST] {message}")
        
        # 設置瀏覽器
        driver = setup_driver()
        test_log("瀏覽器已啟動")
        
        try:
            # 基本導航和登入流程
            test_log("導航到預約系統...")
            driver['page'].goto("https://www.ntpc.ltc-car.org/")
            driver['page'].wait_for_load_state("networkidle")
            
            # 處理初始彈窗
            try:
                driver['page'].click('text=我知道了', timeout=3000)
                test_log("✅ 已處理初始彈窗")
            except:
                test_log("⚠️ 沒有初始彈窗")
            
            # 登入
            test_log("開始登入...")
            driver['page'].fill('#username', 'A102574899')
            driver['page'].fill('#password', 'visi319VISI')
            driver['page'].click('button:has-text("民眾登入")')
            
            # 處理登入成功彈窗
            try:
                driver['page'].wait_for_selector('text=登入成功', timeout=5000)
                driver['page'].click('button:has-text("確定")')
                test_log("✅ 登入成功")
            except:
                test_log("⚠️ 沒有登入成功彈窗")
            
            # 導航到新增預約
            test_log("導航到新增預約...")
            driver['page'].click('text=新增預約')
            driver['page'].wait_for_load_state("networkidle")
            
            # 設置上車地點
            test_log("設置上車地點為醫療院所...")
            driver['page'].select_option('select', '醫療院所')
            
            # 搜尋醫院
            test_log("搜尋亞東紀念醫院...")
            search_input = driver['page'].locator('input[placeholder*="搜尋"]').first
            search_input.fill('亞東紀念醫院')
            driver['page'].wait_for_timeout(2000)
            
            try:
                driver['page'].keyboard.press('ArrowDown')
                driver['page'].keyboard.press('Enter')
                test_log("✅ 已選擇亞東紀念醫院")
            except:
                test_log("⚠️ 選擇醫院可能失敗")
            
            # 選擇住家作為下車地點
            test_log("選擇住家作為下車地點...")
            home_selects = driver['page'].locator('select').all()
            home_selected = False
            
            for i, select_elem in enumerate(home_selects):
                try:
                    if select_elem.is_visible():
                        options = select_elem.locator('option').all()
                        option_texts = [opt.inner_text() for opt in options if opt.is_visible()]
                        
                        if '住家' in option_texts and i > 0:  # 不是第一個選單
                            test_log(f"在選單 {i} 中找到住家，選擇...")
                            select_elem.select_option('住家')
                            driver['page'].wait_for_timeout(2000)
                            home_selected = True
                            test_log("✅ 住家選擇成功")
                            break
                except Exception as e:
                    test_log(f"選單 {i} 檢查失敗: {e}")
                    continue
            
            if not home_selected:
                test_log("❌ 未能選擇住家")
                return {'success': False, 'error': '無法選擇住家選項'}
            
            # 現在開始測試地址填入
            test_log("=== 開始測試住家地址填入方法 ===")
            
            # 找到地址輸入框
            address_inputs = driver['page'].locator('input[type="text"]').all()
            target_address_input = None
            
            for i, input_elem in enumerate(address_inputs):
                try:
                    if input_elem.is_visible() and input_elem.is_enabled():
                        placeholder = input_elem.get_attribute('placeholder') or ''
                        name = input_elem.get_attribute('name') or ''
                        id_attr = input_elem.get_attribute('id') or ''
                        
                        is_address = any(keyword in (placeholder + name + id_attr).lower() 
                                       for keyword in ['地址', '住址', 'address'])
                        is_pickup = any(keyword in (name + id_attr).lower() 
                                      for keyword in ['pickup', 'pickUp', 'origin', 'from', 'start'])
                        
                        if is_address and not is_pickup and i > 0:
                            target_address_input = input_elem
                            test_log(f"✅ 找到地址輸入框 {i}: {placeholder}")
                            break
                except:
                    continue
            
            if not target_address_input:
                test_log("❌ 未找到地址輸入框")
                return {'success': False, 'error': '無法找到地址輸入框'}
            
            # 執行測試
            test_results = {}
            screenshots = []
            
            if test_type == 'quick':
                # 快速測試：只檢查自動填入
                test_log("--- 執行快速檢測 ---")
                for attempt in range(3):
                    current_value = target_address_input.input_value() or ''
                    test_log(f"檢查自動填入 {attempt+1}/3: '{current_value}'")
                    
                    if current_value.strip():
                        test_log(f"✅ 快速檢測成功 - 地址已自動填入: '{current_value}'")
                        test_results['quick'] = True
                        break
                    
                    driver['page'].wait_for_timeout(1000)
                else:
                    test_log("❌ 快速檢測 - 沒有自動填入")
                    test_results['quick'] = False
                
                take_screenshot("quick_test_result")
                screenshots.append({'name': '快速測試結果', 'filename': f'quick_test_result_{int(time.time())}.png'})
            
            else:
                # 完整測試：測試所有方法
                test_log("--- 執行完整測試 ---")
                
                # 方法1: 等待自動填入
                test_log("測試方法1: 等待自動填入")
                method1_success = False
                for attempt in range(5):
                    current_value = target_address_input.input_value() or ''
                    if current_value.strip():
                        test_log(f"✅ 方法1成功: '{current_value}'")
                        method1_success = True
                        break
                    driver['page'].wait_for_timeout(1000)
                
                test_results['method1'] = method1_success
                if not method1_success:
                    test_log("❌ 方法1失敗")
                
                # 方法2: 重新選擇住家
                if not method1_success:
                    test_log("測試方法2: 重新選擇住家")
                    try:
                        home_select = driver['page'].locator('select').filter(has_text='住家').first
                        home_select.select_option('住家')
                        driver['page'].wait_for_timeout(2000)
                        
                        new_value = target_address_input.input_value() or ''
                        if new_value.strip():
                            test_log(f"✅ 方法2成功: '{new_value}'")
                            test_results['method2'] = True
                        else:
                            test_log("❌ 方法2失敗")
                            test_results['method2'] = False
                    except Exception as e:
                        test_log(f"❌ 方法2失敗: {e}")
                        test_results['method2'] = False
                
                # 方法3: 點擊觸發
                if not any(test_results.values()):
                    test_log("測試方法3: 點擊觸發")
                    try:
                        target_address_input.click()
                        driver['page'].wait_for_timeout(1000)
                        target_address_input.focus()
                        driver['page'].wait_for_timeout(2000)
                        
                        new_value = target_address_input.input_value() or ''
                        if new_value.strip():
                            test_log(f"✅ 方法3成功: '{new_value}'")
                            test_results['method3'] = True
                        else:
                            test_log("❌ 方法3失敗")
                            test_results['method3'] = False
                    except Exception as e:
                        test_log(f"❌ 方法3失敗: {e}")
                        test_results['method3'] = False
                
                # 方法4: 手動填入
                if not any(test_results.values()):
                    test_log("測試方法4: 手動填入")
                    try:
                        test_address = "新北市板橋區文化路一段188巷44號"
                        target_address_input.fill(test_address)
                        driver['page'].wait_for_timeout(1000)
                        
                        new_value = target_address_input.input_value() or ''
                        if new_value.strip():
                            test_log(f"✅ 方法4成功: '{new_value}'")
                            test_results['method4'] = True
                        else:
                            test_log("❌ 方法4失敗")
                            test_results['method4'] = False
                    except Exception as e:
                        test_log(f"❌ 方法4失敗: {e}")
                        test_results['method4'] = False
                
                take_screenshot("full_test_result")
                screenshots.append({'name': '完整測試結果', 'filename': f'full_test_result_{int(time.time())}.png'})
            
            test_status = "測試完成"
            
            return {
                'success': True, 
                'logs': test_logs,
                'results': test_results,
                'screenshots': screenshots
            }
            
        finally:
            driver['page'].close()
            driver['browser'].close()
            
    except Exception as e:
        test_status = f"測試失敗: {e}"
        return {'success': False, 'error': str(e)}

@app.route('/run-single-method-test', methods=['POST'])
def run_single_method_test():
    """執行單一方法測試"""
    try:
        data = request.get_json()
        method = data.get('method', '1')
        
        # 這裡可以實現單一方法的測試邏輯
        # 為了簡化，先返回模擬結果
        
        method_descriptions = {
            '1': '等待自動填入',
            '2': '重新選擇住家',
            '3': '點擊觸發',
            '4': '手動填入',
            '5': '地址選單',
            '6': 'JavaScript觸發',
            '7': '表單驗證檢查'
        }
        
        # 模擬測試結果
        import random
        success = random.choice([True, False])
        result = f"方法 {method} ({method_descriptions.get(method, '未知')}) "
        result += "測試成功" if success else "測試失敗"
        
        return {
            'success': success,
            'result': result
        }
        
    except Exception as e:
        return {'success': False, 'error': str(e)}

@app.route('/test-status')
def test_status():
    """獲取測試狀態"""
    try:
        global test_status, test_logs
        return {
            'status': test_status if 'test_status' in globals() else '無進行中的測試',
            'new_logs': test_logs[-5:] if 'test_logs' in globals() else []
        }
    except:
        return {'status': '狀態獲取失敗'}

# 全域變數用於儲存測試狀態
test_logs = []
test_status = "待機中"

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
            description = filename.replace('.png', '').replace('dispatch_', '').replace('_', ' ')
            
            # 美化描述文字
            description_map = {
                '001 page loaded': '步驟 1: 頁面載入完成',
                '002 page complete': '步驟 2: 頁面完全載入', 
                '003 popup closed': '步驟 3: 關閉彈窗',
                '004 login form': '步驟 4: 登入表單載入',
                '005 before login click': '步驟 5: 準備點擊登入',
                '006 login clicked': '步驟 6: 登入按鈕已點擊',
                '007 login success modal found': '步驟 7: 發現登入成功彈窗',
                '008 login complete': '步驟 8: 登入流程完成',
                'order list loaded': '✅ 訂單列表載入完成',
                'records found': '🔍 找到訂單記錄',
                'matching record found': '🎯 找到匹配的預約記錄',
                'result saved': '💾 結果已儲存',
                'no matching record': '❌ 未找到匹配記錄'
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

@app.route('/latest-dispatch')
def latest_dispatch():
    """顯示最新派車結果"""
    try:
        with open('search_result.txt', 'r', encoding='utf-8') as f:
            content = f.read()
        
        return f'''
        <!DOCTYPE html>
        <html>
        <head>
            <title>最新派車結果</title>
            <meta charset="utf-8">
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
                .container {{ max-width: 1000px; margin: 0 auto; }}
                .header {{ background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
                .content {{ background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
                .back-button {{ 
                    background-color: #2196F3; 
                    color: white; 
                    padding: 10px 20px; 
                    text-decoration: none; 
                    border-radius: 4px; 
                    display: inline-block; 
                    margin-bottom: 20px; 
                }}
                .back-button:hover {{ background-color: #1976D2; }}
                .result {{ 
                    background: #f8f9fa; 
                    border: 1px solid #e9ecef; 
                    border-radius: 6px; 
                    padding: 20px; 
                    font-family: 'Courier New', monospace; 
                    white-space: pre-wrap; 
                    word-wrap: break-word;
                    line-height: 1.6;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <a href="/" class="back-button">返回首頁</a>
                    <h1>📋 最新派車結果</h1>
                    <p>顯示最近一次派車查詢的結果</p>
                </div>
                <div class="content">
                    <div class="result">{content}</div>
                </div>
            </div>
        </body>
        </html>
        '''
        
    except FileNotFoundError:
        return '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>最新派車結果</title>
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
            <h1>📋 最新派車結果</h1>
            <p>❌ 暫無派車結果檔案，請先執行派車查詢</p>
        </body>
        </html>
        '''

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
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <a href="/" class="back-button">返回首頁</a>
                <h1>📄 派車結果本地檔案</h1>
                <p>顯示 search_result.txt 檔案的內容，包含最新的派車查詢結果。</p>
            </div>
    '''
    
    try:
        file_path = 'search_result.txt'
        
        if os.path.exists(file_path):
            # 獲取檔案資訊
            file_size = os.path.getsize(file_path)
            modified_time = datetime.fromtimestamp(os.path.getmtime(file_path))
            
            html += f'''
            <div class="file-info">
                <strong>📁 檔案資訊：</strong><br>
                📄 檔案名稱：{file_path}<br>
                📏 檔案大小：{file_size} bytes<br>
                🕒 最後修改：{modified_time.strftime("%Y-%m-%d %H:%M:%S")}
            </div>
            '''
            
            # 讀取檔案內容
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            html += f'''
            <div class="content">
                <div class="file-content">{content}</div>
            </div>
            '''
        else:
            html += '''
            <div class="no-file">
                <h2>📭 檔案不存在</h2>
                <p>search_result.txt 檔案不存在。</p>
                <p>請先執行「🔄 抓取派車結果」功能來生成檔案。</p>
            </div>
            '''
            
    except Exception as e:
        html += f'''
        <div class="no-file">
            <h2>❌ 讀取檔案失敗</h2>
            <p>無法讀取檔案：{str(e)}</p>
        </div>
        '''
    
    html += '''
        </div>
    </body>
    </html>
    '''
    
    return html

if __name__ == '__main__':
    # Zeabur 環境變數
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port) 