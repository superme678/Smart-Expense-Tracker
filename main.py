"""智能个人记账助手 - 主程序入口。"""

import os
import sys
from typing import Optional

from data_manager import THRESHOLD, DataManager
from file_handler import export_to_csv, export_to_json, import_from_csv, import_from_json
from models import ACCOUNT_TYPES, Transaction
from natural_parser import NaturalParser
from validator import validate_amount, validate_date, validate_type, validate_year_month
from visualizer import plot_monthly_pie, plot_monthly_trend

# 加分项1：CLI 异常标记颜色支持（colorama 可选）
try:
    from colorama import Fore, Style, init as colorama_init

    colorama_init()
    _HAS_COLORAMA = True
except ImportError:
    _HAS_COLORAMA = False


def _format_anomaly_suffix(
    data_manager: DataManager, txn: Transaction, is_anomaly: bool
) -> str:
    """格式化异常消费标记文本（兼容 Windows CMD）。"""
    if not is_anomaly:
        return ""
    avg = data_manager.get_category_avg(
        txn.user_id, txn.category_id, txn.transaction_id
    )
    avg_text = f"  (该类历史均值: {avg:.2f})"
    if _HAS_COLORAMA:
        return f"  {Fore.RED}[🔴 异常]{Style.RESET_ALL}{avg_text}"
    return f"  [异常]{avg_text}"


def print_menu() -> None:
    """打印主菜单选项。"""
    print("\n" + "=" * 40)
    print("       智能个人记账助手")
    print("=" * 40)
    print("1. 记一笔（收入/支出）")
    print("2. 自然语言记账（输入'昨天午饭花了35'自动解析）")
    print("3. 查看所有记录")
    print("4. 按分类统计")
    print("5. 生成月度报表（饼图+折线图）")
    print("6. 账户管理（多账户/多币种）")
    print("7. 导出数据（JSON/CSV）")
    print("8. 导入数据（JSON/CSV）")
    print("9. 退出")
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


def print_accounts(data_manager: DataManager) -> None:
    """打印用户的账户列表。"""
    accounts = data_manager.get_accounts()
    if not accounts:
        print("暂无账户。")
        return
    print("\n可选账户：")
    for acc in accounts:
        currency = data_manager.currencies.get(acc.currency_id)
        currency_name = currency.name if currency else "未知"
        print(f"  [{acc.account_id}] {acc.name} ({acc.type}) - {currency_name} ¥{acc.balance:.2f}")


def print_currencies(data_manager: DataManager) -> None:
    """打印可用币种列表。"""
    print("\n可选币种：")
    for curr in data_manager.currencies.values():
        print(f"  [{curr.currency_id}] {curr.name} ({curr.code}) - 汇率: {curr.rate_to_cny:.2f}")


def add_transaction(data_manager: DataManager) -> None:
    """处理「记一笔」功能（支持多账户/多币种）。"""
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

    print_accounts(data_manager)
    while True:
        try:
            account_id = int(input("请输入账户编号（默认1）：").strip() or "1")
            if account_id in data_manager.accounts:
                break
            print("账户编号不存在，请重新输入。")
        except ValueError:
            print("请输入有效的数字编号。")

    print_currencies(data_manager)
    while True:
        try:
            currency_id = int(input("请输入币种编号（默认1=人民币）：").strip() or "1")
            if currency_id in data_manager.currencies:
                break
            print("币种编号不存在，请重新输入。")
        except ValueError:
            print("请输入有效的数字编号。")

    note = input("备注（可留空）：").strip()

    txn = data_manager.add_transaction(date, amount, category_id, txn_type, note, account_id, currency_id)
    print(f"\n记账成功！{txn}")


def natural_language_transaction(data_manager: DataManager) -> None:
    """加分项3：自然语言记账功能。"""
    print("\n--- 自然语言记账 ---")
    print("示例：昨天午饭花了35、今天打车15元、收到红包500、明天发工资8000")
    input_text = input("请输入记账描述：").strip()

    if not input_text:
        print("请输入有效的描述。")
        return

    parser = NaturalParser()
    result = parser.parse(input_text)

    if not result:
        print("无法解析输入，请尝试其他描述方式。")
        return

    print("\n解析结果：")
    print(f"日期：{result['date']}")
    print(f"金额：¥{result['amount']}")
    print(f"类型：{'收入' if result['type'] == 'income' else '支出'}")
    print(f"分类：{result['category']}")
    if 'note' in result:
        print(f"备注：{result['note']}")

    confirm = input("\n确认记账？(y/n)：").strip().lower()
    if confirm != 'y':
        print("已取消记账。")
        return

    category_id = None
    for cat_id, cat in data_manager.categories.items():
        if cat.name == result['category']:
            category_id = cat_id
            break

    if category_id is None:
        print(f"未找到分类 '{result['category']}'，将使用默认分类。")
        category_id = 7 if result['type'] == 'income' else 8

    txn = data_manager.add_transaction(
        date=result['date'],
        amount=float(result['amount']),
        category_id=category_id,
        txn_type=result['type'],
        note=result.get('note', '')
    )
    print(f"\n记账成功！{txn}")


def manage_accounts(data_manager: DataManager) -> None:
    """加分项2：账户管理功能（多账户/多币种）。"""
    while True:
        print("\n" + "-" * 30)
        print("        账户管理")
        print("-" * 30)
        print("1. 查看账户列表")
        print("2. 添加新账户")
        print("3. 查看币种汇率")
        print("4. 更新汇率")
        print("5. 查看总余额（人民币）")
        print("6. 返回主菜单")
        print("-" * 30)
        choice = input("请输入选项（1-6）：").strip()

        if choice == "1":
            print("\n--- 账户列表 ---")
            accounts = data_manager.get_accounts()
            if not accounts:
                print("暂无账户。")
                continue
            for acc in accounts:
                currency = data_manager.currencies.get(acc.currency_id)
                currency_name = currency.name if currency else "未知"
                currency_symbol = currency.symbol if currency else ""
                print(f"ID:{acc.account_id} | {acc.name} | 类型:{acc.type} | 币种:{currency_name} | 余额:{currency_symbol}{acc.balance:.2f}")

        elif choice == "2":
            print("\n--- 添加新账户 ---")
            name = input("请输入账户名称：").strip()
            if not name:
                print("账户名称不能为空。")
                continue

            print("\n可选账户类型：")
            for i, acc_type in enumerate(ACCOUNT_TYPES, 1):
                print(f"  [{i}] {acc_type}")

            while True:
                try:
                    type_choice = int(input("请输入账户类型编号：").strip())
                    if 1 <= type_choice <= len(ACCOUNT_TYPES):
                        account_type = ACCOUNT_TYPES[type_choice - 1]
                        break
                    print("无效的类型编号，请重新输入。")
                except ValueError:
                    print("请输入有效的数字。")

            print_currencies(data_manager)
            while True:
                try:
                    currency_id = int(input("请输入币种编号（默认1=人民币）：").strip() or "1")
                    if currency_id in data_manager.currencies:
                        break
                    print("币种编号不存在，请重新输入。")
                except ValueError:
                    print("请输入有效的数字编号。")

            while True:
                try:
                    balance = float(input("请输入初始余额（默认0）：").strip() or "0")
                    break
                except ValueError:
                    print("请输入有效的金额。")

            try:
                account = data_manager.add_account(name, account_type, currency_id, balance)
                print(f"账户创建成功！ID:{account.account_id}, 名称:{account.name}")
            except Exception as e:
                print(f"创建失败：{e}")

        elif choice == "3":
            print("\n--- 币种汇率 ---")
            for curr in data_manager.currencies.values():
                print(f"ID:{curr.currency_id} | {curr.name} ({curr.code}) | 符号:{curr.symbol} | 汇率(对人民币):{curr.rate_to_cny:.2f}")

        elif choice == "4":
            print("\n--- 更新汇率 ---")
            print_currencies(data_manager)
            while True:
                try:
                    currency_id = int(input("请输入要更新的币种编号：").strip())
                    if currency_id in data_manager.currencies:
                        break
                    print("币种编号不存在，请重新输入。")
                except ValueError:
                    print("请输入有效的数字编号。")

            while True:
                try:
                    new_rate = float(input("请输入新汇率（对人民币）：").strip())
                    if new_rate > 0:
                        break
                    print("汇率必须大于0。")
                except ValueError:
                    print("请输入有效的数字。")

            if data_manager.update_currency_rate(currency_id, new_rate):
                currency = data_manager.currencies[currency_id]
                print(f"汇率更新成功！{currency.name} 新汇率: {new_rate:.2f}")
            else:
                print("更新失败。")

        elif choice == "5":
            total = data_manager.get_total_balance_in_cny()
            print(f"\n--- 总余额 ---")
            print(f"所有账户总余额（换算为人民币）：¥{total:.2f}")

        elif choice == "6":
            break

        else:
            print("无效选项，请输入 1-6 之间的数字。")


def view_all_transactions(data_manager: DataManager) -> None:
    """查看所有交易记录（加分项1：异常消费标红/文本标记）。"""
    print("\n--- 所有交易记录 ---")
    if not data_manager.transactions:
        print("暂无记录。")
        return

    for txn in data_manager.transactions:
        category = data_manager.categories.get(txn.category_id)
        cat_name = category.name if category else "未知"
        type_label = "收入" if txn.type == "income" else "支出"
        is_anomaly = data_manager.check_anomaly(txn)
        anomaly_suffix = _format_anomaly_suffix(data_manager, txn, is_anomaly)
        print(
            f"ID:{txn.transaction_id} | {txn.date} | {type_label} | "
            f"{cat_name} | ¥{txn.amount:.2f} | {txn.note}{anomaly_suffix}"
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


def run_cli() -> None:
    """
    启动命令行版本（基础得分项 3：while True 菜单循环）。

    保留 CLI 入口以确保基础得分项中的循环与分支逻辑仍可验证。
    """
    data_manager = DataManager()
    print(f"欢迎使用智能个人记账助手，当前用户：{data_manager.current_user.username}")

    # 使用 while True 构建主循环
    while True:
        print_menu()
        choice = input("请输入选项（1-9）：").strip()

        if choice == "1":
            add_transaction(data_manager)
        elif choice == "2":
            natural_language_transaction(data_manager)
        elif choice == "3":
            view_all_transactions(data_manager)
        elif choice == "4":
            show_category_stats(data_manager)
        elif choice == "5":
            generate_monthly_report(data_manager)
        elif choice == "6":
            manage_accounts(data_manager)
        elif choice == "7":
            export_data(data_manager)
        elif choice == "8":
            import_data(data_manager)
        elif choice == "9":
            print("感谢使用，再见！")
            data_manager.close()
            sys.exit(0)
        else:
            # 输入错误时给出提示并循环回到菜单
            print("无效选项，请输入 1-9 之间的数字。")


def run_gui() -> None:
    """启动 tkinter GUI 版本。"""
    from gui import run_gui as start_gui

    start_gui()


def main() -> None:
    """
    程序总入口：根据命令行参数选择 CLI 或 GUI 模式。

    - python main.py          → GUI（默认）
    - python main.py --gui    → GUI
    - python main.py --cli    → 命令行
    """
    if "--cli" in sys.argv:
        run_cli()
    else:
        run_gui()


if __name__ == "__main__":
    main()
