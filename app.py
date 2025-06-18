from flask import Flask, jsonify, send_file
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os
from dotenv import load_dotenv

app = Flask(__name__)

def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
    chrome_options.binary_location = '/usr/bin/chromium'  # 指定 chromium 路徑
    # chrome_options.add_argument('user-agent=Mozilla/5.0 ...') # 如需偽裝user-agent可取消註解

    service = Service('/usr/bin/chromedriver')
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

def make_reservation():
    driver = setup_driver()
    try:
        driver.get("https://www.ntpc.ltc-car.org/")
        print("已載入網頁，等待「我知道了」按鈕...")
        WebDriverWait(driver, 30).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
        driver.save_screenshot('/app/before_wait.png')
        elements = driver.find_elements(By.XPATH, "//*[contains(text(), '我知道了')]")
        print("找到元素數量：", len(elements))
        for element in elements:
            print(element.tag_name, element.text)
        iframes = driver.find_elements(By.TAG_NAME, "iframe")
        for iframe in iframes:
            driver.switch_to.frame(iframe)
            elements = driver.find_elements(By.XPATH, "//*[contains(text(), '我知道了')]")
            if elements:
                print("在 iframe 中找到「我知道了」")
                break
            driver.switch_to.default_content()
        button = WebDriverWait(driver, 30).until(
            EC.element_to_be_clickable((By.XPATH, "//*[contains(text(), '我知道了')]"))
        )
        print("找到「我知道了」按鈕，準備點擊...")
        driver.save_screenshot('/app/before_click.png')
        driver.execute_script("arguments[0].click();", button)
        print("已點擊「我知道了」按鈕...")
        driver.save_screenshot('/app/after_click.png')

        # 3. 輸入身分證字號A102574899，密碼visi319VISI，然後點擊「民眾登入」
        print("開始輸入登入資訊...")
        id_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "id"))
        )
        id_input.send_keys("A102574899")
        password_input = driver.find_element(By.ID, "password")
        password_input.send_keys("visi319VISI")
        login_button = driver.find_element(By.XPATH, "//button[contains(text(), '民眾登入')]")
        login_button.click()
        print("已點擊「民眾登入」按鈕...")
        driver.save_screenshot('/app/after_login.png')

        # 4. 看到「登入成功」，點擊「確定」
        print("等待「登入成功」確定按鈕...")
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), '確定')]"))
        ).click()
        print("已點擊「確定」按鈕...")
        driver.save_screenshot('/app/after_confirm.png')

        # 5. 點擊「新增預約」
        print("等待「新增預約」按鈕...")
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), '新增預約')]"))
        ).click()
        print("已點擊「新增預約」按鈕...")
        driver.save_screenshot('/app/after_new_reservation.png')

        # 6. 上車地點請下拉選擇「醫療院所」
        print("選擇上車地點「醫療院所」...")
        pickup_type = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "pickupType"))
        )
        pickup_type.send_keys("醫療院所")
        driver.save_screenshot('/app/after_pickup_type.png')

        # 7. 右邊的文字欄位輸入「亞東紀念醫院」，然後文字欄位下方會有Google搜尋結果，點擊第一個結果
        print("輸入上車地點「亞東紀念醫院」...")
        pickup_location = driver.find_element(By.ID, "pickupLocation")
        pickup_location.send_keys("亞東紀念醫院")
        time.sleep(2)  # 等待搜尋結果
        first_result = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, ".pac-item"))
        )
        first_result.click()
        print("已點擊第一個搜尋結果...")
        driver.save_screenshot('/app/after_pickup_location.png')

        # 8. 下車地點請下拉選擇「住家」
        print("選擇下車地點「住家」...")
        dropoff_type = driver.find_element(By.ID, "dropoffType")
        dropoff_type.send_keys("住家")
        driver.save_screenshot('/app/after_dropoff_type.png')

        # 9. 預約日期/時段請下拉選擇最後一個選項，右邊請下拉選擇16，再往右邊請下拉選擇40
        print("選擇預約日期/時段...")
        date_select = driver.find_element(By.ID, "date")
        date_select.send_keys("最後一個選項")
        hour_select = driver.find_element(By.ID, "hour")
        hour_select.send_keys("16")
        minute_select = driver.find_element(By.ID, "minute")
        minute_select.send_keys("40")
        driver.save_screenshot('/app/after_time_selection.png')

        # 10. 於預約時間前後30分鐘到達 選擇「不同意」
        print("選擇「不同意」於預約時間前後30分鐘到達...")
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//input[@value='不同意']"))
        ).click()
        driver.save_screenshot('/app/after_flexible_time.png')

        # 11. 陪同人數 下拉選擇「1人(免費)」
        print("選擇陪同人數「1人(免費)」...")
        companion_select = driver.find_element(By.ID, "companion")
        companion_select.send_keys("1人(免費)")
        driver.save_screenshot('/app/after_companion.png')

        # 12. 同意共乘 選擇「否」
        print("選擇「否」同意共乘...")
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//input[@value='否']"))
        ).click()
        driver.save_screenshot('/app/after_share_ride.png')

        # 13. 搭乘輪椅上車 選擇「是」
        print("選擇「是」搭乘輪椅上車...")
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//input[@value='是']"))
        ).click()
        driver.save_screenshot('/app/after_wheelchair.png')

        # 14. 大型輪椅 選擇「否」
        print("選擇「否」大型輪椅...")
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//input[@value='否']"))
        ).click()
        driver.save_screenshot('/app/after_large_wheelchair.png')

        # 15. 點擊「下一步，確認預約資訊」按鈕
        print("點擊「下一步，確認預約資訊」按鈕...")
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), '下一步，確認預約資訊')]"))
        ).click()
        driver.save_screenshot('/app/after_next_step.png')

        # 16. 新的頁面點擊「送出預約」
        print("點擊「送出預約」按鈕...")
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), '送出預約')]"))
        ).click()
        driver.save_screenshot('/app/after_submit.png')

        # 17. 跳出「已完成預約」畫面，表示完成
        print("等待「已完成預約」畫面...")
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//*[contains(text(), '已完成預約')]"))
        )
        print("已完成預約")
        driver.save_screenshot('/app/after_success.png')
        return True
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        driver.save_screenshot('/app/error.png')
        import os
        print("error.png exists:", os.path.exists('/app/error.png'))
        return False
    finally:
        driver.quit()

@app.route('/')
def index():
    return jsonify({"status": "服務正在運行"})

@app.route('/reserve')
def reserve():
    success = make_reservation()
    return jsonify({"success": success})

@app.route('/error-screenshot')
def error_screenshot():
    try:
        return send_file('/app/error.png', mimetype='image/png')
    except Exception as e:
        return jsonify({"error": "找不到截圖檔案"}), 404

@app.route('/before-click')
def before_click():
    try:
        return send_file('/app/before_click.png', mimetype='image/png')
    except Exception as e:
        return jsonify({"error": "找不到截圖檔案"}), 404

@app.route('/after-click')
def after_click():
    try:
        return send_file('/app/after_click.png', mimetype='image/png')
    except Exception as e:
        return jsonify({"error": "找不到截圖檔案"}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080))) 