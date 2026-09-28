import sqlite3
import time
import re
import pandas as pd
import matplotlib.pyplot as plt
import os
import base64
from datetime import datetime, timedelta
from pathlib import Path

from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoAlertPresentException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from email.message import EmailMessage
from email.mime.text import MIMEText
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build


# ============================================================
# 設定
# ============================================================

BASE_URL = "https://rate.bot.com.tw/xrt/all"

TARGET_CURRENCIES={
    "USD",
    "GBP",
    "JPY",
    "EUR",
    "CNY"
}

# 設定趨勢圖說明的字型(MacOS)
plt.rcParams['font.sans-serif'] = ['PingFang TC']
plt.rcParams['axes.unicode_minus'] = False


# 最多往前找幾天
MAX_LOOKBACK_DAYS = 10

# Challenge Validation 等待時間
CHALLENGE_WAIT_SECONDS = 120

NO_DATA_MESSAGE = "您輸入的歷史資料日期不是一個有效值"

#SCOPES = ['https://googleapis.com']

SCOPES=[
    "https://www.googleapis.com/auth/gmail.send"
]

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
# SQLite 寫入
# ============================================================

def save_database(
    conn,
    rate_date,
    rate_time,
    rates
):
    
    now = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )
    job_date=datetime.now().strftime(
        "%Y-%m-%d"
    )
    
    for curr in list(rates.keys()):
        sql = """

            INSERT INTO change_rates (

                rate_date,
                currency,
                rate_time,
                job_date ,
                rate_buy,
                rate_sell,
                created_at,
                updated_at

            )

            VALUES (

                ?, ?,

                ?, ?,

                ?, ?,

                ?,

                ?

            )

            ON CONFLICT(rate_date,currency)

            DO UPDATE SET

                rate_time = excluded.rate_time,
                job_date = excluded.job_date,

                rate_buy = excluded.rate_buy,
                rate_sell = excluded.rate_sell,
                updated_at = excluded.updated_at

        """


        values = (

            rate_date,
            curr,
            rate_time,
            job_date,

            to_float(
                rates[curr]["spot_buy"]
            ),
            to_float(
                rates[curr]["spot_sell"]
            ),

            now,
            now
        )


        cursor = conn.cursor()

        cursor.execute(
            sql,
            values
        )

    conn.commit()


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


# ============================================================
# 找最近交易日
# ============================================================
def get_rate_data(driver):

    today = datetime.now().date()

    today = (datetime.strptime("2026-08-24","%Y-%m-%d")).date()

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


# =============================================================
# 顯示最近30個交易日的掛牌資料，先以美金為例
# =============================================================
def getdaily30(conn):
    
    sql="""
      WITH ranked AS (
          SELECT
              rate_date,
              currency,
              rate_sell,
              ROW_NUMBER() OVER (
                  PARTITION BY currency
                  ORDER BY rate_date DESC
              ) AS rn
          FROM change_rates
          WHERE currency = ?
      )
      SELECT
          rate_date as 日期,
          rate_sell as 即期賣出
      FROM ranked
      WHERE rn <= 10
      ORDER BY rate_date;
    """
    df = pd.read_sql_query(sql, conn, params=("USD",))
    
    return df

#=============================================================
# 計算累積變動率及波動率
#=============================================================
def cal_variance(df):
    
    df = df.sort_values("日期").dropna(subset=["即期賣出"])
        
    df["每日變動%"] = (
        df["即期賣出"].pct_change() * 100
    )
 
    last_30 = df.tail(10).copy()
 
    start_rate = last_30.iloc[0]["即期賣出"]
    end_rate = last_30.iloc[-1]["即期賣出"]

    cumulative_change = (
        (end_rate / start_rate) - 1
    ) * 100

    max_rate = last_30["即期賣出"].max()
    min_rate = last_30["即期賣出"].min()
    avg_rate = last_30["即期賣出"].mean()

    volatility = last_30["每日變動%"].std()

    print(f"資料期間：{last_30.iloc[0]['日期']} ~ "
            f"{last_30.iloc[-1]['日期']}")

    print(f"起始匯率：{start_rate:.4f}")
    print(f"最新匯率：{end_rate:.4f}")
  
    print(f"30日累積變動：{cumulative_change:+.2f}%")

    print(f"30日最高：{max_rate:.4f}")
    print(f"30日最低：{min_rate:.4f}")
    print(f"30日平均：{avg_rate:.4f}")
    print(f"每日變動標準差：{volatility:.2f}%")


#=============================================================
# 寄信服務
#=============================================================
def get_gmail_service():
    creds=None
    
    #如果之前己經授權過
    if os.path.exists("token.json"):
        creds=Credentials.from_authorized_user_file(
            "token.json",
            SCOPES
        )
        
     #如果沒有憑證或憑證己失效
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow=InstalledAppFlow.from_client_secrets_file(
                    "credentials.json",
                    SCOPES
            )
            
            #flow.oauth2session.auth_url = "https://google.com"
            #flow.oauth2session.token_url = "https://googleapis.com"

            creds=flow.run_local_server(port=8080, open_browser=True)
        
        with open("token.json","w") as token:
            token.write(creds.to_json())
        
    service=build(
        "gmail",
        "v1",
        credentials=creds
    )
    
    return service


#=============================================================
# 寄信
#=============================================================
def send_email(service,sender,receiver,subject,body):
    
    message=EmailMessage()
    message.set_content(body)
    message["From"]=sender
    message["To"]=receiver
    message["Subject"]=subject
    
    encoded_message=base64.urlsafe_b64encode(
        message.as_bytes()
    ).decode()

    create_message={
        "raw":encoded_message
    }
    
    result=(
        service.users()
        .messages()
        .send(
            userId="me",
            body=create_message
        )
        .execute()
    )
    
    print("寄信成功！")
    print("Message ID:",result["id"])



# ============================================================
# 主程式
# ============================================================

def main():

    print()
    print("=" * 70)
    print("臺灣銀行每日匯率 → SQLite")
    print("=" * 70)
    print()


    conn = None
    driver = None

    try:
        # ----------------------------------------------------
        # 1.Database Connection
        # ----------------------------------------------------
        conn = sqlite3.connect(DB_FILE)
        
        # ----------------------------------------------------
        # 2. Chrome
        # ----------------------------------------------------

        driver = create_driver()

        print("Chrome 啟動完成")


        # ----------------------------------------------------
        # 3. 取得最近交易日
        # ----------------------------------------------------

        rate_date, rate_time, rates = get_rate_data(
            driver
        )


        # ----------------------------------------------------
        # 4. 顯示
        # ----------------------------------------------------

        print_rates(
            rate_date,
            rate_time,
            rates
        )

        # ----------------------------------------------------
        # 5. 寫入 SQLite
        # ----------------------------------------------------

        #save_database(
        #    conn,
        #    rate_date,
        #    rate_time,
        #    rates
        #)

        #print()
        #print(
        #    f"✓ {rate_date} 已寫入 SQLite"
        #)

        # ----------------------------------------------------
        # 6. 顯示資料庫
        # ----------------------------------------------------

        #df=getdaily30(conn)
        #print(df)
        
        #cal_variance(df)

      # ------------------------------------
      # 畫30日趨勢圖
      # ------------------------------------
        #df_trend=get_trend(conn,currency,start_date,latest_date,change_percent)

        my_email="hf19883366@gmail.com"
        service=get_gmail_service()
        send_email(
            service=service,
            sender=my_email,
            receiver=my_email,
            subject="Python Gmail API 測試",
            body="這是一封使用 Gmail API+Oauth 2.0寄出的測試信"
        )


        print()
        print("程式執行完成。")

    except Exception as e:

        print()
        print("=" * 70)
        print("程式執行失敗")
        print("=" * 70)

        print(
            f"{type(e).__name__}: {e}"
        )


    finally:

        if driver:
            
            # 如果想在自動排程時自動關閉 Chrome，
            # 這裡保持 True。
            driver.quit()

        if conn:

            conn.close()


# ============================================================
# 執行
# ============================================================

if __name__ == "__main__":

    main()
    
