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

## 主要功能
1. 自動擷取匯率資料
定期從台灣銀行取得美元兌新台幣匯率資料，並將資料寫入資料庫。
主要資料包含：

.匯率日期
.幣別
.匯率
.即期買入匯率
.即期賣出匯率
.其他相關匯率資訊

