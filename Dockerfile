FROM python:3.9-slim

# 安裝 Chrome、chromedriver 和必要的依賴
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    xvfb \
    libxi6 \
    libgconf-2-4 \
    fonts-liberation libasound2 libatk1.0-0 libatk-bridge2.0-0 libcups2 libdbus-1-3 libgtk-3-0 libnspr4 libnss3 libxcomposite1 libxdamage1 libxrandr2 xdg-utils \
    && wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && apt-get install -y chromium-chromedriver \
    && ln -s /usr/lib/chromium-browser/chromedriver /usr/bin/chromedriver || ln -s /usr/lib/chromium/chromedriver /usr/bin/chromedriver \
    && rm -rf /var/lib/apt/lists/*

# 設置工作目錄
WORKDIR /app

# 複製專案文件
COPY requirements.txt .
COPY app.py .

# 安裝 Python 依賴
RUN pip install --no-cache-dir -r requirements.txt

# 設置環境變數
ENV DISPLAY=:99
ENV PYTHONUNBUFFERED=1

# 啟動應用
CMD ["python", "app.py"] 