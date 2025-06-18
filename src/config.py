from selenium.webdriver.common.by import By

# 網站設定
URL = "https://www.mvdis.gov.tw/m3-emv-trn/trn01qry/trn01qry"

# 元素定位器
LOCATORS = {
    "id_input": (By.ID, "idno"),
    "password_input": (By.ID, "birthday"),
    "login_button": (By.XPATH, "//button[contains(text(), '登入')]"),
    "i_know_button": (By.XPATH, "//button[contains(text(), '我知道了')]"),
    "reservation_button": (By.XPATH, "//button[contains(text(), '預約')]"),
    "date_input": (By.ID, "date"),
    "time_select": (By.ID, "time"),
    "confirm_button": (By.XPATH, "//button[contains(text(), '確認')]")
}

# 等待時間設定（秒）
WAIT_TIMES = {
    "page_load": 30,
    "element": 10
}

# 使用者代理字串
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36" 