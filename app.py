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
    chrome_options.binary_location = '/usr/bin/chromium'  # 指定 chromium 路徑
    # chrome_options.add_argument('user-agent=Mozilla/5.0 ...') # 如需偽裝user-agent可取消註解

    service = Service('/usr/bin/chromedriver')
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

def make_reservation():
    driver = setup_driver()
    try:
        # 1. 連線到網站
        driver.get("https://www.ntpc.ltc-car.org/")
        
        # 2. 點擊「我知道了」
        WebDriverWait(driver, 30).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), '我知道了')]"))
        ).click()
        
        # 3. 輸入登入資訊
        id_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "id"))
        )
        id_input.send_keys("A102574899")
        
        password_input = driver.find_element(By.ID, "password")
        password_input.send_keys("visi319VISI")
        
        login_button = driver.find_element(By.XPATH, "//button[contains(text(), '民眾登入')]")
        login_button.click()
        
        # 4. 點擊「登入成功」確定
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), '確定')]"))
        ).click()
        
        # 5. 點擊「新增預約」
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), '新增預約')]"))
        ).click()
        
        # 6-7. 選擇上車地點
        pickup_type = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "pickupType"))
        )
        pickup_type.send_keys("醫療院所")
        
        pickup_location = driver.find_element(By.ID, "pickupLocation")
        pickup_location.send_keys("亞東紀念醫院")
        time.sleep(2)  # 等待搜尋結果
        first_result = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, ".pac-item"))
        )
        first_result.click()
        
        # 8. 選擇下車地點
        dropoff_type = driver.find_element(By.ID, "dropoffType")
        dropoff_type.send_keys("住家")
        
        # 9. 選擇預約時間
        date_select = driver.find_element(By.ID, "date")
        date_select.send_keys("最後一個選項")
        
        hour_select = driver.find_element(By.ID, "hour")
        hour_select.send_keys("16")
        
        minute_select = driver.find_element(By.ID, "minute")
        minute_select.send_keys("40")
        
        # 10-14. 填寫其他選項
        driver.find_element(By.ID, "flexibleTime").send_keys("不同意")
        driver.find_element(By.ID, "companionCount").send_keys("1人(免費)")
        driver.find_element(By.ID, "shareRide").send_keys("否")
        driver.find_element(By.ID, "wheelchair").send_keys("是")
        driver.find_element(By.ID, "largeWheelchair").send_keys("否")
        
        # 15. 點擊下一步
        next_button = driver.find_element(By.XPATH, "//button[contains(text(), '下一步，確認預約資訊')]")
        next_button.click()
        
        # 16. 送出預約
        submit_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), '送出預約')]"))
        )
        submit_button.click()
        
        # 17. 確認預約完成
        success_message = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//div[contains(text(), '已完成預約')]"))
        )
        
        return True
        
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        driver.save_screenshot('/app/error.png')
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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080))) 