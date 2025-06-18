#!/usr/bin/env python3
"""
測試住家地址填入的各種方法
用於調試和驗證不同的地址自動填入方案
"""

import sys
from playwright.sync_api import sync_playwright
import time

def test_address_methods():
    """測試各種住家地址填入方法"""
    
    with sync_playwright() as p:
        # 啟動瀏覽器（測試模式）
        browser = p.chromium.launch(headless=False, slow_mo=1000)
        page = browser.new_page()
        
        try:
            # 導航到預約頁面
            print("正在導航到預約系統...")
            page.goto("https://trms.care.tphd.tpc.gov.tw/TRMS/Html/Index.html")
            
            # 等待頁面載入
            page.wait_for_load_state("networkidle")
            
            # 處理初始彈窗
            print("處理初始彈窗...")
            try:
                page.click('text=我知道了', timeout=3000)
                print("✅ 已點擊'我知道了'")
            except:
                print("⚠️ 沒有找到初始彈窗")
            
            # 登入
            print("開始登入...")
            page.fill('#username', 'A102574899')
            page.fill('#password', 'visi319VISI')
            
            # 點擊民眾登入
            page.click('button:has-text("民眾登入")')
            
            # 處理登入成功彈窗
            try:
                page.wait_for_selector('text=登入成功', timeout=5000)
                page.click('button:has-text("確定")')
                print("✅ 登入成功")
            except:
                print("⚠️ 沒有登入成功彈窗或處理失敗")
            
            # 導航到新增預約
            print("導航到新增預約...")
            page.click('text=新增預約')
            page.wait_for_load_state("networkidle")
            
            # 設置上車地點為醫療院所
            print("設置上車地點...")
            page.select_option('select', '醫療院所')
            
            # 搜尋亞東紀念醫院
            print("搜尋亞東紀念醫院...")
            search_input = page.locator('input[placeholder*="搜尋"]').first
            search_input.fill('亞東紀念醫院')
            page.wait_for_timeout(2000)
            
            # 選擇搜尋結果
            try:
                page.keyboard.press('ArrowDown')
                page.keyboard.press('Enter')
                print("✅ 已選擇亞東紀念醫院")
            except:
                print("⚠️ 選擇醫院失敗，但繼續測試")
            
            # 現在測試下車地點住家選擇
            print("\n=== 開始測試住家地址填入方法 ===")
            
            # 選擇住家作為下車地點
            print("選擇住家作為下車地點...")
            home_selects = page.locator('select').all()
            for i, select_elem in enumerate(home_selects):
                try:
                    options = select_elem.locator('option').all()
                    option_texts = [opt.inner_text() for opt in options]
                    
                    if '住家' in option_texts and i > 0:  # 不是第一個選單
                        print(f"在選單 {i} 中找到住家，選擇...")
                        select_elem.select_option('住家')
                        page.wait_for_timeout(2000)
                        break
                except:
                    continue
            
            # 現在開始測試地址填入方法
            print("\n--- 測試方法1：等待自動填入 ---")
            address_inputs = page.locator('input[type="text"]').all()
            target_address_input = None
            
            # 找到地址輸入框
            for i, input_elem in enumerate(address_inputs):
                try:
                    if input_elem.is_visible():
                        placeholder = input_elem.get_attribute('placeholder') or ''
                        name = input_elem.get_attribute('name') or ''
                        
                        if '地址' in placeholder or 'address' in name.lower():
                            if 'pickup' not in name.lower():
                                target_address_input = input_elem
                                print(f"✅ 找到地址輸入框: {placeholder}")
                                break
                except:
                    continue
            
            if target_address_input:
                # 檢查自動填入
                for attempt in range(5):
                    current_value = target_address_input.input_value() or ''
                    print(f"檢查自動填入 {attempt+1}/5: '{current_value}'")
                    
                    if current_value.strip():
                        print(f"✅ 方法1成功 - 自動填入: '{current_value}'")
                        break
                    
                    page.wait_for_timeout(1000)
                else:
                    print("❌ 方法1失敗 - 沒有自動填入")
                    
                    # 測試方法2：重新選擇住家
                    print("\n--- 測試方法2：重新選擇住家 ---")
                    try:
                        home_select = page.locator('select').filter(has_text='住家').first
                        home_select.select_option('住家')
                        page.wait_for_timeout(2000)
                        
                        new_value = target_address_input.input_value() or ''
                        if new_value.strip():
                            print(f"✅ 方法2成功 - 重新選擇觸發: '{new_value}'")
                        else:
                            print("❌ 方法2失敗")
                    except Exception as e:
                        print(f"❌ 方法2失敗: {e}")
                    
                    # 測試方法3：點擊觸發
                    print("\n--- 測試方法3：點擊地址框觸發 ---")
                    try:
                        target_address_input.click()
                        page.wait_for_timeout(1000)
                        target_address_input.focus()
                        page.wait_for_timeout(2000)
                        
                        new_value = target_address_input.input_value() or ''
                        if new_value.strip():
                            print(f"✅ 方法3成功 - 點擊觸發: '{new_value}'")
                        else:
                            print("❌ 方法3失敗")
                    except Exception as e:
                        print(f"❌ 方法3失敗: {e}")
                    
                    # 測試方法4：手動填入
                    print("\n--- 測試方法4：手動填入地址 ---")
                    try:
                        test_address = "新北市板橋區文化路一段188巷44號"
                        target_address_input.fill(test_address)
                        page.wait_for_timeout(1000)
                        
                        new_value = target_address_input.input_value() or ''
                        if new_value.strip():
                            print(f"✅ 方法4成功 - 手動填入: '{new_value}'")
                        else:
                            print("❌ 方法4失敗")
                    except Exception as e:
                        print(f"❌ 方法4失敗: {e}")
                    
                    # 測試方法5：JavaScript觸發
                    print("\n--- 測試方法5：JavaScript觸發 ---")
                    try:
                        js_script = """
                        // 觸發住家地址自動填入
                        const addressInputs = document.querySelectorAll('input[type="text"]');
                        let success = false;
                        
                        addressInputs.forEach((input, index) => {
                            const placeholder = input.placeholder || '';
                            const name = input.name || '';
                            
                            if ((placeholder.includes('地址') || name.includes('address')) && 
                                !name.includes('pickup') && index > 0) {
                                if (!input.value.trim()) {
                                    input.value = '新北市板橋區文化路一段188巷44號';
                                    input.dispatchEvent(new Event('input', {bubbles: true}));
                                    input.dispatchEvent(new Event('change', {bubbles: true}));
                                    success = true;
                                }
                            }
                        });
                        
                        return success;
                        """
                        
                        result = page.evaluate(js_script)
                        if result:
                            page.wait_for_timeout(1000)
                            new_value = target_address_input.input_value() or ''
                            print(f"✅ 方法5成功 - JavaScript填入: '{new_value}'")
                        else:
                            print("❌ 方法5失敗")
                    except Exception as e:
                        print(f"❌ 方法5失敗: {e}")
            
            else:
                print("❌ 未找到地址輸入框")
            
            print("\n=== 地址填入測試完成 ===")
            print("請查看瀏覽器視窗中的結果")
            
            # 暫停讓用戶查看結果
            input("按 Enter 鍵結束測試...")
            
        except Exception as e:
            print(f"測試過程發生錯誤: {e}")
        
        finally:
            browser.close()

if __name__ == "__main__":
    test_address_methods() 