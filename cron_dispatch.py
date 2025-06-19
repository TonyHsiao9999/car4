#!/usr/bin/env python3
"""
Zeabur Cron Job 排程腳本 - 派車結果查詢
每週一和週四 00:10 自動執行派車結果查詢

使用方式：
- 在 zeabur.toml 中設定 cron job
- 此腳本會直接調用派車結果查詢功能，無需 HTTP 請求
"""

import sys
import os
import logging
from datetime import datetime
import pytz

# 添加當前目錄到 Python 路徑
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('cron_dispatch.log'),
        logging.StreamHandler()
    ]
)

def main():
    """主要執行函數"""
    try:
        # 使用台北時區記錄時間
        taipei_tz = pytz.timezone('Asia/Taipei')
        current_time = datetime.now(taipei_tz)
        
        logging.info("=== 開始執行排程派車結果查詢 ===")
        logging.info(f"執行時間: {current_time.strftime('%Y-%m-%d %H:%M:%S')} (台北時區)")
        
        # 導入 app.py 中的派車結果查詢函數
        from app import fetch_dispatch_results
        
        # 執行派車結果查詢
        result = fetch_dispatch_results()
        
        if result:
            logging.info("✅ 排程派車結果查詢執行成功")
            print("SUCCESS: 派車結果查詢完成")
            return 0
        else:
            logging.info("ℹ️ 排程派車結果查詢執行完成（可能未找到記錄）")
            print("COMPLETED: 派車結果查詢完成")
            return 0  # 即使沒找到記錄也算成功執行
            
    except ImportError as e:
        logging.error(f"導入錯誤: {e}")
        print(f"IMPORT_ERROR: {e}")
        return 1
        
    except Exception as e:
        logging.error(f"執行錯誤: {e}")
        print(f"ERROR: {e}")
        return 1
    
    finally:
        taipei_tz = pytz.timezone('Asia/Taipei')
        end_time = datetime.now(taipei_tz)
        logging.info(f"=== 排程派車結果查詢執行結束 {end_time.strftime('%Y-%m-%d %H:%M:%S')} ===")

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 