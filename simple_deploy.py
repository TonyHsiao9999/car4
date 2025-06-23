#!/usr/bin/env python3

import os
import sys
from flask import Flask, render_template_string

app = Flask(__name__)

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

# 簡化版首頁模板
home_template = """
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>新北市長照交通接送預約系統</title>
    <style>
        body {
            font-family: 'Microsoft YaHei', Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: rgba(255, 255, 255, 0.95);
            border-radius: 15px;
            padding: 30px;
            box-shadow: 0 15px 35px rgba(0, 0, 0, 0.1);
        }
        h1 {
            text-align: center;
            color: #2c3e50;
            margin-bottom: 40px;
            font-size: 2.5em;
        }
        .feature-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 30px;
            margin-top: 30px;
        }
        .feature-card {
            background: white;
            padding: 25px;
            border-radius: 10px;
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
            transition: transform 0.3s ease;
        }
        .feature-card:hover {
            transform: translateY(-5px);
        }
        .feature-title {
            font-size: 1.3em;
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 15px;
        }
        .btn {
            display: inline-block;
            padding: 12px 24px;
            background: #3498db;
            color: white;
            text-decoration: none;
            border-radius: 6px;
            transition: background 0.3s ease;
            margin: 5px;
        }
        .btn:hover {
            background: #2980b9;
        }
        .status {
            padding: 20px;
            background: #e8f5e8;
            border-radius: 8px;
            margin: 20px 0;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🚗 新北市長照交通接送預約系統</h1>
        
        <div class="status">
            <h3>🎯 系統狀態</h3>
            <p><strong>部署環境:</strong> {{ environment }}</p>
            <p><strong>Python 版本:</strong> {{ python_version }}</p>
            <p><strong>運行端口:</strong> {{ port }}</p>
            <p><strong>系統時間:</strong> {{ current_time }}</p>
        </div>

        <div class="feature-grid">
            <div class="feature-card">
                <div class="feature-title">📅 預約功能</div>
                <p>自動化預約新北市長照交通接送服務</p>
                <a href="/reservation" class="btn">開始預約</a>
                <a href="/screenshots" class="btn">查看預約截圖</a>
            </div>

            <div class="feature-card">
                <div class="feature-title">🚛 派車查詢</div>
                <p>查詢已派車的記錄和詳細資訊</p>
                <a href="/fetch-dispatch" class="btn">抓取派車結果</a>
                <a href="/latest-dispatch" class="btn">看最新派車結果</a>
                <a href="/dispatch-screenshots" class="btn">查看派車截圖</a>
            </div>

            <div class="feature-card">
                <div class="feature-title">📊 系統日誌</div>
                <p>查看系統運行記錄和錯誤日誌</p>
                <a href="/logs/reservation" class="btn">查看預約日誌</a>
                <a href="/logs/dispatch" class="btn">查看派車查詢日誌</a>
            </div>

            <div class="feature-card">
                <div class="feature-title">⏰ 排程狀態</div>
                <p>查看自動化排程的運行狀態</p>
                <a href="/cron-status" class="btn">查看排程狀態</a>
                <a href="/test" class="btn">測試連線</a>
            </div>
        </div>
    </div>
</body>
</html>
"""

@app.route('/')
def home():
    import datetime
    return render_template_string(home_template, 
        environment="Render.com" if os.environ.get('RENDER') else "Local",
        python_version=sys.version,
        port=os.environ.get('PORT', '5000'),
        current_time=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    )

@app.route('/test')
def test():
    return {
        'status': 'success',
        'message': '系統運行正常',
        'environment': 'Render.com' if os.environ.get('RENDER') else 'Local',
        'port': os.environ.get('PORT', '5000')
    }

@app.route('/health')
def health():
    return {'status': 'healthy'}

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    host = '0.0.0.0' if os.environ.get('RENDER') else '127.0.0.1'
    debug = not bool(os.environ.get('RENDER'))
    
    print(f"🚀 啟動簡化版長照交通接送系統")
    print(f"📍 運行地址: {host}:{port}")
    print(f"🔧 除錯模式: {debug}")
    print(f"☁️ Render 環境: {bool(os.environ.get('RENDER'))}")
    
    app.run(host=host, port=port, debug=debug) 