# 派車結果查詢排程設定

## 概述
系統已設置自動排程執行派車結果查詢功能，會在指定時間自動抓取並儲存派車結果。

## 排程時間
- **執行頻率**：每週一和每週四
- **執行時間**：台灣時間 00:10 (午夜 12 點 10 分)
- **UTC 時間**：週日和週三的 16:10 (Zeabur 使用 UTC)

## 檔案結構

### 主要檔案
- `cron_dispatch.py` - 派車查詢排程腳本
- `zeabur.toml` - 包含 cron job 設定
- `app.py` - 包含派車查詢邏輯

### 日誌檔案
- `cron_dispatch.log` - 派車查詢執行日誌
- `search_result.txt` - 派車結果資料

## Cron Job 設定

在 `zeabur.toml` 中的設定：
```toml
[cron]
# 每週一和週四台灣時間 00:10 執行派車結果查詢
# 台灣週一 00:10 = 週日 16:10 UTC
# 台灣週四 00:10 = 週三 16:10 UTC
"10 16 * * 0,3" = "python3 cron_dispatch.py"
```

## 排程腳本功能

### cron_dispatch.py 腳本
- 自動調用 `fetch_dispatch_results()` 函數
- 使用台北時區記錄執行時間
- 產生詳細執行日誌
- 錯誤處理和異常紀錄

### 主要流程
1. 記錄開始執行時間 (台北時區)
2. 導入並執行派車結果查詢功能
3. 記錄執行結果
4. 產生日誌檔案

## Web 介面

### 新增頁面
- `/dispatch-cron-logs` - 查看派車查詢執行日誌
- `/dispatch-cron-logs/download` - 下載完整日誌
- `/dispatch-cron-logs/clear` - 清空日誌

### 首頁新增按鈕
- 📊 查看派車查詢日誌

## 監控和維護

### 日誌監控
- 透過 Web 介面查看執行狀態
- 自動重新整理頁面 (30秒)
- 顯示成功/失敗統計

### 檔案輸出
- `search_result.txt` 包含查詢結果
- 截圖檔案 `dispatch_*.png` 記錄執行過程

## 時區處理
- 所有時間戳記使用台北時區 (`Asia/Taipei`)
- Zeabur 平台使用 UTC，已進行時差轉換
- 確保查詢當天的預約記錄

## 錯誤處理
- 導入錯誤捕獲
- 執行異常記錄
- 即使沒找到記錄也視為正常執行

## 部署資訊
- 自動部署：推送到 GitHub 會觸發 Zeabur 重新部署
- Cron job 會在部署後自動啟用
- 無需手動重啟排程服務 