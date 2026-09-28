import base64
import os

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow


from config import (
    TOKEN_FILE,
    CREDENTIALS_FILE,
    GMAIL_SENDER,
    GMAIL_RECIPIENTS
)


SCOPES = [
    "https://www.googleapis.com/auth/gmail.send"
]


def get_gmail_service():
    creds=None

    #如果之前己經授權過
    if os.path.exists(TOKEN_FILE):
        creds=Credentials.from_authorized_user_file(
            TOKEN_FILE,
            SCOPES
        )
        
     #如果沒有憑證或憑證己失效
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            
            flow=InstalledAppFlow.from_client_secrets_file(
                    CREDENTIALS_FILE,
                    SCOPES
            )            

            creds=flow.run_local_server(port=8080, open_browser=True)
        
        with open(TOKEN_FILE,"w") as token:
            token.write(creds.to_json())
        
    service=build(
        "gmail",
        "v1",
        credentials=creds
    )
    
    return service




def build_email(
    sender: str,
    to_email: list,
    subject: str,
    statistics: dict,
    ai_report: str,
    chart_path: str
):

    message = MIMEMultipart("related")

    message["From"] = sender
    message["To"] = ",".join(to_email)
    message["Subject"] = subject

    # HTML Email
    html = f"""
    <html>
    <body style="
        font-family: Arial, sans-serif;
        color: #333;
        line-height: 1.6;
    ">

    <h2>USD/TWD 30天匯率分析報告</h2>

    <p>
        分析期間：
        <b>{statistics["start_date"]}</b>
        至
        <b>{statistics["end_date"]}</b>
    </p>

    <h3>一、統計摘要</h3>

    <table
        border="1"
        cellpadding="8"
        cellspacing="0"
        style="border-collapse: collapse;"
    >

        <tr>
            <td>起始匯率</td>
            <td>{statistics["start_rate"]:.4f}</td>
        </tr>

        <tr>
            <td>最新匯率</td>
            <td>{statistics["end_rate"]:.4f}</td>
        </tr>

        <tr>
            <td>30天最高</td>
            <td>{statistics["max_rate"]:.4f}</td>
        </tr>

        <tr>
            <td>30天最低</td>
            <td>{statistics["min_rate"]:.4f}</td>
        </tr>

        <tr>
            <td>每日變動率標準差</td>
            <td>
                {statistics["daily_change_std"] * 100:.4f}%
            </td>
        </tr>

        <tr>
            <td>累積變動率</td>
            <td>
                {statistics["cumulative_change"] * 100:.4f}%
            </td>
        </tr>

    </table>

    <h3>二、30天匯率趨勢</h3>

    <p>
        <img
            src="cid:usd_twd_chart"
            style="max-width: 900px; width: 100%;"
        >
    </p>

    <h3>三、AI 分析報告</h3>

    <div style="
        white-space: pre-wrap;
        background-color: #f5f5f5;
        padding: 15px;
        border-radius: 5px;
    ">
{ai_report}
    </div>

    <hr>

    <p style="color: #777; font-size: 12px;">
        本報告由系統依據 SQLite 匯率資料自動產生，
        AI 分析僅供資料解讀，不構成投資建議。
    </p>

    </body>
    </html>
    """

    html_part = MIMEText(
        html,
        "html",
        "utf-8"
    )

    message.attach(html_part)

    # 將趨勢圖內嵌到 Email
    with open(chart_path, "rb") as f:

        image = MIMEImage(
            f.read(),
            _subtype="png"
        )

    image.add_header(
        "Content-ID",
        "<usd_twd_chart>"
    )

    image.add_header(
        "Content-Disposition",
        "inline",
        filename=os.path.basename(chart_path)
    )

    message.attach(image)

    return message


def send_email(
    statistics: dict,
    ai_report: str,
    chart_path: str
):

    service = get_gmail_service()

    subject = (
        f"USD/TWD 30天匯率分析 "
        f"{statistics['end_date']}"
    )

    message = build_email(
        GMAIL_SENDER,
        GMAIL_RECIPIENTS,
        subject,
        statistics,
        ai_report,
        chart_path
    )

    encoded_message = base64.urlsafe_b64encode(
        message.as_bytes()
    ).decode()

    body = {
        "raw": encoded_message
    }

    result = (
        service.users()
        .messages()
        .send(
            userId="me",
            body=body
        )
        .execute()
    )

    print(
        "Gmail 已寄出，Message ID:",
        result["id"]
    )

    return result
