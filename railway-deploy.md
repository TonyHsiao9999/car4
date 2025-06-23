# 🚂 Railway 部署指南

## 為什麼選擇 Railway？

✅ **真正的 Docker 支援** - 沒有 debconf 限制  
✅ **免費額度充足** - $5/月，約 500 小時  
✅ **支援 Cron Jobs** - 內建排程功能  
✅ **GitHub 自動部署** - 推送即部署  
✅ **無平台限制** - 支援任何 Dockerfile  

## 🚀 快速部署步驟

### 1. 註冊 Railway
- 前往：https://railway.app
- 使用 GitHub 帳號登入

### 2. 創建新專案
1. 點擊 "New Project"
2. 選擇 "Deploy from GitHub repo"
3. 選擇你的 `car4` 倉庫
4. 點擊 "Deploy Now"

### 3. 配置環境變數
在 Railway 控制台中設置：
```
PORT=8080
PYTHONUNBUFFERED=1
TZ=Asia/Taipei
```

### 4. 選擇 Dockerfile
Railway 會自動偵測到多個 Dockerfile，選擇：
- **推薦**：`Dockerfile.slim`
- **備選**：`Dockerfile.ultra-alpine`

### 5. 設置 Cron Jobs
1. 在專案中點擊 "New"
2. 選擇 "Empty Service"
3. 連接同一個 GitHub 倉庫
4. 在設置中添加：
   ```
   Start Command: python cron_job.py
   Cron Schedule: 1 16 * * 0,3
   ```

## 🎯 Railway 專用配置檔案

我們已經有完美的 Docker 配置： 