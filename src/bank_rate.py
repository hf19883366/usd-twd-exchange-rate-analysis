from selenium import webdriver
from datetime import datetime, timedelta
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoAlertPresentException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
import re




BASE_URL = "https://rate.bot.com.tw/xrt/all"

TARGET_CURRENCIES={
    "USD",
    "GBP",
    "JPY",
    "EUR",
    "CNY"
}

# 最多往前找幾天
MAX_LOOKBACK_DAYS = 10

# Challenge Validation 等待時間
CHALLENGE_WAIT_SECONDS = 120

NO_DATA_MESSAGE = "您輸入的歷史資料日期不是一個有效值"

# ============================================================
# 建立 Chrome
# ============================================================

def create_driver():

    options = Options()

    # 正常顯示瀏覽器
    # 不使用 headless，因為遇到 Challenge 時可能需要人工確認
    options.add_argument("--start-maximized")

    options.add_argument(
        "--disable-blink-features=AutomationControlled"
    )

    options.add_argument(
        "--disable-notifications"
    )

    options.add_argument(
        "--lang=zh-TW"
    )

    driver = webdriver.Chrome(
        options=options
    )

    driver.set_page_load_timeout(60)

    return driver


# ============================================================
# 判斷是否為 Challenge Validation
# ============================================================

def is_challenge_page(driver):

    title = driver.title.lower()

    page_text = driver.page_source.lower()

    keywords = [
        "challenge",
        "validation",
        "checking your browser",
        "verify you are human",
        "人機驗證",
    ]
    
    for keyword in keywords:

        if keyword in title:
            return True

        if keyword in page_text:
            return True

    return False
    

# ============================================================
# 等待 Challenge
# ============================================================

def wait_for_challenge(driver):

    if not is_challenge_page(driver):

        return True


    print()
    print("=" * 70)
    print("偵測到臺灣銀行 Challenge Validation")
    print("=" * 70)
    print()

    print("請在開啟的 Chrome 視窗中完成驗證。")
    print("完成後程式會自動繼續。")
    print()
    print(
        f"最多等待 {CHALLENGE_WAIT_SECONDS} 秒..."
    )
    print()

    start_time = time.time()

    while True:

        time.sleep(2)
        if not is_challenge_page(driver):
            print("Challenge Validation 已完成。")
            print()

            return True

        elapsed = time.time() - start_time

        if elapsed >= CHALLENGE_WAIT_SECONDS:

            print()
            print("等待 Challenge Validation 超時。")

            return False


# ============================================================
# 取得指定日期網頁
# ============================================================

def open_rate_page(driver, date):

    date_string = date.strftime("%Y-%m-%d")

    url = f"{BASE_URL}/{date_string}"

    print()
    print(f"讀取：{url}")

    try:
        driver.get(url)

        alert = WebDriverWait(driver, 2).until(
            EC.alert_is_present()
        )

        alert_message = alert.text
        alert.accept()
        
        # 等待頁面
        time.sleep(3)
        # Challenge
        if not wait_for_challenge(driver):

            return None

        return None, alert_message

    except Exception:
        # 沒有 alert，正常取得頁面
        return driver.page_source, None
        
# ============================================================
# 解析日期
# ============================================================
def parse_rate_time(soup):

    text = soup.get_text(
        " ",
        strip=True
    )

    # 例如：
    # 掛牌時間：2026/07/28 16:01

    pattern = r"掛牌時間[：:]\s*(\d{4}/\d{2}/\d{2}\s+\d{2}:\d{2})"

    match = re.search(
        pattern,
        text
    )

    if match:

        return match.group(1)

    return None

# ============================================================
# 解析匯率
# ============================================================

def parse_rates(html):

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    rate_time = parse_rate_time(
        soup
    )

    result = {}
    rows=soup.select("tbody tr")

    for row in rows:

        text = row.get_text(
            " ",
            strip=True
        )

        currency = None

        for code in TARGET_CURRENCIES:

            if f"({code})" in text:

                currency = code
                break


        if currency is None:

            continue


        cells = row.find_all("td")

        values = []

        for cell in cells:
            value = cell.get_text(
                "|",
                strip=True
            )

            values.append(value)


        # 臺灣銀行目前歷史收盤頁：
        #
        # 1 現金買入
        # 2 現金賣出
        # 3 即期買入
        # 4 即期賣出
        #
        if len(values) >= 4:

            result[currency] = {
                "cash_buy": values[1],

                "cash_sell": values[2],

                "spot_buy": values[3],

                "spot_sell": values[4],
            }
 
    return rate_time, result

# ============================================================
# 數字轉換
# ============================================================

def to_float(value):

    if value is None:

        return None

    value = str(value).strip()

    if value == "" or value == "-":

        return None

    try:

        return float(value)

    except ValueError:

        return None

# ============================================================
# 檢查資料是否完整
# ============================================================
def validate_rates(rates):

    for currency in TARGET_CURRENCIES:

        if currency not in rates:

            print(
                f"缺少幣別：{currency}"
            )

            return False
        spot_buy = rates[currency]["spot_buy"]
        
        spot_sell = rates[currency]["spot_sell"]


        if to_float(spot_buy) is None:

            print(
                f"{currency} 即期買入資料無效："
                f"{spot_buy}"
            )

            return False


        if to_float(spot_sell) is None:
            print(
                f"{currency} 即期賣出資料無效："
                f"{spot_sell}"
            )

            return False

    return True

# ============================================================
# 找最近交易日
# ============================================================
def get_rate_data(driver):

    today = datetime.now().date()


    for days_back in range(
        0,
        MAX_LOOKBACK_DAYS + 1
    ):
        
        target_date = (
            today -
            timedelta(days=days_back)
        )


        html, alert_message = open_rate_page(
            driver,
            target_date
        )

        # 有 alert，代表該日期沒有歷史資料
        if alert_message == NO_DATA_MESSAGE:
            print(
                f"{target_date} 沒有歷史資料："
                f"{alert_message}"
            )
            continue
  
        if alert_message:

            raise RuntimeError(
                f"{target_date} 發生網站錯誤："
                f"{alert_message}"
            )

        if not html:
            continue
        rate_time, rates = parse_rates(
            html
        )
        if rate_time==None:
            print(
                f"{target_date} 沒有歷史資料!"
                "繼續往前找..."
            )
            continue
        

        if not validate_rates(rates):

            print(
                f"{target_date} 資料不完整，"
                "繼續往前找..."
            )

            continue

        # 使用掛牌時間確認真正資料日期

        if rate_time:

            try:

                dt = datetime.strptime(
                    rate_time,
                    "%Y/%m/%d %H:%M"
                )
                actual_date = datetime.strftime(target_date,"%Y-%m-%d")                
                print_rates(actual_date,rate_time,rates)
                
            except ValueError:
                pass            

        return (
            actual_date,
            rate_time,
            rates
        )

    raise RuntimeError(
        "最近 "
        f"{MAX_LOOKBACK_DAYS} 天找不到完整匯率資料"
    )


# ============================================================
# 顯示資料
# ============================================================

def print_rates(
    rate_date,
    rate_time,
    rates
):

    print()
    print("=" * 70)
    print("臺灣銀行匯率")
    print("=" * 70)

    print(f"日期：{rate_date}")
    print(
        f"掛牌時間：{rate_time}"
    )

    print()
    print(
        f"{'幣別':<8}"
        f"{'即期買入':>12}"
        f"{'即期賣出':>12}"
    )

    print("-" * 35)
    for currency in TARGET_CURRENCIES:

        buy = rates[currency]["spot_buy"]

        sell = rates[currency]["spot_sell"]

        print(
            f"{currency:<8}"
            f"{buy:>12}"
            f"{sell:>12}"
        )

    print("=" * 70)



