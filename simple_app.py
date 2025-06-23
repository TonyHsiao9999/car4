from flask import Flask
import os

app = Flask(__name__)

@app.route('/')
def index():
    return '''
    <!DOCTYPE html>
    <html lang="zh-TW">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>長照交通接送預約系統 - 測試版</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; }
            .container { max-width: 800px; margin: 0 auto; background: white; border-radius: 15px; padding: 30px; box-shadow: 0 10px 30px rgba(0,0,0,0.3); }
            h1 { color: #2c3e50; text-align: center; margin-bottom: 30px; }
            .status { background: #d4edda; border: 1px solid #c3e6cb; border-radius: 8px; padding: 15px; margin: 20px 0; }
            .info { background: #cce5ff; border: 1px solid #b3d9ff; border-radius: 8px; padding: 15px; margin: 20px 0; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🚗 長照交通接送預約系統</h1>
            
            <div class="status">
                <h3>✅ 系統狀態</h3>
                <p><strong>平台：</strong> Render.com 原生 Python 環境</p>
                <p><strong>狀態：</strong> 基本服務運行正常</p>
                <p><strong>測試時間：</strong> 系統已成功部署</p>
            </div>
            
            <div class="info">
                <h3>📋 測試報告</h3>
                <p>✅ Flask 應用程式正常運行</p>
                <p>✅ 沒有 Term::ReadLine 錯誤</p>
                <p>✅ 原生 Python 環境部署成功</p>
                <p>⏳ Playwright 功能待修復</p>
            </div>
            
            <div class="info">
                <h3>🔧 下一步計劃</h3>
                <p>1. 確認基本 Flask 服務穩定運行</p>
                <p>2. 逐步加入 Playwright 功能</p>
                <p>3. 或考慮遷移到 Railway.app 平台</p>
            </div>
        </div>
    </body>
    </html>
    '''

@app.route('/health')
def health():
    return {'status': 'ok', 'message': '系統運行正常'}

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port) 