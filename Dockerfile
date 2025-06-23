FROM python:3.9-slim

# 安裝系統依賴
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    curl \
    xvfb \
    libnss3 \
    libatk-bridge2.0-0 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libgbm1 \
    libxss1 \
    libasound2 \
    libatspi2.0-0 \
    libgtk-3-0 \
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
ENV PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1

# 創建截圖目錄
RUN mkdir -p /app/screenshots

# 創建啟動腳本
RUN echo '#!/bin/bash\n\
# 啟動虛擬顯示器\n\
Xvfb :99 -screen 0 1920x1080x24 -ac +extension GLX +render -noreset &\n\
export DISPLAY=:99\n\
\n\
# 等待虛擬顯示器啟動\n\
sleep 2\n\
\n\
# 執行程式\n\
exec "$@"' > /app/start.sh && chmod +x /app/start.sh

# 暴露端口
EXPOSE $PORT

CMD ["/app/start.sh", "python", "app.py"] 