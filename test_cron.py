#!/usr/bin/env python3
"""
測試 Cron Job 腳本
用於驗證排程功能是否正常運作
"""

import subprocess
import sys
import os
from datetime import datetime

def test_cron_job():
    """測試 cron job 腳本"""
    print("=== 測試 Cron Job 排程腳本 ===")
    print(f"測試時間: {datetime.now()}")
    print()
    
    try:
        # 執行 cron_job.py
        print("正在執行 cron_job.py...")
        result = subprocess.run(
            [sys.executable, "cron_job.py"],
            capture_output=True,
            text=True,
            timeout=300  # 5分鐘超時
        )
        
        print(f"執行結果 - 返回碼: {result.returncode}")
        print()
        
        if result.stdout:
            print("標準輸出:")
            print(result.stdout)
            print()
        
        if result.stderr:
            print("錯誤輸出:")
            print(result.stderr)
            print()
        
        if result.returncode == 0:
            print("✅ Cron Job 測試成功")
        else:
            print("❌ Cron Job 測試失敗")
            
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        print("❌ 測試超時（超過5分鐘）")
        return False
        
    except Exception as e:
        print(f"❌ 測試過程發生錯誤: {e}")
        return False

def check_files():
    """檢查必要的檔案是否存在"""
    print("=== 檢查檔案 ===")
    
    files_to_check = [
        "cron_job.py",
        "app.py",
        "zeabur.toml"
    ]
    
    all_exist = True
    for file in files_to_check:
        if os.path.exists(file):
            print(f"✅ {file} - 存在")
        else:
            print(f"❌ {file} - 不存在")
            all_exist = False
    
    print()
    return all_exist

def main():
    """主函數"""
    print("開始 Cron Job 測試...")
    print()
    
    # 檢查檔案
    if not check_files():
        print("❌ 缺少必要檔案，測試終止")
        return 1
    
    # 測試 cron job
    if test_cron_job():
        print("🎉 所有測試通過！")
        return 0
    else:
        print("💥 測試失敗！")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 