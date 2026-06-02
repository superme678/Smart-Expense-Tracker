"""数据模型模块：定义用户、分类、交易、账户、币种等核心类。"""

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
class Currency:
    """币种类，表示支持的货币类型。"""

    currency_id: int
    code: str  # 货币代码，如 CNY、USD、EUR
    name: str  # 货币名称，如人民币、美元、欧元
    symbol: str  # 货币符号，如 ¥、$、€
    rate_to_cny: float  # 对人民币的汇率

    def __repr__(self) -> str:
        """返回币种的可读字符串表示。"""
        return f"Currency(currency_id={self.currency_id}, code='{self.code}', name='{self.name}', symbol='{self.symbol}', rate_to_cny={self.rate_to_cny})"

    def to_dict(self) -> Dict[str, Any]:
        """将币种对象序列化为字典。"""
        return asdict(self)


# 预置常用币种（首次初始化数据库时使用）
DEFAULT_CURRENCIES = [
    ("CNY", "人民币", "¥", 1.0),
    ("USD", "美元", "$", 7.24),
    ("EUR", "欧元", "€", 7.86),
    ("JPY", "日元", "¥", 0.048),
    ("GBP", "英镑", "£", 9.12),
]


@dataclass
class Account:
    """账户类，表示用户的银行账户、现金等。"""

    account_id: int
    user_id: int
    name: str  # 账户名称，如工资卡、支付宝、现金
    type: str  # 账户类型：cash（现金）、card（银行卡）、alipay（支付宝）、wechat（微信）等
    balance: float  # 账户余额
    currency_id: int  # 默认币种 ID

    def __repr__(self) -> str:
        """返回账户的可读字符串表示。"""
        return f"Account(account_id={self.account_id}, user_id={self.user_id}, name='{self.name}', type='{self.type}', balance={self.balance}, currency_id={self.currency_id})"

    def to_dict(self) -> Dict[str, Any]:
        """将账户对象序列化为字典。"""
        return asdict(self)


# 预置账户类型
ACCOUNT_TYPES = ["cash", "card", "alipay", "wechat", "other"]


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
    account_id: int = 1  # 关联账户 ID，默认第一个账户
    currency_id: int = 1  # 币种 ID，默认人民币

    def __repr__(self) -> str:
        """返回交易记录的可读字符串表示。"""
        return (
            f"Transaction(transaction_id={self.transaction_id}, user_id={self.user_id}, "
            f"date='{self.date}', amount={self.amount}, category_id={self.category_id}, "
            f"type='{self.type}', note='{self.note}', account_id={self.account_id}, "
            f"currency_id={self.currency_id})"
        )

    def to_dict(self) -> Dict[str, Any]:
        """将交易对象序列化为字典。"""
        return asdict(self)
