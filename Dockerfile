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
COPY static/ ./static/

# 安裝 Python 依賴
RUN pip install --no-cache-dir -r requirements.txt

# 安裝 Playwright 瀏覽器
RUN playwright install chromium

# 設置環境變數
ENV DISPLAY=:99
ENV PYTHONUNBUFFERED=1

# 創建截圖目錄
RUN mkdir -p /app/screenshots

CMD ["python", "app.py"] 