#!/usr/bin/env python3
"""
Zeabur Cron Job 排程腳本
每週一和週四 00:01 自動執行預約

使用方式：
- 在 zeabur.toml 中設定 cron job
- 此腳本會直接調用預約功能，無需 HTTP 請求
"""

import sys
import os
import logging
from datetime import datetime

# 添加當前目錄到 Python 路徑
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('cron_reservation.log'),
        logging.StreamHandler()
    ]
)

def main():
    """主要執行函數"""
    try:
        logging.info("=== 開始執行排程預約 ===")
        logging.info(f"執行時間: {datetime.now()}")
        
        # 導入 app.py 中的預約函數
        from app import make_reservation
        
        # 執行預約
        result = make_reservation()
        
        if result:
            logging.info("✅ 排程預約執行成功")
            print("SUCCESS: 預約完成")
            return 0
        else:
            logging.error("❌ 排程預約執行失敗")
            print("FAILED: 預約失敗")
            return 1
            
    except ImportError as e:
        logging.error(f"導入錯誤: {e}")
        print(f"IMPORT_ERROR: {e}")
        return 1
        
    except Exception as e:
        logging.error(f"執行錯誤: {e}")
        print(f"ERROR: {e}")
        return 1
    
    finally:
        logging.info("=== 排程預約執行結束 ===")

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 