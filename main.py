"""智能个人记账助手 - 主程序入口。"""

import os
import sys
from typing import Optional

from data_manager import DataManager
from file_handler import export_to_csv, export_to_json, import_from_csv, import_from_json
from models import Transaction
from validator import validate_amount, validate_date, validate_type, validate_year_month
from visualizer import plot_monthly_pie, plot_monthly_trend


def print_menu() -> None:
    """打印主菜单选项。"""
    print("\n" + "=" * 40)
    print("       智能个人记账助手")
    print("=" * 40)
    print("1. 记一笔（收入/支出）")
    print("2. 查看所有记录")
    print("3. 按分类统计")
    print("4. 生成月度报表（饼图+折线图）")
    print("5. 导出数据（JSON/CSV）")
    print("6. 导入数据（JSON/CSV）")
    print("7. 退出")
    print("=" * 40)


def print_categories(data_manager: DataManager, txn_type: str) -> None:
    """打印指定类型的分类列表。"""
    categories = data_manager.get_categories_by_type(txn_type)
    type_label = "收入" if txn_type == "income" else "支出"
    print(f"\n可选{type_label}分类：")
    for cat in categories:
        print(f"  [{cat.category_id}] {cat.name}")


def input_with_retry(prompt: str, validator_func) -> str:
    """
    带重试的输入函数，校验失败时提示并重新输入。

    :param prompt: 输入提示语
    :param validator_func: 校验函数，成功返回标准化值
    """
    while True:
        try:
            user_input = input(prompt).strip()
            return validator_func(user_input)
        except ValueError as exc:
            print(f"输入错误：{exc}，请重新输入。")


def add_transaction(data_manager: DataManager) -> None:
    """处理「记一笔」功能。"""
    print("\n--- 记一笔 ---")

    # 校验交易类型
    txn_type = input_with_retry(
        "请输入类型（income=收入 / expense=支出）：",
        validate_type,
    )
    print_categories(data_manager, txn_type)

    # 选择分类
    while True:
        try:
            category_id = int(input("请输入分类编号：").strip())
            if category_id in data_manager.categories:
                cat = data_manager.categories[category_id]
                if cat.type != txn_type:
                    print(f"该分类属于{'收入' if cat.type == 'income' else '支出'}，与所选类型不符，请重新选择。")
                    continue
                break
            print("分类编号不存在，请重新输入。")
        except ValueError:
            print("请输入有效的数字编号。")

    date = input_with_retry("请输入日期（YYYY-MM-DD）：", validate_date)
    amount = input_with_retry("请输入金额：", validate_amount)
    note = input("备注（可留空）：").strip()

    txn = data_manager.add_transaction(date, amount, category_id, txn_type, note)
    print(f"\n记账成功！{txn}")


def view_all_transactions(data_manager: DataManager) -> None:
    """查看所有交易记录。"""
    print("\n--- 所有交易记录 ---")
    if not data_manager.transactions:
        print("暂无记录。")
        return

    for txn in data_manager.transactions:
        category = data_manager.categories.get(txn.category_id)
        cat_name = category.name if category else "未知"
        type_label = "收入" if txn.type == "income" else "支出"
        print(
            f"ID:{txn.transaction_id} | {txn.date} | {type_label} | "
            f"{cat_name} | ¥{txn.amount:.2f} | {txn.note}"
        )


def show_category_stats(data_manager: DataManager) -> None:
    """按分类统计收支。"""
    print("\n--- 按分类统计 ---")
    print("1. 统计支出  2. 统计收入  3. 统计全部")
    choice = input("请选择：").strip()

    if choice == "1":
        stats = data_manager.get_category_stats("expense")
        title = "支出分类统计"
    elif choice == "2":
        stats = data_manager.get_category_stats("income")
        title = "收入分类统计"
    elif choice == "3":
        stats = data_manager.get_category_stats()
        title = "全部分类统计"
    else:
        print("无效选项，请重新选择。")
        return

    if not stats:
        print("暂无统计数据。")
        return

    print(f"\n{title}（格式：分类名 | 总额 | 笔数）：")
    for category_name, total_amount, count in stats:
        # 使用元组 (category_name, total_amount, count) 展示统计结果
        print(f"  {category_name} | ¥{total_amount:.2f} | {count} 笔")


def generate_monthly_report(data_manager: DataManager) -> None:
    """生成月度报表：饼图 + 折线图。"""
    print("\n--- 生成月度报表 ---")
    year_month = input_with_retry(
        "请输入要查看的月份（YYYY-MM，用于饼图）：",
        validate_year_month,
    )
    print(f"正在生成 {year_month} 支出饼图...")
    plot_monthly_pie(data_manager, year_month)
    print("正在生成收支趋势折线图...")
    plot_monthly_trend(data_manager)


def export_data(data_manager: DataManager) -> None:
    """导出数据到 JSON 或 CSV 文件。"""
    print("\n--- 导出数据 ---")
    print("1. 导出为 JSON  2. 导出为 CSV")
    choice = input("请选择格式：").strip()

    default_name = "transactions_export"
    filepath = input(f"请输入文件路径（默认 ./{default_name}）：").strip()
    if not filepath:
        filepath = default_name

    data = data_manager.get_all_transactions()
    if not data:
        print("暂无数据可导出。")
        return

    try:
        if choice == "1":
            if not filepath.endswith(".json"):
                filepath += ".json"
            export_to_json(data, filepath)
        elif choice == "2":
            if not filepath.endswith(".csv"):
                filepath += ".csv"
            export_to_csv(data, filepath)
        else:
            print("无效选项。")
            return
        print(f"导出成功：{os.path.abspath(filepath)}")
    except OSError as exc:
        print(f"导出失败：{exc}")


def import_data(data_manager: DataManager) -> None:
    """从 JSON 或 CSV 文件导入数据。"""
    print("\n--- 导入数据 ---")
    print("1. 从 JSON 导入  2. 从 CSV 导入")
    choice = input("请选择格式：").strip()
    filepath = input("请输入文件路径：").strip()

    if not filepath:
        print("文件路径不能为空。")
        return

    if not os.path.exists(filepath):
        print(f"文件不存在：{filepath}")
        return

    try:
        if choice == "1":
            imported = import_from_json(filepath)
        elif choice == "2":
            imported = import_from_csv(filepath)
        else:
            print("无效选项。")
            return

        count = 0
        for txn in imported:
            # 导入时使用当前用户 ID，避免 ID 冲突则作为新记录插入
            txn.user_id = data_manager.current_user.user_id
            txn.transaction_id = 0
            data_manager.save_transaction(txn)
            count += 1

        print(f"导入成功，共导入 {count} 条记录。")
    except (OSError, KeyError, ValueError) as exc:
        print(f"导入失败：{exc}")


def main() -> None:
    """主函数：构建命令行菜单循环。"""
    data_manager = DataManager()
    print(f"欢迎使用智能个人记账助手，当前用户：{data_manager.current_user.username}")

    # 使用 while True 构建主循环
    while True:
        print_menu()
        choice = input("请输入选项（1-7）：").strip()

        if choice == "1":
            add_transaction(data_manager)
        elif choice == "2":
            view_all_transactions(data_manager)
        elif choice == "3":
            show_category_stats(data_manager)
        elif choice == "4":
            generate_monthly_report(data_manager)
        elif choice == "5":
            export_data(data_manager)
        elif choice == "6":
            import_data(data_manager)
        elif choice == "7":
            print("感谢使用，再见！")
            data_manager.close()
            sys.exit(0)
        else:
            # 输入错误时给出提示并循环回到菜单
            print("无效选项，请输入 1-7 之间的数字。")


if __name__ == "__main__":
    main()
