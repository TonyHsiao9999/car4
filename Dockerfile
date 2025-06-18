FROM python:3.9-slim

# 安裝系統依賴
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 安裝 Chrome
RUN wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# 下載 ChromeDriver 137 版本
RUN wget -q "https://chromedriver.storage.googleapis.com/137.0.7151.119/chromedriver_linux64.zip" -O /tmp/chromedriver.zip \
    && unzip /tmp/chromedriver.zip -d /usr/local/bin/ \
    && rm /tmp/chromedriver.zip \
    && chmod +x /usr/local/bin/chromedriver \
    && echo "ChromeDriver 137.0.7151.119 安裝完成"

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
ENV CHROME_BIN=/usr/bin/google-chrome
ENV CHROMEDRIVER_PATH=/usr/local/bin/chromedriver

# 創建截圖目錄
RUN mkdir -p /app/screenshots

# 啟動應用
CMD ["python", "app.py"] 