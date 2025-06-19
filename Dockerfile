FROM python:3.9-slim

# 安裝系統依賴
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    curl \
    --no-install-recommends \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

WORKDIR /app

COPY requirements.txt .
COPY app.py .
COPY cron_dispatch.py .
COPY static/ ./static/

# 安裝 Python 依賴
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# 安裝 Playwright 瀏覽器和依賴
RUN playwright install-deps
RUN playwright install chromium

# 設置環境變數
ENV DISPLAY=:99
ENV PYTHONUNBUFFERED=1

# 創建截圖目錄
RUN mkdir -p /app/screenshots

# 測試 Playwright 安裝
RUN python -c "from playwright.sync_api import sync_playwright; p = sync_playwright().start(); browser = p.chromium.launch(); browser.close(); p.stop(); print('Playwright 測試成功')"

CMD ["python", "app.py"] 