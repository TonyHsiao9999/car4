FROM python:3.9-slim

# 安裝系統依賴和 Chromium
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    curl \
    chromium \
    chromium-driver \
    --no-install-recommends \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# 設置工作目錄
WORKDIR /app

# 複製專案文件
COPY requirements.txt .
COPY app.py .
COPY static/ ./static/

# 安裝 Python 依賴
RUN pip install --no-cache-dir -r requirements.txt

# 設置環境變數
ENV DISPLAY=:99
ENV PYTHONUNBUFFERED=1
ENV CHROME_BIN=/usr/bin/chromium
ENV CHROMEDRIVER_PATH=/usr/bin/chromedriver
# 減少記憶體使用的環境變數
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONHASHSEED=random

# 創建截圖目錄
RUN mkdir -p /app/screenshots

# 啟動應用
CMD ["python", "app.py"] 