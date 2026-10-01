# USD/TWD Exchange Rate Analysis & AI Report

一套以 Python 建置的 USD/TWD（美元兌新台幣）匯率自動化分析系統。

系統透過排程程式定期擷取台灣銀行美元兌新台幣匯率資料，將資料儲存至資料庫，並使用最近 30 日匯率資料進行統計分析。

接著，系統會將原始匯率資料與統計結果提供給 AI，產生自然語言匯率分析報告，最後透過 Email 自動寄送給指定人員。

---

## 📌 專案目的

將原本需要人工執行的：

> 匯率資料蒐集 → 資料儲存 → 統計分析 → 報告撰寫 → Email 發送

流程自動化。

透過排程機制定期執行，讓使用者可以自動收到包含以下內容的 Email：

- 近期匯率資料
- 匯率統計資訊
- AI 匯率分析報告

## 🏗️ 技術架構

flowchart TB

    subgraph External["External Services"]
        Bank["台灣銀行"]
        AI["AI API"]
        Gmail["Gmail / Email"]
    end

    subgraph Application["Python Application"]
        Scheduler["Scheduler"]
        Collector["Crawler / Data Collector"]
        Analysis["Analysis Engine"]
        Reporter["AI Report Generator"]
        Mailer["Email Sender"]
    end

    subgraph Storage["Data Storage"]
        DB[("Database")]
    end

    Scheduler --> Collector
    Bank --> Collector
    Collector --> DB

    DB --> Analysis
    DB --> Reporter
    Analysis --> Reporter

    Reporter --> AI
    AI --> Reporter

    Reporter --> Mailer
    Mailer --> Gmail


## 🔄 系統流程

開始<br>
↓<br>
從台灣銀行取得匯率資料<br>
↓<br>
Database - USD/TWD Data<br>
↓<br>
取得最近 30 日資料<br>
↓<br>
計算統計資訊<br>
↓<br>
AI Engine<br>
↓<br>
產生 AI 分析報告<br>
↓<br>
Email Service<br>
↓<br>
Recipients
<br>
<br>
流程說明<br>
取得匯率資料：從台灣銀行取得最新 USD/TWD 匯率資料。<br>
資料儲存：將匯率資料寫入 Database。<br>
取得歷史資料：從 Database 取得最近 30 日的匯率資料。<br>
統計分析：計算最高匯率、最低匯率、每日變動率及累積變動率。<br>
AI 分析：將匯率資料與統計結果提供給 AI Engine。<br>
產生報告：AI 根據提供的資料產生自然語言分析報告。<br>
Email 發送：將匯率資料、統計資訊及 AI 分析報告寄送給指定收件者。<br>

## 🚀主要功能
1. 自動擷取匯率資料<br>
定期從台灣銀行取得美元兌新台幣匯率資料，並將資料寫入資料庫。<br>
主要資料包含：<br>
    .匯率日期<br>
    .幣別<br>
    .匯率<br>
    .即期買入匯率<br>
    .即期賣出匯率<br>
    .其他相關匯率資訊<br>
2. 資料庫儲存<br>
將每日取得的匯率資料保存於資料庫，避免每次分析時都需要重新取得歷史資料。<br>
資料庫同時作為：<br>
    .歷史匯率資料來源<br>
    .統計分析資料來源<br>
    .AI 分析資料來源<br>
3. 30 日匯率統計分析<br>
系統會取得最近 30 日的 USD/TWD 匯率資料，並計算相關統計資訊：<br>
    .最高匯率<br>
    .最低匯率<br>
    .每日匯率變動率<br>
    .30 日累積變動率<br>
4. AI 匯率分析報告<br>
系統會將以下資料提供給 AI：<br>
分析期間<br>
    .最近 30 日每日匯率<br>
    .最高匯率<br>
    .最低匯率<br>
    .每日匯率變動率<br>
    .累積變動率<br>
AI 根據提供的資料產生自然語言分析報告。<br>
分析內容主要包含：<br>
    .期間概況<br>
    .價格區間<br>
    .波動程度<br>
    .累積變化<br>
    .資料趨勢觀察<br>
    .風險與限制<br>
AI 分析以系統提供的資料為基礎，不額外捏造不存在的市場資料。<br>
5. Email 自動發送<br>
完成資料分析及 AI 報告產生後，系統會自動建立 Email，將分析結果寄送給指定人員。<br>
Email 內容包含：<br>
    .USD/TWD 最近 30 日匯率資料<br>
    .匯率統計資訊<br>
    .AI 匯率分析報告<br>

## 📁 專案架構

<ul> <li> <strong>project/</strong> <ul> <li> <strong>src/</strong> <ul> <li>app.py</li> <li>config.py</li> <li>bank_rate.py</li> <li>database.py</li> <li>analysis.py</li> <li>chart.py</li> <li>ai_report.py</li> <li>gmail_sender.py</li> </ul> </li> <li> <strong>sql/</strong> <ul> <li>init.sql</li> </ul> </li> <li> <strong>tests/</strong> <ul> <li>test_bank_rate.py</li> <li>test_analysis.py</li> <li>test_database.py</li> </ul> </li> <li>.env.example</li> <li>.gitignore</li> <li>requirements.txt</li> <li>README.md</li> <li>LICENSE</li> </ul> </li> </ul><br>
credentials.json、token.json、.env 等敏感檔案應保留在本機，不應提交至 Git repository。<br>

## 🔧 技術流程
系統主要分為以下幾個階段：<br>
Data Collection<br>
    .從台灣銀行取得 USD/TWD 匯率資料。<br>
Data <br>
    .將取得的資料寫入資料庫。<br>
Data Analysis<br>
    .從資料庫取得最近 30 日資料，計算匯率統計資訊。<br>
AI Analysis<br>
    .將每日匯率資料與統計結果傳送給 AI，產生自然語言分析報告。<br>
Notification<br>
    .將統計資料及 AI 分析結果整理成 Email 並寄送。<br>

## ⏰ 排程執行
系統可透過排程機制定期執行：<br>

Scheduler<br>
    ↓<br>
取得最新匯率<br>
    ↓<br>
寫入 Database<br>
    ↓<br>
取得最近 30 日資料<br>
    ↓<br>
計算統計資訊<br>
    ↓<br>
AI 產生分析報告<br>
    ↓<br>
Email 發送<br>

實際排程方式可依部署環境使用：<br>
Windows Task Scheduler<br>
Linux Cron<br>
Docker / Container Scheduler<br>
Cloud Scheduler<br>
CI/CD Scheduled Job<br>

## 📊 統計計算
每日匯率變動率<br>
每日匯率變動率依前一交易日匯率計算：<br>
    > 每日變動率 ＝ (（當日滙率 - 前一交易日匯率）/ 前一交易日匯率 ) * 100 % <br>
    
累積變動率<br>
以分析期間第一筆與最後一筆匯率計算：<br>
    >累積變動率 ＝ （（最新匯率 - 起始匯率）/ 起始匯率 ）* 100 % <br>

## 🤖 AI 分析原則
AI 分析報告遵循以下原則：<br>
    .僅根據系統提供的資料進行分析。<br>
    .不捏造不存在的市場資料。<br>
    .明確區分「資料觀察」與「可能的解讀」。<br>
    .當資料不足以支持某項結論時，明確說明限制。<br>
    .不提供投資買賣建議。<br>
    .分析結果僅作為資料整理與市場資訊參考。<br>

## 🛠️ 環境需求
建議環境：<br>
    .Python 3.x<br>
    .Database<br>
    .AI API<br>
    .Gmail API + OAuth 2.0<br>

## 🔐 環境變數
敏感資訊不應直接寫入程式碼或提交至 GitHub。<br>
建議使用 .env：<br>
DATABASE_HOST=<br>
DATABASE_PORT=<br>
DATABASE_NAME=<br>
DATABASE_USER=<br>
DATABASE_PASSWORD=<br>

AI_API_KEY=<br>

EMAIL_FROM=<br>
EMAIL_TO=<br>



