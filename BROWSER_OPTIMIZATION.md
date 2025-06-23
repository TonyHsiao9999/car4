# 🚀 瀏覽器啟動優化方案

## 問題分析
原本的設計在每次網頁啟動時都會執行 `playwright install chromium`，這非常浪費時間（可能需要1-2分鐘）。

## 🎯 優化方案

### 方案1：智能檢查模式（預設）
- **特點**：先檢查瀏覽器是否已安裝，只在必要時才下載
- **優勢**：第一次啟動會下載，之後啟動都很快
- **使用方式**：設置 `FAST_BROWSER_MODE=false` 或不設置

### 方案2：快速模式（推薦）⚡
- **特點**：完全跳過運行時下載，直接使用 Docker 預安裝的瀏覽器
- **優勢**：啟動速度最快，5-10秒完成
- **使用方式**：設置 `FAST_BROWSER_MODE=true`

## 🔧 如何啟用快速模式

### 在 Render.com 部署
快速模式已經在 `render.yaml` 和 `Dockerfile.playwright` 中啟用：

```yaml
envVars:
  - key: FAST_BROWSER_MODE
    value: true
```

### 本地測試
```bash
export FAST_BROWSER_MODE=true
python app.py
```

### Docker 部署
```bash
docker build -f Dockerfile.playwright -t car4-app .
docker run -e FAST_BROWSER_MODE=true -p 8080:10000 car4-app
```

## 📊 性能對比

| 模式 | 首次啟動 | 後續啟動 | 瀏覽器下載 |
|------|----------|----------|------------|
| 原始版本 | 120秒 | 120秒 | 每次都下載 |
| 智能檢查 | 120秒 | 15秒 | 只下載一次 |
| 快速模式 | 10秒 | 10秒 | 構建時預安裝 |

## ⚙️ 技術細節

### 快速模式的關鍵
1. **Dockerfile 預安裝**：
   ```dockerfile
   RUN python -m playwright install chromium
   RUN python -m playwright install-deps chromium
   ```

2. **跳過運行時檢查**：
   ```python
   if os.environ.get('FAST_BROWSER_MODE', 'false').lower() == 'true':
       driver = setup_driver_fast()  # 直接啟動，不下載
   ```

3. **優化的瀏覽器參數**：
   - `--single-process`：避免多進程問題
   - `--no-sandbox`：容器環境必需
   - 15秒啟動超時：快速失敗

## 🛠️ 故障排除

### 如果快速模式失敗
1. 檢查 Dockerfile 是否正確構建瀏覽器
2. 確認環境變數設置正確
3. 可以暫時切換回標準模式：`FAST_BROWSER_MODE=false`

### 日誌關鍵字
- ✅ `使用快速瀏覽器模式`：快速模式啟用
- ✅ `直接啟動預安裝瀏覽器`：跳過下載
- ❌ `快速模式失敗`：回退到標準模式

## 📈 推薦設置

**生產環境（Render.com）**：
```yaml
FAST_BROWSER_MODE: true
```

**開發環境**：
```bash
export FAST_BROWSER_MODE=true  # 如果有 Docker
export FAST_BROWSER_MODE=false # 如果本地開發
```

---

**重要提醒**：使用快速模式時，請確保使用 `Dockerfile.playwright` 而不是其他 Dockerfile，因為只有這個版本有預安裝瀏覽器。 