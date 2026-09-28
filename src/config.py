import os
from pathlib import Path
from dotenv import load_dotenv


load_dotenv()


# ============================================================
# SQLite
# ============================================================

DATABASE_PATH = os.getenv("DATABASE_PATH")

# ============================================================
# OpenAI
# ============================================================

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

OPENAI_MODEL = os.getenv("OPENAI_MODEL")

# ============================================================
# Gmail
# ============================================================

GMAIL_SENDER = os.getenv("GMAIL_SENDER")

GMAIL_RECIPIENTS = [
    x.strip()
    for x in os.getenv(
        "GMAIL_RECIPIENTS",
        ""
    ).split(",")
    if x.strip()
]

CREDENTIALS_FILE = "credentials.json"

TOKEN_FILE = "token.json"

  
# ============================================================
# Report
# ============================================================

REPORT_SUBJECT_PREFIX = os.getenv("REPORT_SUBJECT_PREFIX")

CHART_PATH = os.getenv("CHART_PATH")

