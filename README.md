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

