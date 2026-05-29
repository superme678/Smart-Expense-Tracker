"""图表可视化模块：使用 matplotlib 生成月度报表。"""

from typing import Dict, List, Optional, Tuple

import matplotlib.pyplot as plt
from matplotlib.figure import Figure

from data_manager import DataManager

# 设置中文字体，避免图表中文乱码
plt.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False


def _get_pie_chart_data(
    data_manager: DataManager, year_month: str
) -> Tuple[List[str], List[float]]:
    """
    汇总指定月份各分类支出数据，供饼图绘制使用。

    :return: (labels, sizes) 标签列表与金额列表
    """
    transactions = data_manager.get_transactions_by_month(year_month)
    expense_txns = [t for t in transactions if t.type == "expense"]

    category_totals: Dict[str, float] = {}
    for txn in expense_txns:
        category = data_manager.categories.get(txn.category_id)
        name = category.name if category else f"分类{txn.category_id}"
        category_totals[name] = category_totals.get(name, 0.0) + txn.amount

    return list(category_totals.keys()), list(category_totals.values())


def get_monthly_pie_figure(
    data_manager: DataManager, year_month: str
) -> Optional[Figure]:
    """
    生成月度支出饼图 Figure 对象，供 tkinter 嵌入使用。

    :param data_manager: 数据管理器实例
    :param year_month: 年月字符串，格式 YYYY-MM
    :return: matplotlib Figure，无数据时返回 None
    """
    labels, sizes = _get_pie_chart_data(data_manager, year_month)
    if not labels:
        return None

    fig, ax = plt.subplots(figsize=(8, 6))
    ax.pie(sizes, labels=labels, autopct="%1.1f%%", startangle=90)
    ax.set_title(f"{year_month} 月度支出分类占比")
    ax.axis("equal")
    fig.tight_layout()
    return fig


def get_monthly_trend_figure(
    data_manager: DataManager, months: int = 6
) -> Optional[Figure]:
    """
    生成月度收支趋势折线图 Figure 对象，供 tkinter 嵌入使用。

    :param data_manager: 数据管理器实例
    :param months: 显示最近几个月，默认 6 个月
    :return: matplotlib Figure，无数据时返回 None
    """
    summary = data_manager.get_monthly_summary()
    if not summary:
        return None

    sorted_months: List[str] = sorted(summary.keys())
    if len(sorted_months) > months:
        sorted_months = sorted_months[-months:]

    income_data = [summary[m]["income"] for m in sorted_months]
    expense_data = [summary[m]["expense"] for m in sorted_months]

    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(sorted_months, income_data, marker="o", label="收入", color="#2ecc71")
    ax.plot(sorted_months, expense_data, marker="s", label="支出", color="#e74c3c")
    ax.set_title("月度收支趋势图")
    ax.set_xlabel("月份")
    ax.set_ylabel("金额（元）")
    ax.legend()
    ax.grid(True, linestyle="--", alpha=0.6)
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right")
    fig.tight_layout()
    return fig


def plot_monthly_pie(data_manager: DataManager, year_month: str) -> None:
    """
    统计指定月份各分类支出占比，绘制饼图（弹窗显示）。

    :param data_manager: 数据管理器实例
    :param year_month: 年月字符串，格式 YYYY-MM
    """
    fig = get_monthly_pie_figure(data_manager, year_month)
    if fig is None:
        print(f"{year_month} 暂无支出记录，无法生成饼图。")
        return
    plt.show()


def plot_monthly_trend(data_manager: DataManager, months: int = 6) -> None:
    """
    统计最近若干个月的收入与支出总额，绘制折线图（弹窗显示）。

    :param data_manager: 数据管理器实例
    :param months: 显示最近几个月，默认 6 个月
    """
    fig = get_monthly_trend_figure(data_manager, months)
    if fig is None:
        print("暂无交易记录，无法生成趋势图。")
        return
    plt.show()
