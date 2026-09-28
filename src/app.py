import os
import sqlite3

from database import save_database,getdaily30,calculate_statistics
from ai_report import generate_ai_report
from chart import create_chart
from gmail_sender import send_email
from bank_rate import create_driver,get_rate_data


from config import (
    DATABASE_PATH,
    CHART_PATH
)



def main():

    print()
    print("=" * 70)
    print("臺灣銀行每日匯率 → SQLite")
    print("=" * 70)
    print()

    driver=None
    conn=None
    
    try:
        # ----------------------------------------------------
        # 1.設定Database Connection
        # ----------------------------------------------------
        conn = sqlite3.connect(DATABASE_PATH)
        
        # ----------------------------------------------------
        # 2. 開啟Chrome
        # ----------------------------------------------------

        driver = create_driver()

        print("Chrome 啟動完成")

        # ----------------------------------------------------
        # 3. 取得最近交易日及其匯率
        # ----------------------------------------------------

        rate_date, rate_time, rates = get_rate_data(
            driver
        )
        
        # ----------------------------------------------------
        # 4. 寫入 SQLite
        # ----------------------------------------------------

        database.save_database(conn,rate_date,rate_time,rates)
        
        df = getdaily30(conn)
        
        # --------------------------------
        # 5. 計算統計資料
        # --------------------------------
        
        statistics = calculate_statistics(df)
        
        # --------------------------------
        # 3. 產生趨勢圖
        # --------------------------------
        
        chart_path = create_chart(df)


        # --------------------------------
        # 4. AI 分析
        # --------------------------------

        ai_report = generate_ai_report(statistics)

        # --------------------------------
        # 5. Gmail
        # --------------------------------
        
        send_email(
            statistics=statistics,
            ai_report=ai_report,
            chart_path=chart_path
        )

        print()
        print("================================")
        print("完成")
        print("================================")

       
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
    
