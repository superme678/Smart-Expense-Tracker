"""数据模型模块：定义用户、分类、交易等核心类。"""

from dataclasses import dataclass, asdict
from typing import Any, Dict


@dataclass
class User:
    """用户类，表示记账系统的使用者。"""

    user_id: int
    username: str
    created_at: str

    def __repr__(self) -> str:
        """返回用户的可读字符串表示。"""
        return f"User(user_id={self.user_id}, username='{self.username}', created_at='{self.created_at}')"

    def to_dict(self) -> Dict[str, Any]:
        """将用户对象序列化为字典。"""
        return asdict(self)


@dataclass
class Category:
    """分类类，表示收入或支出类别。"""

    category_id: int
    name: str
    type: str  # "income" 或 "expense"

    def __repr__(self) -> str:
        """返回分类的可读字符串表示。"""
        return f"Category(category_id={self.category_id}, name='{self.name}', type='{self.type}')"

    def to_dict(self) -> Dict[str, Any]:
        """将分类对象序列化为字典。"""
        return asdict(self)


# 预置常用分类（首次初始化数据库时使用）
DEFAULT_CATEGORIES = [
    ("餐饮", "expense"),
    ("交通", "expense"),
    ("购物", "expense"),
    ("娱乐", "expense"),
    ("工资", "income"),
    ("奖金", "income"),
    ("其他支出", "expense"),
    ("其他收入", "income"),
]


@dataclass
class Transaction:
    """账目类，表示一条收入或支出记录。"""

    transaction_id: int
    user_id: int
    date: str
    amount: float
    category_id: int
    type: str  # "income" 或 "expense"
    note: str = ""

    def __repr__(self) -> str:
        """返回交易记录的可读字符串表示。"""
        return (
            f"Transaction(transaction_id={self.transaction_id}, user_id={self.user_id}, "
            f"date='{self.date}', amount={self.amount}, category_id={self.category_id}, "
            f"type='{self.type}', note='{self.note}')"
        )

    def to_dict(self) -> Dict[str, Any]:
        """将交易对象序列化为字典。"""
        return asdict(self)
