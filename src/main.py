import argparse
from driver import setup_driver
from reservation import ReservationBot

def main():
    parser = argparse.ArgumentParser(description='自動預約系統')
    parser.add_argument('--id', required=True, help='身分證號')
    parser.add_argument('--password', required=True, help='生日密碼')
    parser.add_argument('--date', required=True, help='預約日期 (YYYY-MM-DD)')
    parser.add_argument('--time', required=True, help='預約時間')
    
    args = parser.parse_args()
    
    driver = setup_driver()
    bot = ReservationBot(driver)
    
    try:
        if bot.login(args.id, args.password):
            print("登入成功")
            if bot.make_reservation(args.date, args.time):
                print("預約成功")
            else:
                print("預約失敗")
        else:
            print("登入失敗")
    finally:
        driver.quit()

if __name__ == "__main__":
    main() 