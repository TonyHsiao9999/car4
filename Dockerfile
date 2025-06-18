FROM ubuntu:22.04

# 避免互動式安裝
ENV DEBIAN_FRONTEND=noninteractive

# 安裝 Python3、pip、chromium 及相關依賴
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    wget \
    gnupg \
    unzip \
    curl \
    chromium-browser \
    chromium-chromedriver \
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
RUN pip3 install --no-cache-dir -r requirements.txt

# 設置環境變數
ENV DISPLAY=:99
ENV PYTHONUNBUFFERED=1
ENV CHROME_BIN=/usr/bin/chromium-browser
ENV CHROMEDRIVER_PATH=/usr/bin/chromedriver
# 減少記憶體使用的環境變數
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONHASHSEED=random

# 創建截圖目錄
RUN mkdir -p /app/screenshots

# 啟動應用
CMD ["python3", "app.py"] 