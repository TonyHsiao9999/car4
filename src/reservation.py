from selenium.webdriver.support.ui import Select
from .config import URL, LOCATORS, WAIT_TIMES
from .driver import wait_for_element, safe_click, print_debug_info

class ReservationBot:
    def __init__(self, driver):
        self.driver = driver

    def login(self, id_number, password):
        """執行登入流程"""
        try:
            self.driver.get(URL)
            self.driver.implicitly_wait(WAIT_TIMES["page_load"])

            # 輸入身分證號
            id_input = wait_for_element(self.driver, LOCATORS["id_input"])
            if id_input:
                id_input.send_keys(id_number)

            # 輸入生日
            password_input = wait_for_element(self.driver, LOCATORS["password_input"])
            if password_input:
                password_input.send_keys(password)

            # 點擊登入按鈕
            if not safe_click(self.driver, LOCATORS["login_button"]):
                return False

            # 處理「我知道了」按鈕
            if not safe_click(self.driver, LOCATORS["i_know_button"]):
                return False

            return True
        except Exception as e:
            print_debug_info(self.driver, "登入流程", f"登入過程發生錯誤: {e}")
            return False

    def make_reservation(self, date, time):
        """執行預約流程"""
        try:
            # 點擊預約按鈕
            if not safe_click(self.driver, LOCATORS["reservation_button"]):
                return False

            # 選擇日期
            date_input = wait_for_element(self.driver, LOCATORS["date_input"])
            if date_input:
                date_input.clear()
                date_input.send_keys(date)

            # 選擇時間
            time_select = wait_for_element(self.driver, LOCATORS["time_select"])
            if time_select:
                Select(time_select).select_by_visible_text(time)

            # 點擊確認按鈕
            if not safe_click(self.driver, LOCATORS["confirm_button"]):
                return False

            return True
        except Exception as e:
            print_debug_info(self.driver, "預約流程", f"預約過程發生錯誤: {e}")
            return False 