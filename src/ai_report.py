from openai import OpenAI
from config import OPENAI_API_KEY, OPENAI_MODEL


def generate_ai_report(
    statistics: dict
) -> str:

    client = OpenAI(
        api_key=OPENAI_API_KEY
    )

    daily_changes = statistics["daily_changes"]

    rows = []

    for _, row in daily_changes.iterrows():

        change = row["daily_changes"]

        if change != change:  # NaN
            change_text = "N/A"
        else:
            change_text = f"{change * 100:.3f}%"

        rows.append(
            f"{row['日期'].strftime('%Y-%m-%d')} "
            f"匯率={row['即期賣出']:.4f} "
            f"日變動={row['每日變動%']:.3f}"
        )

    daily_data = "\n".join(rows)

    prompt = f"""
你是一位金融市場資料分析助手。

請根據以下 USD/TWD 過去 30 天資料，
撰寫一份「美元兌新台幣匯率分析報告」。

請注意：
1. 只根據提供的資料分析。
2. 不要捏造不存在的資料。
3. 不要提供投資買賣建議。
4. 明確區分「資料觀察」與「可能的解讀」。
5. 如果資料不足以支持某個結論，請明確說明。
6. 使用繁體中文。

【期間】
{statistics["start_date"]}
至
{statistics["end_date"]}

【基本統計】

起始匯率：
{statistics["start_rate"]:.4f}

最新匯率：
{statistics["end_rate"]:.4f}

最高匯率：
{statistics["max_rate"]:.4f}

最低匯率：
{statistics["min_rate"]:.4f}

每日變動率標準差：
{statistics["daily_change_std"] * 100:.4f}%

累積變動率：
{statistics["cumulative_change"] * 100:.4f}%

【每日資料】

{daily_data}

請使用以下格式：

一、期間概況

二、價格區間

三、波動程度

四、累積變化

五、資料趨勢觀察

六、風險與限制

報告應該簡潔、專業，約 500～800 字。
"""

    response = client.responses.create(
        model=OPENAI_MODEL,
        input=prompt
    )

    return response.output_text
