OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxx

OPENAI_MODEL=gpt-5.6-luna

SQLITE_DB=/home/user/exchange/exchange_rate.db

GMAIL_USERNAME=youraccount@gmail.com
GMAIL_APP_PASSWORD=xxxxxxxxxxxxxxxx

MAIL_TO=manager@example.com,finance@example.com


import os
import json
import sqlite3
import smtplib
import traceback

from datetime import datetime
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt

from dotenv import load_dotenv
from openai import OpenAI

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage


# ============================================================
# 1. 載入設定
# ============================================================

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv(
    "OPENAI_MODEL",
    "gpt-5.6-luna"
)

SQLITE_DB = os.getenv("SQLITE_DB")

GMAIL_USERNAME = os.getenv("GMAIL_USERNAME")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")

MAIL_TO = [
    x.strip()
    for x in os.getenv("MAIL_TO", "").split(",")
    if x.strip()
]


# ============================================================
# 2. 基本檢查
# ============================================================

def validate_config():

    required = {
        "OPENAI_API_KEY": OPENAI_API_KEY,
        "SQLITE_DB": SQLITE_DB,
        "GMAIL_USERNAME": GMAIL_USERNAME,
        "GMAIL_APP_PASSWORD": GMAIL_APP_PASSWORD,
    }

    missing = [
        key
        for key, value in required.items()
        if not value
    ]

    if missing:
        raise RuntimeError(
            "缺少環境變數："
            + ", ".join(missing)
        )

    if not MAIL_TO:
        raise RuntimeError(
            "MAIL_TO 沒有設定收件人"
        )

    if not Path(SQLITE_DB).exists():
        raise RuntimeError(
            f"SQLite 資料庫不存在：{SQLITE_DB}"
        )


# ============================================================
# 3. OpenAI Client
# ============================================================

client = OpenAI(
    api_key=OPENAI_API_KEY
)


# ============================================================
# 4. 從 SQLite 取得最近 10 筆資料
# ============================================================

def get_exchange_rates():

    sql = """
        SELECT
            rate_date,
            rate_sell
        FROM exchange_rate
        WHERE rate_sell IS NOT NULL
        ORDER BY rate_date DESC
        LIMIT 10
    """

    conn = sqlite3.connect(SQLITE_DB)

    try:

        df = pd.read_sql_query(
            sql,
            conn
        )

    finally:

        conn.close()

    if df.empty:
        raise RuntimeError(
            "資料庫沒有匯率資料"
        )

    if len(df) < 2:
        raise RuntimeError(
            "匯率資料至少需要兩筆"
        )

    # 日期轉換
    df["rate_date"] = pd.to_datetime(
        df["rate_date"]
    )

    # 匯率轉數字
    df["rate_sell"] = pd.to_numeric(
        df["rate_sell"],
        errors="coerce"
    )

    # 排除無效資料
    df = df.dropna(
        subset=["rate_sell"]
    )

    # 舊 → 新
    df = df.sort_values(
        "rate_date"
    ).reset_index(drop=True)

    return df


# ============================================================
# 5. 計算匯率變化
# ============================================================

def calculate_changes(df):

    # --------------------------------------------------------
    # 今日 vs 前一筆交易日
    # --------------------------------------------------------

    df["daily_change_pct"] = (
        df["rate_sell"].pct_change() * 100
    )

    # --------------------------------------------------------
    # 今日 vs 十天資料中的第一天
    # --------------------------------------------------------

    first_rate = df.iloc[0]["rate_sell"]

    df["ten_day_change_pct"] = (
        (
            df["rate_sell"] / first_rate
            - 1
        )
        * 100
    )

    return df


# ============================================================
# 6. 取得最新資料
# ============================================================

def get_latest_info(df):

    latest = df.iloc[-1]

    previous = (
        df.iloc[-2]
        if len(df) >= 2
        else None
    )

    return latest, previous


# ============================================================
# 7. 建立給 AI 的 JSON 資料
# ============================================================

def prepare_ai_data(df):

    records = []

    for _, row in df.iterrows():

        daily_change = (
            None
            if pd.isna(row["daily_change_pct"])
            else round(
                float(row["daily_change_pct"]),
                4
            )
        )

        ten_day_change = round(
            float(row["ten_day_change_pct"]),
            4
        )

        records.append({

            "date": row[
                "rate_date"
            ].strftime("%Y-%m-%d"),

            "usd_twd_sell": round(
                float(row["rate_sell"]),
                4
            ),

            "daily_change_pct":
                daily_change,

            "ten_day_change_pct":
                ten_day_change
        })

    return records


# ============================================================
# 8. 呼叫 OpenAI
# ============================================================

def analyze_with_openai(df):

    data = prepare_ai_data(df)

    latest = data[-1]

    previous = (
        data[-2]
        if len(data) >= 2
        else None
    )

    prompt = f"""
你是一位企業財務部門的匯率分析助手。

請分析以下 USD/TWD 美元兌新台幣「賣出匯率」資料。

資料如下：

{json.dumps(
    data,
    ensure_ascii=False,
    indent=2
)}

最新資料：

{json.dumps(
    latest,
    ensure_ascii=False,
    indent=2
)}

前一交易日資料：

{json.dumps(
    previous,
    ensure_ascii=False,
    indent=2
)}

請完成以下分析：

1. 今日匯率狀況
2. 今日相較前一交易日的變化
3. 最近十筆資料的整體趨勢
4. 十筆資料期間的累積變化
5. 最近是否有明顯波動
6. 短期趨勢判斷
7. 給企業財務人員的後續觀察重點

重要規則：

- 只能根據提供的匯率數據分析。
- 不可以自行虛構新聞、政策或經濟事件。
- 如果資料不足以判斷匯率上漲或下跌原因，必須明確說明。
- 不提供投資建議。
- 使用繁體中文。
- 語氣專業、簡潔。
- 所有百分比請以資料計算結果為準。

請只回傳 JSON，不要加 Markdown code fence。

JSON 格式必須為：

{{
    "trend": "偏升/偏貶/區間震盪",
    "trend_strength": "弱/中/強",
    "daily_summary": "今日變化摘要",
    "ten_day_summary": "十日變化摘要",
    "volatility": "低/中/高",
    "observation": "值得注意的現象",
    "short_term_view": "短期趨勢觀察",
    "cause_note": "如果無法從資料判斷原因，請明確說明",
    "risk_note": "給企業財務人員的風險觀察"
}}
"""

    response = client.responses.create(
        model=OPENAI_MODEL,
        input=prompt
    )

    text = response.output_text.strip()

    # --------------------------------------------------------
    # 清理可能出現的 Markdown
    # --------------------------------------------------------

    if text.startswith("```"):

        text = text.replace(
            "```json",
            ""
        )

        text = text.replace(
            "```",
            ""
        )

        text = text.strip()

    try:

        result = json.loads(text)

    except json.JSONDecodeError:

        print("OpenAI 回傳不是合法 JSON：")
        print(text)

        raise RuntimeError(
            "OpenAI JSON parsing failed"
        )

    return result


# ============================================================
# 9. OpenAI 失敗時使用的 fallback
# ============================================================

def create_fallback_analysis(df):

    latest = df.iloc[-1]

    daily_change = latest[
        "daily_change_pct"
    ]

    ten_day_change = latest[
        "ten_day_change_pct"
    ]

    if daily_change > 0:
        trend = "偏升"

    elif daily_change < 0:
        trend = "偏貶"

    else:
        trend = "區間震盪"

    return {

        "trend": trend,

        "trend_strength": "未判斷",

        "daily_summary":
            f"今日賣出匯率為 "
            f"{latest['rate_sell']:.4f}，"
            f"較前一交易日 "
            f"{daily_change:+.2f}%。",

        "ten_day_summary":
            f"最近十筆資料期間累積變化 "
            f"{ten_day_change:+.2f}%。",

        "volatility":
            "未判斷",

        "observation":
            "OpenAI 分析服務目前無法取得，"
            "以上僅提供程式計算結果。",

        "short_term_view":
            "請依後續交易日資料持續觀察。",

        "cause_note":
            "因 AI 分析服務無法取得，"
            "無法進一步分析變動原因。",

        "risk_note":
            "本日報告未完成 AI 輔助分析，"
            "請以原始匯率數據為準。"
    }


# ============================================================
# 10. 建立 10 日走勢圖
# ============================================================

def create_chart(df):

    filename = (
        "usd_twd_10days_"
        + datetime.now().strftime(
            "%Y%m%d_%H%M%S"
        )
        + ".png"
    )

    plt.figure(
        figsize=(10, 5)
    )

    plt.plot(
        df["rate_date"],
        df["rate_sell"],
        marker="o",
        linewidth=2,
        color="#1976D2"
    )

    # 最新值標示
    latest = df.iloc[-1]

    plt.annotate(
        f'{latest["rate_sell"]:.4f}',
        (
            latest["rate_date"],
            latest["rate_sell"]
        ),
        xytext=(10, 10),
        textcoords="offset points",
        fontsize=11,
        fontweight="bold",
        color="#D32F2F"
    )

    # 每個點標示數值
    for _, row in df.iterrows():

        plt.annotate(
            f'{row["rate_sell"]:.4f}',
            (
                row["rate_date"],
                row["rate_sell"]
            ),
            xytext=(0, 7),
            textcoords="offset points",
            ha="center",
            fontsize=8
        )

    plt.title(
        "USD/TWD Sell Rate - Recent 10 Trading Days"
    )

    plt.xlabel("Date")
    plt.ylabel("TWD")

    plt.grid(
        True,
        linestyle="--",
        alpha=0.3
    )

    plt.xticks(
        rotation=45
    )

    plt.tight_layout()

    plt.savefig(
        filename,
        dpi=150,
        bbox_inches="tight"
    )

    plt.close()

    return filename


# ============================================================
# 11. 建立 HTML Email
# ============================================================

def create_email_html(
    df,
    analysis
):

    latest = df.iloc[-1]

    daily_change = latest[
        "daily_change_pct"
    ]

    ten_day_change = latest[
        "ten_day_change_pct"
    ]

    # --------------------------------------------------------
    # 顏色
    # --------------------------------------------------------

    if daily_change > 0:
        daily_color = "#d32f2f"

    elif daily_change < 0:
        daily_color = "#388e3c"

    else:
        daily_color = "#555555"


    if ten_day_change > 0:
        ten_day_color = "#d32f2f"

    elif ten_day_change < 0:
        ten_day_color = "#388e3c"

    else:
        ten_day_color = "#555555"


    # --------------------------------------------------------
    # 十日資料表
    # --------------------------------------------------------

    table_rows = ""

    for _, row in df.iloc[::-1].iterrows():

        daily = row[
            "daily_change_pct"
        ]

        if pd.isna(daily):
            daily_text = "-"

        else:
            daily_text = (
                f"{daily:+.2f}%"
            )

        table_rows += f"""
        <tr>
            <td>
                {row["rate_date"].strftime("%Y-%m-%d")}
            </td>

            <td>
                {row["rate_sell"]:.4f}
            </td>

            <td>
                {daily_text}
            </td>

            <td>
                {row["ten_day_change_pct"]:+.2f}%
            </td>
        </tr>
        """


    # --------------------------------------------------------
    # HTML
    # --------------------------------------------------------

    html = f"""
<!DOCTYPE html>

<html>

<head>

<meta charset="UTF-8">

<style>

body {{
    font-family:
        Arial,
        "Microsoft JhengHei",
        sans-serif;

    color: #333;

    line-height: 1.6;

    background-color: #ffffff;
}}

.container {{
    max-width: 900px;

    margin: auto;
}}

.header {{
    background-color: #1976D2;

    color: white;

    padding: 20px;

    border-radius: 8px;
}}

.summary {{
    display: flex;

    gap: 15px;

    margin-top: 20px;
}}

.card {{
    flex: 1;

    background-color: #f5f7fa;

    padding: 15px;

    border-radius: 8px;

    border: 1px solid #e0e0e0;
}}

.card-title {{
    color: #666;

    font-size: 14px;
}}

.card-value {{
    font-size: 24px;

    font-weight: bold;
}}

.section {{
    margin-top: 25px;
}}

.analysis {{
    background-color: #f8f9fa;

    border-left: 5px solid #1976D2;

    padding: 15px;

    border-radius: 5px;
}}

.analysis-item {{
    margin-bottom: 12px;
}}

.analysis-title {{
    font-weight: bold;

    color: #1976D2;
}}

table {{
    border-collapse: collapse;

    width: 100%;

    margin-top: 10px;
}}

th {{
    background-color: #1976D2;

    color: white;

    padding: 8px;
}}

td {{
    border: 1px solid #ddd;

    padding: 8px;

    text-align: center;
}}

tr:nth-child(even) {{
    background-color: #f8f8f8;
}}

.footer {{
    color: #888;

    font-size: 12px;

    margin-top: 30px;

    border-top: 1px solid #ddd;

    padding-top: 10px;
}}

</style>

</head>


<body>

<div class="container">

<div class="header">

<h1>
USD/TWD 每日匯率分析報告
</h1>

<p>
掛牌日期：
<strong>
{latest["rate_date"].strftime("%Y-%m-%d")}
</strong>
</p>

</div>


<!-- ================================================== -->
<!-- Summary -->
<!-- ================================================== -->

<div class="summary">

<div class="card">

<div class="card-title">
今日賣出匯率
</div>

<div class="card-value">
{latest["rate_sell"]:.4f}
</div>

</div>


<div class="card">

<div class="card-title">
較前一交易日
</div>

<div
    class="card-value"
    style="color:{daily_color}"
>

{daily_change:+.2f}%

</div>

</div>


<div class="card">

<div class="card-title">
十日累積變化
</div>

<div
    class="card-value"
    style="color:{ten_day_color}"
>

{ten_day_change:+.2f}%

</div>

</div>

</div>


<!-- ================================================== -->
<!-- Chart -->
<!-- ================================================== -->

<div class="section">

<h2>
十日匯率走勢
</h2>

<img
    src="cid:exchange_chart"
    style="width:100%; max-width:850px;"
>

</div>


<!-- ================================================== -->
<!-- AI Analysis -->
<!-- ================================================== -->

<div class="section">

<h2>
AI 匯率分析
</h2>

<div class="analysis">


<div class="analysis-item">

<span class="analysis-title">
趨勢：
</span>

{analysis.get("trend", "")}

</div>


<div class="analysis-item">

<span class="analysis-title">
趨勢強度：
</span>

{analysis.get("trend_strength", "")}

</div>


<div class="analysis-item">

<span class="analysis-title">
今日變化：
</span>

{analysis.get("daily_summary", "")}

</div>


<div class="analysis-item">

<span class="analysis-title">
十日變化：
</span>

{analysis.get("ten_day_summary", "")}

</div>


<div class="analysis-item">

<span class="analysis-title">
波動程度：
</span>

{analysis.get("volatility", "")}

</div>


<div class="analysis-item">

<span class="analysis-title">
值得注意：
</span>

{analysis.get("observation", "")}

</div>


<div class="analysis-item">

<span class="analysis-title">
短期觀察：
</span>

{analysis.get("short_term_view", "")}

</div>


<div class="analysis-item">

<span class="analysis-title">
變動原因說明：
</span>

{analysis.get("cause_note", "")}

</div>


<div class="analysis-item">

<span class="analysis-title">
財務風險觀察：
</span>

{analysis.get("risk_note", "")}

</div>


</div>

</div>


<!-- ================================================== -->
<!-- Data Table -->
<!-- ================================================== -->

<div class="section">

<h2>
最近十筆匯率資料
</h2>


<table>

<tr>

<th>
掛牌日期
</th>

<th>
美元賣出匯率
</th>

<th>
日變動率
</th>

<th>
十日累積變動率
</th>

</tr>

{table_rows}

</table>

</div>


<div class="footer">

本報告由系統自動產生。

<br>

AI 分析僅根據本報告提供之匯率資料，
不代表投資建議或未來匯率預測。

</div>


</div>

</body>

</html>
"""

    return html


# ============================================================
# 12. Gmail 寄信
# ============================================================

def send_email(
    subject,
    html,
    chart_file
):

    message = MIMEMultipart(
        "related"
    )

    message["Subject"] = subject

    message["From"] = GMAIL_USERNAME

    message["To"] = ", ".join(
        MAIL_TO
    )


    # --------------------------------------------------------
    # HTML
    # --------------------------------------------------------

    html_part = MIMEText(
        html,
        "html",
        "utf-8"
    )

    message.attach(
        html_part
    )


    # --------------------------------------------------------
    # Embedded image
    # --------------------------------------------------------

    with open(
        chart_file,
        "rb"
    ) as f:

        image = MIMEImage(
            f.read()
        )

    image.add_header(
        "Content-ID",
        "<exchange_chart>"
    )

    image.add_header(
        "Content-Disposition",
        "inline",
        filename=os.path.basename(
            chart_file
        )
    )

    message.attach(
        image
    )


    # --------------------------------------------------------
    # Gmail SMTP
    # --------------------------------------------------------

    with smtplib.SMTP(
        "smtp.gmail.com",
        587,
        timeout=30
    ) as server:

        server.ehlo()

        server.starttls()

        server.ehlo()

        server.login(
            GMAIL_USERNAME,
            GMAIL_APP_PASSWORD
        )

        server.sendmail(
            GMAIL_USERNAME,
            MAIL_TO,
            message.as_string()
        )


# ============================================================
# 13. 主程式
# ============================================================

def main():

    print("=" * 60)

    print(
        "USD/TWD 每日匯率 AI 分析報告"
    )

    print(
        "開始時間：",
        datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )
    )

    print("=" * 60)


    # --------------------------------------------------------
    # Configuration
    # --------------------------------------------------------

    validate_config()


    # --------------------------------------------------------
    # 取得匯率
    # --------------------------------------------------------

    print(
        "\n[1/5] 讀取 SQLite..."
    )

    df = get_exchange_rates()

    print(
        df.to_string(index=False)
    )


    # --------------------------------------------------------
    # 計算變化
    # --------------------------------------------------------

    print(
        "\n[2/5] 計算匯率變化..."
    )

    df = calculate_changes(
        df
    )

    latest = df.iloc[-1]

    print(
        f"今日匯率："
        f"{latest['rate_sell']:.4f}"
    )

    print(
        f"日變動："
        f"{latest['daily_change_pct']:+.2f}%"
    )

    print(
        f"十日累積："
        f"{latest['ten_day_change_pct']:+.2f}%"
    )


    # --------------------------------------------------------
    # OpenAI
    # --------------------------------------------------------

    print(
        "\n[3/5] 呼叫 OpenAI..."
    )

    try:

        analysis = analyze_with_openai(
            df
        )

        print(
            "OpenAI 分析完成"
        )

    except Exception as e:

        print(
            "OpenAI 分析失敗：",
            str(e)
        )

        analysis = (
            create_fallback_analysis(
                df
            )
        )


    # --------------------------------------------------------
    # Chart
    # --------------------------------------------------------

    print(
        "\n[4/5] 建立十日走勢圖..."
    )

    chart_file = create_chart(
        df
    )

    print(
        f"圖表：{chart_file}"
    )


    # --------------------------------------------------------
    # Email
    # --------------------------------------------------------

    print(
        "\n[5/5] 寄送 Gmail..."
    )

    html = create_email_html(
        df,
        analysis
    )

    report_date = latest[
        "rate_date"
    ].strftime(
        "%Y-%m-%d"
    )

    subject = (
        f"【每日匯率 AI 分析】"
        f"USD/TWD {report_date}"
    )

    send_email(
        subject,
        html,
        chart_file
    )

    print(
        "\nEmail 寄送成功！"
    )

    print(
        "完成時間：",
        datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )
    )


# ============================================================
# 14. Entry Point
# ============================================================

if __name__ == "__main__":

    try:

        main()

    except Exception as e:

        print(
            "\n程式執行失敗："
        )

        print(
            str(e)
        )

        traceback.print_exc()

        raise
