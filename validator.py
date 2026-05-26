"""输入校验模块：使用正则表达式校验用户输入。"""

import re
from datetime import datetime


# 日期格式：YYYY-MM-DD
DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")

# 金额格式：正数，最多两位小数
AMOUNT_PATTERN = re.compile(r"^\d+(\.\d{1,2})?$")

# 类型格式：仅允许 income 或 expense（宽松匹配，忽略大小写和首尾空格）
TYPE_PATTERN = re.compile(r"^\s*(income|expense)\s*$", re.IGNORECASE)


def validate_date(date_str: str) -> str:
    """
    校验日期字符串格式及合法性。

    :param date_str: 待校验的日期字符串
    :return: 标准化后的日期字符串 YYYY-MM-DD
    :raises ValueError: 格式不合法或日期不存在时抛出
    """
    if not DATE_PATTERN.match(date_str):
        raise ValueError("日期格式错误，请使用 YYYY-MM-DD 格式，例如 2024-06-15")

    try:
        parsed = datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError as exc:
        raise ValueError(f"日期不合法：{date_str}") from exc

    return parsed.strftime("%Y-%m-%d")


def validate_amount(amount_str: str) -> float:
    """
    校验金额字符串格式及数值合法性。

    :param amount_str: 待校验的金额字符串
    :return: 转换后的浮点金额
    :raises ValueError: 格式不合法或非正数时抛出
    """
    amount_str = amount_str.strip()
    if not AMOUNT_PATTERN.match(amount_str):
        raise ValueError("金额格式错误，请输入正数，最多保留两位小数，例如 12.50")

    amount = float(amount_str)
    if amount <= 0:
        raise ValueError("金额必须为正数")

    return amount


def validate_type(type_str: str) -> str:
    """
    校验交易类型，仅允许 income 或 expense。

    :param type_str: 待校验的类型字符串
    :return: 标准化后的类型（小写）
    :raises ValueError: 类型不合法时抛出
    """
    match = TYPE_PATTERN.match(type_str)
    if not match:
        raise ValueError("类型错误，仅允许 income（收入）或 expense（支出）")

    return match.group(1).lower()


def validate_year_month(year_month: str) -> str:
    """
    校验年月格式 YYYY-MM。

    :param year_month: 待校验的年月字符串
    :return: 标准化后的年月字符串
    :raises ValueError: 格式不合法时抛出
    """
    pattern = re.compile(r"^\d{4}-\d{2}$")
    if not pattern.match(year_month):
        raise ValueError("年月格式错误，请使用 YYYY-MM 格式，例如 2024-06")

    year, month = year_month.split("-")
    if not (1 <= int(month) <= 12):
        raise ValueError("月份必须在 01-12 之间")

    return year_month
