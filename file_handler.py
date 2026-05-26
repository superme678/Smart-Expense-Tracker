"""文件读写模块：实现 JSON 与 CSV 格式的导入导出。"""

import csv
import json
from typing import Any, Dict, List

from models import Transaction


def export_to_json(data: List[Transaction], filepath: str) -> None:
    """
    将交易记录列表导出为 JSON 文件。

    :param data: Transaction 对象列表
    :param filepath: 目标文件路径
    """
    # 将对象列表转为字典列表后写入 JSON
    json_data = [item.to_dict() for item in data]
    with open(filepath, "w", encoding="utf-8") as file:
        json.dump(json_data, file, ensure_ascii=False, indent=2)


def export_to_csv(data: List[Transaction], filepath: str) -> None:
    """
    将交易记录列表导出为 CSV 文件。

    :param data: Transaction 对象列表
    :param filepath: 目标文件路径
    """
    fieldnames = [
        "transaction_id",
        "user_id",
        "date",
        "amount",
        "category_id",
        "type",
        "note",
    ]
    with open(filepath, "w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        for item in data:
            writer.writerow(item.to_dict())


def import_from_json(filepath: str) -> List[Transaction]:
    """
    从 JSON 文件读取交易记录并恢复为对象列表。

    :param filepath: JSON 文件路径
    :return: Transaction 对象列表
    """
    with open(filepath, "r", encoding="utf-8") as file:
        raw_data: List[Dict[str, Any]] = json.load(file)

    transactions: List[Transaction] = []
    for item in raw_data:
        transactions.append(
            Transaction(
                transaction_id=int(item["transaction_id"]),
                user_id=int(item["user_id"]),
                date=str(item["date"]),
                amount=float(item["amount"]),
                category_id=int(item["category_id"]),
                type=str(item["type"]),
                note=str(item.get("note", "")),
            )
        )
    return transactions


def import_from_csv(filepath: str) -> List[Transaction]:
    """
    从 CSV 文件读取交易记录并恢复为对象列表。

    :param filepath: CSV 文件路径
    :return: Transaction 对象列表
    """
    transactions: List[Transaction] = []
    with open(filepath, "r", encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)
        for row in reader:
            transactions.append(
                Transaction(
                    transaction_id=int(row["transaction_id"]),
                    user_id=int(row["user_id"]),
                    date=str(row["date"]),
                    amount=float(row["amount"]),
                    category_id=int(row["category_id"]),
                    type=str(row["type"]),
                    note=str(row.get("note", "")),
                )
            )
    return transactions
