#!/usr/bin/env python3

import os
import sys

# 將test_simple.py重命名為app.py來部署
if __name__ == '__main__':
    # 檢查是否有test_simple.py
    if os.path.exists('test_simple.py'):
        # 備份原始app.py
        if os.path.exists('app.py'):
            os.rename('app.py', 'app_backup.py')
            print("已備份原始app.py為app_backup.py")
        
        # 複製test_simple.py為app.py
        import shutil
        shutil.copy2('test_simple.py', 'app.py')
        print("已將test_simple.py設置為app.py")
        print("現在可以部署到Zeabur進行測試")
    else:
        print("找不到test_simple.py檔案") 