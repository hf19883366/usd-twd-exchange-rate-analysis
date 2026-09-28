import sqlite3
import pandas as pd


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
      WHERE rn <= 30
      ORDER BY rate_date;
    """
    df = pd.read_sql_query(sql, conn, params=("USD",))
    
    return df

#=============================================================
# 計算累積變動率及波動率
#=============================================================
def calculate_statistics(df: pd.DataFrame) -> dict:
    
    if len(df)<2:
        raise ValueError("至少需要 2 筆匯率資料才能計算變動率")
    
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
    print(f"每日變動標準差：{volatility:+.2f}%")

    return {
        "start_date": last_30.iloc[0]['日期'],
        "end_date": last_30.iloc[-1]['日期'],
        "data_count": len(last_30),

        "start_rate": float(last_30.iloc[0]["即期賣出"]),
        "end_rate": float(last_30.iloc[-1]["即期賣出"]),

        "max_rate": float(max_rate),
        "min_rate": float(min_rate),

        "daily_change_std": float(volatility),

        "cumulative_change": float(
            cumulative_change
        ),

        "daily_changes": last_30[
            ["日期", "即期賣出", "每日變動%"]
        ].copy()
    }


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

