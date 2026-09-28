import os
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd


from config import CHART_PATH


def create_chart(df):

    plt.figure(
        figsize=(12, 6)
    )

    df["日期"] = pd.to_datetime(df["日期"])


    plt.plot(
        df["日期"],
        df["即期賣出"],
        marker="o",
        linewidth=2,
        markersize=4,
        color="#2563eb"
    )

    plt.title(
        "USD/TWD - 30 Day Exchange Rate Trend",
        fontsize=16
    )

    plt.xlabel("Date")
    plt.ylabel("TWD per USD")

    plt.grid(
        True,
        linestyle="--",
        alpha=0.3
    )

    plt.gca().xaxis.set_major_formatter(
        mdates.DateFormatter("%m-%d")
    )

    plt.xticks(rotation=45)

    plt.tight_layout()

    plt.savefig(
        CHART_PATH,
        dpi=150,
        bbox_inches="tight"
    )

    plt.close()

    return CHART_PATH
