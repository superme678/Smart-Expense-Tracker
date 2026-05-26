"""图表可视化模块：使用 matplotlib 生成月度报表。"""

from typing import Dict, List

import matplotlib.pyplot as plt

from data_manager import DataManager

# 设置中文字体，避免图表中文乱码
plt.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False


def plot_monthly_pie(data_manager: DataManager, year_month: str) -> None:
    """
    统计指定月份各分类支出占比，绘制饼图。

    :param data_manager: 数据管理器实例
    :param year_month: 年月字符串，格式 YYYY-MM
    """
    transactions = data_manager.get_transactions_by_month(year_month)
    # 仅统计支出
    expense_txns = [t for t in transactions if t.type == "expense"]

    if not expense_txns:
        print(f"{year_month} 暂无支出记录，无法生成饼图。")
        return

    # 按分类汇总支出金额
    category_totals: Dict[str, float] = {}
    for txn in expense_txns:
        category = data_manager.categories.get(txn.category_id)
        name = category.name if category else f"分类{txn.category_id}"
        category_totals[name] = category_totals.get(name, 0.0) + txn.amount

    labels = list(category_totals.keys())
    sizes = list(category_totals.values())

    plt.figure(figsize=(8, 6))
    plt.pie(sizes, labels=labels, autopct="%1.1f%%", startangle=90)
    plt.title(f"{year_month} 月度支出分类占比")
    plt.axis("equal")
    plt.tight_layout()
    plt.show()


def plot_monthly_trend(data_manager: DataManager, months: int = 6) -> None:
    """
    统计最近若干个月的收入与支出总额，绘制折线图。

    :param data_manager: 数据管理器实例
    :param months: 显示最近几个月，默认 6 个月
    """
    summary = data_manager.get_monthly_summary()

    if not summary:
        print("暂无交易记录，无法生成趋势图。")
        return

    # 按年月排序，取最近 months 个月（或全部月份）
    sorted_months: List[str] = sorted(summary.keys())
    if len(sorted_months) > months:
        sorted_months = sorted_months[-months:]

    income_data = [summary[m]["income"] for m in sorted_months]
    expense_data = [summary[m]["expense"] for m in sorted_months]

    plt.figure(figsize=(10, 6))
    plt.plot(sorted_months, income_data, marker="o", label="收入", color="#2ecc71")
    plt.plot(sorted_months, expense_data, marker="s", label="支出", color="#e74c3c")
    plt.title("月度收支趋势图")
    plt.xlabel("月份")
    plt.ylabel("金额（元）")
    plt.legend()
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()
