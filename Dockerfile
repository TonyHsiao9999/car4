FROM python:3.9-slim

# 安裝系統依賴
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    curl \
    xvfb \
    --no-install-recommends \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

WORKDIR /app

# 先複製requirements.txt以利用Docker快取
COPY requirements.txt .

# 安裝 Python 依賴
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# 安裝 Playwright 瀏覽器和依賴
RUN playwright install-deps
RUN playwright install chromium

# 複製應用程式檔案
COPY app.py .
COPY cron_dispatch.py .
COPY cron_job.py .
COPY src/ ./src/
COPY static/ ./static/

# 設置環境變數
ENV DISPLAY=:99
ENV PYTHONUNBUFFERED=1
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

# 創建截圖目錄
RUN mkdir -p /app/screenshots

# 測試 Playwright 安裝
RUN python -c "from playwright.sync_api import sync_playwright; p = sync_playwright().start(); browser = p.chromium.launch(); browser.close(); p.stop(); print('Playwright 測試成功')"

# 創建啟動腳本
RUN echo '#!/bin/bash\nXvfb :99 -screen 0 1920x1080x24 &\nexec "$@"' > /app/start.sh && chmod +x /app/start.sh

# 暴露端口
EXPOSE $PORT

CMD ["/app/start.sh", "python", "app.py"] 