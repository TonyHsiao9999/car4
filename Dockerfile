FROM python:3.9-slim

# 安裝系統依賴（減少記憶體使用）
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    curl \
    ca-certificates \
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 \
    libdrm2 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    xdg-utils \
    --no-install-recommends \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# 安裝最新版本的 Chrome（不指定版本）
RUN wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | gpg --dearmor -o /usr/share/keyrings/google-chrome.gpg \
    && echo "deb [arch=amd64 signed-by=/usr/share/keyrings/google-chrome.gpg] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable --no-install-recommends \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# 下載最新版本的 ChromeDriver
RUN wget -q "https://chromedriver.storage.googleapis.com/LATEST_RELEASE" -O /tmp/chromedriver_version \
    && CHROMEDRIVER_VERSION=$(cat /tmp/chromedriver_version) \
    && echo "ChromeDriver 版本: $CHROMEDRIVER_VERSION" \
    && wget -q "https://chromedriver.storage.googleapis.com/$CHROMEDRIVER_VERSION/chromedriver_linux64.zip" -O /tmp/chromedriver.zip \
    && unzip /tmp/chromedriver.zip -d /usr/local/bin/ \
    && rm /tmp/chromedriver.zip /tmp/chromedriver_version \
    && chmod +x /usr/local/bin/chromedriver \
    && echo "ChromeDriver 安裝完成"

# 設置工作目錄
WORKDIR /app

# 複製專案文件
COPY requirements.txt .
COPY app.py .
COPY static/ ./static/

# 安裝 Python 依賴（修正安裝參數）
RUN pip install --no-cache-dir -r requirements.txt

# 設置環境變數
ENV DISPLAY=:99
ENV PYTHONUNBUFFERED=1
ENV CHROME_BIN=/usr/bin/google-chrome
ENV CHROMEDRIVER_PATH=/usr/local/bin/chromedriver
# 減少記憶體使用的環境變數
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONHASHSEED=random

# 創建截圖目錄
RUN mkdir -p /app/screenshots

# 啟動應用
CMD ["python", "app.py"] 