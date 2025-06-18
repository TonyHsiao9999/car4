# 長照交通接送預約系統

這是一個自動化的長照交通接送預約系統，使用 Selenium 進行網頁自動化操作。

## 功能特色

- 🔄 自動化預約流程
- 📸 詳細的截圖記錄
- 🌐 網頁介面查看截圖
- 📱 響應式設計
- 🔍 頁面原始碼查看

## 部署方式

### Zeabur 雲端部署 (推薦)

1. **Fork 或 Clone 此專案**
   ```bash
   git clone https://github.com/your-username/car4.git
   cd car4
   ```

2. **推送到 GitHub**
   ```bash
   git add .
   git commit -m "Initial commit"
   git push origin main
   ```

3. **在 Zeabur 部署**
   - 前往 [Zeabur](https://zeabur.com)
   - 註冊/登入帳號
   - 點擊 "New Project"
   - 選擇 "GitHub" 並連接您的 GitHub 帳號
   - 選擇此專案
   - 點擊 "Deploy"

4. **等待部署完成**
   - Zeabur 會自動建置 Docker 映像
   - 部署完成後會提供一個網址

### 本地開發

1. **安裝依賴**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # Linux/Mac
   # 或 venv\Scripts\activate  # Windows
   pip install -r requirements.txt
   ```

2. **運行應用**
   ```bash
   python app.py
   ```

3. **訪問應用**
   - 打開瀏覽器訪問 `http://localhost:8080`

## 使用方式

### 網頁介面

1. **首頁** (`/`)
   - 開始預約：執行自動化預約流程
   - 查看截圖：瀏覽所有截圖
   - 查看頁面原始碼：檢查網頁結構

2. **截圖頁面** (`/screenshots`)
   - 按時間順序顯示所有截圖
   - 每個截圖都有詳細描述
   - 支援圖片放大查看

3. **頁面原始碼** (`/page_source`)
   - 顯示最後執行的頁面原始碼
   - 方便除錯和檢查元素

### API 端點

- `GET /` - 首頁
- `GET /reserve` - 執行預約流程
- `GET /screenshots` - 查看截圖頁面
- `GET /screenshot/<filename>` - 下載特定截圖
- `GET /page_source` - 查看頁面原始碼

## 技術架構

- **後端**: Python Flask
- **自動化**: Selenium WebDriver
- **瀏覽器**: Chrome (Headless)
- **部署**: Docker + Zeabur
- **前端**: HTML + CSS

## 檔案結構

```
car4/
├── app.py              # 主應用程式
├── requirements.txt    # Python 依賴
├── Dockerfile         # Docker 設定
├── zeabur.toml        # Zeabur 設定
├── .dockerignore      # Docker 忽略檔案
├── README.md          # 說明文件
└── static/            # 靜態檔案
    └── favicon.ico    # 網站圖示
```

## 環境變數

- `PORT`: 應用程式端口 (預設: 8080)
- `CHROME_BIN`: Chrome 瀏覽器路徑
- `CHROMEDRIVER_PATH`: ChromeDriver 路徑

## 注意事項

1. **Chrome 安裝**: 系統會自動安裝 Chrome 和 ChromeDriver
2. **截圖儲存**: 截圖會儲存在應用程式根目錄
3. **記憶體使用**: 建議至少 512MB RAM
4. **網路連線**: 需要穩定的網路連線

## 除錯

如果遇到問題：

1. 檢查截圖頁面了解執行過程
2. 查看頁面原始碼檢查元素
3. 檢查 Zeabur 日誌
4. 確認網路連線正常

## 授權

MIT License # Force rebuild 2025年 6月18日 週三 15時16分02秒 CST
