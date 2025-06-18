# 自動預約系統

這是一個使用 Python 和 Selenium 開發的自動預約系統，用於自動化網頁登入和預約流程。

## 功能特點

- 自動化網頁登入
- 自動填寫預約資訊
- 錯誤處理和重試機制
- 詳細的除錯資訊輸出

## 系統需求

- Python 3.8 或更高版本
- Chrome 瀏覽器
- ChromeDriver

## 安裝步驟

1. 克隆專案：
```bash
git clone [您的專案URL]
cd [專案目錄]
```

2. 安裝依賴套件：
```bash
pip install -r requirements.txt
```

3. 確保已安裝 Chrome 瀏覽器和對應版本的 ChromeDriver

## 使用方法

執行以下命令來啟動預約程序：

```bash
python src/main.py --id "您的身分證號" --password "您的生日密碼" --date "YYYY-MM-DD" --time "預約時間"
```

參數說明：
- `--id`: 身分證號
- `--password`: 生日密碼
- `--date`: 預約日期（格式：YYYY-MM-DD）
- `--time`: 預約時間

## 專案結構

```
.
├── src/
│   ├── __init__.py
│   ├── main.py          # 主程式入口
│   ├── config.py        # 配置設定
│   ├── driver.py        # WebDriver 相關功能
│   └── reservation.py   # 預約相關功能
├── requirements.txt     # 依賴套件列表
├── Dockerfile          # Docker 配置
└── README.md          # 專案說明文件
```

## 注意事項

- 請確保您的網路連接穩定
- 建議在執行前先測試網站是否可正常訪問
- 請遵守網站的使用條款和規定

## 授權

MIT License 