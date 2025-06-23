# Render.com 部署指南

## 🚀 部署到 Render.com

### 方法一：使用 render.yaml 自動配置

1. **推送代碼到 GitHub**
   ```bash
   git add .
   git commit -m "Add Render.com deployment configuration"
   git push origin master
   ```

2. **在 Render.com 創建服務**
   - 前往 [render.com](https://render.com)
   - 註冊/登入帳號
   - 點擊 "New +" → "Blueprint"
   - 連接 GitHub 倉庫：選擇您的 car4 倉庫
   - Render 會自動讀取 `render.yaml` 並創建：
     - Web Service (主應用)
     - 2個 Cron Jobs (預約和派車查詢)

### 方法二：手動創建服務

#### 1. 創建 Web Service
- 點擊 "New +" → "Web Service"
- 連接 GitHub 倉庫
- 配置：
  - **Name**: `car4-ltc`
  - **Environment**: `Docker`
  - **Dockerfile Path**: `./Dockerfile`
  - **Plan**: `Starter` (免費)

#### 2. 環境變數設置
在 Environment 頁面添加：
```
PORT=10000
PYTHONUNBUFFERED=1
DISPLAY=:99
```

#### 3. 創建定時任務 (Cron Jobs)

**預約任務**：
- **Name**: `car4-reservation-cron`
- **Environment**: `Docker`
- **Schedule**: `1 16 * * 0,3`
- **Command**: `python cron_job.py`

**派車查詢任務**：
- **Name**: `car4-dispatch-cron`
- **Environment**: `Docker`  
- **Schedule**: `10 16 * * 0,3`
- **Command**: `python cron_dispatch.py`

## ⏰ 定時任務說明

- **預約**: 週一和週四台灣時間 00:01 (UTC 16:01)
- **派車查詢**: 週一和週四台灣時間 00:10 (UTC 16:10)
- 時區轉換：台灣 UTC+8，Render 使用 UTC

## 🔧 技術特點

### Docker 優化
- 使用 Python 3.9 slim 映像
- 安裝 Playwright + Chromium 
- 包含 Xvfb 虛擬顯示器
- 優化 Docker 層快取

### Playwright 配置
- Headless Chrome 瀏覽器
- 1920x1080 解析度
- 無沙盒模式 (適用容器環境)
- 自動截圖功能

### 應用功能
- 🏠 **精美首頁**: 分區功能介面
- 📅 **智能預約**: 自動選擇時段和地址
- 🚗 **派車查詢**: 全方位狀態分析，不限記錄數量
- 📸 **截圖記錄**: 完整操作過程記錄
- 📊 **詳細日誌**: 即時狀態和錯誤追蹤

## 🌐 訪問網址

部署完成後，您可以通過以下網址訪問：
- `https://your-service-name.onrender.com`

## 🔍 監控和日誌

- Render 提供即時日誌查看
- 可在 Dashboard 監控服務狀態
- 支援自動重啟和健康檢查

## ⚠️ 注意事項

1. **免費方案限制**：
   - 服務會在15分鐘無活動後休眠
   - 首次訪問可能需要冷啟動時間

2. **Playwright 資源**：
   - Chrome 瀏覽器需要較多記憶體
   - 建議監控資源使用情況

3. **定時任務**：
   - Cron Jobs 在免費方案有限制
   - 建議升級到付費方案以獲得更好的可靠性

## 🆙 升級建議

如需更穩定的服務，建議升級到：
- **Starter Plan**: $7/月，無休眠限制
- **Standard Plan**: $25/月，更多資源和功能 