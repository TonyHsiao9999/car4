FROM python:3.9-alpine

# 安裝系統依賴
RUN apk add --no-cache \
    chromium \
    chromium-chromedriver \
    nss \
    freetype \
    freetype-dev \
    harfbuzz \
    ca-certificates \
    ttf-freefont \
    && rm -rf /var/cache/apk/*

WORKDIR /app

COPY requirements.txt .
COPY app.py .
COPY static/ ./static/

# 安裝 Python 依賴
RUN pip install --upgrade pip
RUN pip install --no-cache-dir flask==3.0.2
RUN pip install --no-cache-dir selenium==4.18.1

# 設置環境變數
ENV DISPLAY=:99
ENV PYTHONUNBUFFERED=1
ENV CHROME_BIN=/usr/bin/chromium-browser
ENV CHROME_PATH=/usr/bin/chromium-browser
ENV CHROMEDRIVER_PATH=/usr/bin/chromedriver

# 創建截圖目錄
RUN mkdir -p /app/screenshots

CMD ["python", "app.py"] 