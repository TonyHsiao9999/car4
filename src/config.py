# 網站設定
URL = "https://www.mvdis.gov.tw/m3-emv-trn/trn01qry/trn01qry"

# 元素定位器（CSS選擇器格式）
LOCATORS = {
    "id_input": "#idno",
    "password_input": "#birthday", 
    "login_button": "button:has-text('登入')",
    "i_know_button": "button:has-text('我知道了')",
    "reservation_button": "button:has-text('預約')",
    "date_input": "#date",
    "time_select": "#time",
    "confirm_button": "button:has-text('確認')"
}

# 等待時間設定（秒）
WAIT_TIMES = {
    "page_load": 30,
    "element": 10
}

# 使用者代理字串
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36" 