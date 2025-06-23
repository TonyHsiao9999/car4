#!/usr/bin/env python3
"""
測試 Playwright 瀏覽器是否正確安裝和可用
"""

import os
import sys
from playwright.sync_api import sync_playwright

def test_browser():
    """測試瀏覽器可用性"""
    print("🔍 測試 Playwright 瀏覽器...")
    
    # 檢查環境變數
    print(f"PLAYWRIGHT_BROWSERS_PATH: {os.environ.get('PLAYWRIGHT_BROWSERS_PATH', 'Not set')}")
    
    try:
        playwright = sync_playwright().start()
        
        # 檢查可執行檔路徑
        chromium_path = playwright.chromium.executable_path
        print(f"✅ Chromium 路徑: {chromium_path}")
        
        # 檢查檔案是否存在
        if os.path.exists(chromium_path):
            print("✅ Chromium 可執行檔存在")
        else:
            print("❌ Chromium 可執行檔不存在")
            return False
        
        # 嘗試啟動瀏覽器
        print("⚡ 嘗試啟動瀏覽器...")
        browser = playwright.chromium.launch(headless=True)
        print("✅ 瀏覽器啟動成功")
        
        # 測試基本功能
        page = browser.new_page()
        page.goto("https://example.com")
        title = page.title()
        print(f"✅ 頁面標題: {title}")
        
        browser.close()
        playwright.stop()
        
        print("🎉 所有測試通過！")
        return True
        
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        return False

if __name__ == "__main__":
    success = test_browser()
    sys.exit(0 if success else 1) 