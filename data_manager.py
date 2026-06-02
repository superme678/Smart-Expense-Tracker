"""数据管理模块：内存数据结构 + SQLite 数据库持久化。"""

import os
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from models import (
    DEFAULT_CATEGORIES,
    DEFAULT_CURRENCIES,
    Account,
    Category,
    Currency,
    Transaction,
    User,
)

# 数据库文件路径
DB_PATH = "expense_tracker.db"

# 加分项1：异常消费检测阈值（超过历史均值的倍数即标记为异常）
THRESHOLD = 1.5

# 默认人民币币种 ID
DEFAULT_CURRENCY_ID = 1


class DataManager:
    """数据管理器：维护会话内存数据并提供数据库 CRUD 操作。"""

    def __init__(self, db_path: str = DB_PATH) -> None:
        """
        初始化数据管理器。

        :param db_path: SQLite 数据库文件路径
        """
        self.db_path = db_path
        # 使用列表存储当前会话中的 Transaction 对象
        self.transactions: List[Transaction] = []
        # 使用字典构建索引，按 category_id 和 date 快速查找
        self._index_by_category: Dict[int, List[Transaction]] = {}
        self._index_by_date: Dict[str, List[Transaction]] = {}
        self.categories: Dict[int, Category] = {}
        self.currencies: Dict[int, Currency] = {}
        self.accounts: Dict[int, Account] = {}
        self.current_user: Optional[User] = None
        self.conn: Optional[sqlite3.Connection] = None

        self.init_db()
        self._load_categories()
        self._load_currencies()
        self._ensure_default_user()
        self._ensure_default_account()
        self.reload_from_db()

    def init_db(self) -> None:
        """初始化数据库表结构，程序启动时自动建表。"""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        cursor = self.conn.cursor()

        # 创建用户表
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )

        # 创建分类表
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS categories (
                category_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                type TEXT NOT NULL CHECK(type IN ('income', 'expense'))
            )
            """
        )

        # 创建币种表
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS currencies (
                currency_id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT NOT NULL UNIQUE,
                name TEXT NOT NULL,
                symbol TEXT NOT NULL,
                rate_to_cny REAL NOT NULL DEFAULT 1.0
            )
            """
        )

        # 创建账户表
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS accounts (
                account_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                type TEXT NOT NULL,
                balance REAL NOT NULL DEFAULT 0.0,
                currency_id INTEGER NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(user_id),
                FOREIGN KEY (currency_id) REFERENCES currencies(currency_id)
            )
            """
        )

        # 创建交易记录表
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS transactions (
                transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                date TEXT NOT NULL,
                amount REAL NOT NULL,
                category_id INTEGER NOT NULL,
                type TEXT NOT NULL CHECK(type IN ('income', 'expense')),
                note TEXT DEFAULT '',
                account_id INTEGER NOT NULL DEFAULT 1,
                currency_id INTEGER NOT NULL DEFAULT 1,
                FOREIGN KEY (user_id) REFERENCES users(user_id),
                FOREIGN KEY (category_id) REFERENCES categories(category_id),
                FOREIGN KEY (account_id) REFERENCES accounts(account_id),
                FOREIGN KEY (currency_id) REFERENCES currencies(currency_id)
            )
            """
        )
        self.conn.commit()

        # 预置常用分类
        cursor.execute("SELECT COUNT(*) FROM categories")
        if cursor.fetchone()[0] == 0:
            for name, cat_type in DEFAULT_CATEGORIES:
                cursor.execute(
                    "INSERT INTO categories (name, type) VALUES (?, ?)",
                    (name, cat_type),
                )
            self.conn.commit()

        # 预置常用币种
        cursor.execute("SELECT COUNT(*) FROM currencies")
        if cursor.fetchone()[0] == 0:
            for code, name, symbol, rate in DEFAULT_CURRENCIES:
                cursor.execute(
                    "INSERT INTO currencies (code, name, symbol, rate_to_cny) VALUES (?, ?, ?, ?)",
                    (code, name, symbol, rate),
                )
            self.conn.commit()

    def _ensure_default_user(self) -> None:
        """确保存在默认用户，供首次使用时记账。"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT user_id, username, created_at FROM users LIMIT 1")
        row = cursor.fetchone()
        if row:
            self.current_user = User(
                user_id=row["user_id"],
                username=row["username"],
                created_at=row["created_at"],
            )
        else:
            created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute(
                "INSERT INTO users (username, created_at) VALUES (?, ?)",
                ("默认用户", created_at),
            )
            self.conn.commit()
            self.current_user = User(
                user_id=cursor.lastrowid,
                username="默认用户",
                created_at=created_at,
            )

    def _ensure_default_account(self) -> None:
        """确保存在默认账户，供首次使用时记账。"""
        if self.current_user is None:
            return
        cursor = self.conn.cursor()
        cursor.execute("SELECT account_id FROM accounts WHERE user_id = ? LIMIT 1", (self.current_user.user_id,))
        row = cursor.fetchone()
        if not row:
            cursor.execute(
                "INSERT INTO accounts (user_id, name, type, balance, currency_id) VALUES (?, ?, ?, ?, ?)",
                (self.current_user.user_id, "默认账户", "cash", 0.0, DEFAULT_CURRENCY_ID),
            )
            self.conn.commit()
            self._load_accounts()

    def _load_categories(self) -> None:
        """从数据库加载分类到内存字典。"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT category_id, name, type FROM categories")
        self.categories = {}
        for row in cursor.fetchall():
            category = Category(
                category_id=row["category_id"],
                name=row["name"],
                type=row["type"],
            )
            self.categories[category.category_id] = category

    def _load_currencies(self) -> None:
        """从数据库加载币种到内存字典。"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT currency_id, code, name, symbol, rate_to_cny FROM currencies")
        self.currencies = {}
        for row in cursor.fetchall():
            currency = Currency(
                currency_id=row["currency_id"],
                code=row["code"],
                name=row["name"],
                symbol=row["symbol"],
                rate_to_cny=row["rate_to_cny"],
            )
            self.currencies[currency.currency_id] = currency

    def _load_accounts(self) -> None:
        """从数据库加载账户到内存字典。"""
        if self.current_user is None:
            return
        cursor = self.conn.cursor()
        cursor.execute("SELECT account_id, user_id, name, type, balance, currency_id FROM accounts WHERE user_id = ?", (self.current_user.user_id,))
        self.accounts = {}
        for row in cursor.fetchall():
            account = Account(
                account_id=row["account_id"],
                user_id=row["user_id"],
                name=row["name"],
                type=row["type"],
                balance=row["balance"],
                currency_id=row["currency_id"],
            )
            self.accounts[account.account_id] = account

    def _rebuild_indexes(self) -> None:
        """根据当前交易列表重建索引字典。"""
        self._index_by_category = {}
        self._index_by_date = {}
        for txn in self.transactions:
            # 按 category_id 索引
            self._index_by_category.setdefault(txn.category_id, []).append(txn)
            # 按 date 索引
            self._index_by_date.setdefault(txn.date, []).append(txn)

    def reload_from_db(self) -> None:
        """从数据库重新加载所有交易到内存列表。"""
        self.transactions = self.get_all_transactions()
        self._rebuild_indexes()

    def _row_to_transaction(self, row: sqlite3.Row) -> Transaction:
        """将数据库行转换为 Transaction 对象。"""
        return Transaction(
            transaction_id=row["transaction_id"],
            user_id=row["user_id"],
            date=row["date"],
            amount=row["amount"],
            category_id=row["category_id"],
            type=row["type"],
            note=row["note"] or "",
            account_id=row["account_id"] if "account_id" in row.keys() else 1,
            currency_id=row["currency_id"] if "currency_id" in row.keys() else 1,
        )

    def save_transaction(self, transaction: Transaction) -> Transaction:
        """
        插入一条交易记录到数据库并同步到内存。

        :param transaction: 交易对象（transaction_id 可为 0 表示新增）
        :return: 带有新 ID 的交易对象
        """
        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT INTO transactions (user_id, date, amount, category_id, type, note, account_id, currency_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                transaction.user_id,
                transaction.date,
                transaction.amount,
                transaction.category_id,
                transaction.type,
                transaction.note,
                transaction.account_id,
                transaction.currency_id,
            ),
        )
        self.conn.commit()
        transaction.transaction_id = cursor.lastrowid
        self.transactions.append(transaction)
        self._rebuild_indexes()
        self._update_account_balance(transaction)
        return transaction

    def get_all_transactions(self) -> List[Transaction]:
        """查询所有交易记录。"""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM transactions ORDER BY date DESC, transaction_id DESC"
        )
        return [self._row_to_transaction(row) for row in cursor.fetchall()]

    def get_transactions_by_month(self, year_month: str) -> List[Transaction]:
        """
        按年月查询交易记录。

        :param year_month: 年月字符串，格式 YYYY-MM
        :return: 该月的交易记录列表
        """
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM transactions WHERE date LIKE ? ORDER BY date",
            (f"{year_month}-%",),
        )
        return [self._row_to_transaction(row) for row in cursor.fetchall()]

    def get_transaction_by_id(self, transaction_id: int) -> Optional[Transaction]:
        """根据 ID 查询单条交易记录。"""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM transactions WHERE transaction_id = ?",
            (transaction_id,),
        )
        row = cursor.fetchone()
        if row:
            return self._row_to_transaction(row)
        return None

    def update_transaction(self, transaction: Transaction) -> bool:
        """
        更新一条交易记录。

        :param transaction: 包含更新后数据的交易对象
        :return: 是否更新成功
        """
        cursor = self.conn.cursor()
        cursor.execute(
            """
            UPDATE transactions
            SET user_id=?, date=?, amount=?, category_id=?, type=?, note=?, account_id=?, currency_id=?
            WHERE transaction_id=?
            """,
            (
                transaction.user_id,
                transaction.date,
                transaction.amount,
                transaction.category_id,
                transaction.type,
                transaction.note,
                transaction.account_id,
                transaction.currency_id,
                transaction.transaction_id,
            ),
        )
        self.conn.commit()
        if cursor.rowcount > 0:
            self.reload_from_db()
            return True
        return False

    def delete_transaction(self, transaction_id: int) -> bool:
        """
        删除一条交易记录。

        :param transaction_id: 交易 ID
        :return: 是否删除成功
        """
        cursor = self.conn.cursor()
        cursor.execute(
            "DELETE FROM transactions WHERE transaction_id = ?",
            (transaction_id,),
        )
        self.conn.commit()
        if cursor.rowcount > 0:
            self.reload_from_db()
            return True
        return False

    def add_transaction(
        self,
        date: str,
        amount: float,
        category_id: int,
        txn_type: str,
        note: str = "",
        account_id: int = 1,
        currency_id: int = 1,
    ) -> Transaction:
        """
        新增一条收支记录（增）。

        :param date: 日期
        :param amount: 金额
        :param category_id: 分类ID
        :param txn_type: 类型（income/expense）
        :param note: 备注
        :param account_id: 账户ID
        :param currency_id: 币种ID
        :return: 新建的交易对象
        """
        if self.current_user is None:
            raise ValueError("当前无有效用户")
        transaction = Transaction(
            transaction_id=0,
            user_id=self.current_user.user_id,
            date=date,
            amount=amount,
            category_id=category_id,
            type=txn_type,
            note=note,
            account_id=account_id,
            currency_id=currency_id,
        )
        return self.save_transaction(transaction)

    def find_by_category(self, category_id: int) -> List[Transaction]:
        """通过索引按分类查找交易记录（查）。"""
        return self._index_by_category.get(category_id, [])

    def find_by_date(self, date: str) -> List[Transaction]:
        """通过索引按日期查找交易记录（查）。"""
        return self._index_by_date.get(date, [])

    def get_category_stats(
        self, txn_type: Optional[str] = None
    ) -> List[Tuple[str, float, int]]:
        """
        按分类统计交易，使用元组返回固定格式结果。

        :param txn_type: 可选，筛选 income 或 expense
        :return: (category_name, total_amount, count) 元组列表
        """
        stats: Dict[int, Tuple[str, float, int]] = {}
        for txn in self.transactions:
            if txn_type and txn.type != txn_type:
                continue
            category = self.categories.get(txn.category_id)
            if not category:
                continue
            if txn.category_id not in stats:
                stats[txn.category_id] = (category.name, 0.0, 0)
            name, total, count = stats[txn.category_id]
            stats[txn.category_id] = (name, total + txn.amount, count + 1)

        return list(stats.values())

    def get_categories_by_type(self, txn_type: str) -> List[Category]:
        """获取指定类型的所有分类。"""
        return [cat for cat in self.categories.values() if cat.type == txn_type]

    def get_monthly_summary(self) -> Dict[str, Dict[str, float]]:
        """
        获取各月份的收入与支出汇总，供折线图使用。

        :return: { "YYYY-MM": {"income": x, "expense": y}, ... }
        """
        summary: Dict[str, Dict[str, float]] = {}
        for txn in self.transactions:
            year_month = txn.date[:7]
            if year_month not in summary:
                summary[year_month] = {"income": 0.0, "expense": 0.0}
            summary[year_month][txn.type] += txn.amount
        return summary

    def _get_expense_history_amounts(
        self, user_id: int, category_id: int, exclude_transaction_id: int = 0
    ) -> List[float]:
        """
        查询用户某分类的历史支出金额列表（不含指定记录）。

        :param exclude_transaction_id: 排除的交易 ID，0 表示不排除
        """
        cursor = self.conn.cursor()
        if exclude_transaction_id:
            cursor.execute(
                """
                SELECT amount FROM transactions
                WHERE user_id=? AND category_id=? AND type='expense'
                  AND transaction_id != ?
                """,
                (user_id, category_id, exclude_transaction_id),
            )
        else:
            cursor.execute(
                """
                SELECT amount FROM transactions
                WHERE user_id=? AND category_id=? AND type='expense'
                """,
                (user_id, category_id),
            )
        return [float(row[0]) for row in cursor.fetchall()]

    def get_category_avg(
        self, user_id: int, category_id: int, exclude_transaction_id: int = 0
    ) -> float:
        """
        获取用户某分类历史支出的算术平均值（用于 GUI 弹窗提示）。

        :return: 历史均值；记录不足 2 条时返回 0.0
        """
        try:
            amounts = self._get_expense_history_amounts(
                user_id, category_id, exclude_transaction_id
            )
            if len(amounts) < 2:
                return 0.0
            return sum(amounts) / len(amounts)
        except Exception:
            return 0.0

    def check_anomaly(self, transaction: Transaction) -> bool:
        """
        加分项1：基于历史均值自动标记异常消费。

        仅检测支出；若该用户该分类历史支出不足 2 条则返回 False；
        当金额超过历史均值 * THRESHOLD 时判定为异常。
        """
        if transaction.type != "expense":
            return False

        try:
            history = self._get_expense_history_amounts(
                transaction.user_id,
                transaction.category_id,
                transaction.transaction_id,
            )
            if len(history) < 2:
                return False
            avg = sum(history) / len(history)
            return transaction.amount > avg * THRESHOLD
        except Exception:
            return False

    def _update_account_balance(self, transaction: Transaction) -> None:
        """
        根据交易更新账户余额。

        :param transaction: 交易对象
        """
        if transaction.account_id not in self.accounts:
            return

        account = self.accounts[transaction.account_id]
        currency = self.currencies.get(transaction.currency_id)
        if not currency:
            return

        amount_in_account_currency = self.convert_currency(
            transaction.amount,
            transaction.currency_id,
            account.currency_id
        )

        if transaction.type == "income":
            account.balance += amount_in_account_currency
        else:
            account.balance -= amount_in_account_currency

        cursor = self.conn.cursor()
        cursor.execute(
            "UPDATE accounts SET balance = ? WHERE account_id = ?",
            (account.balance, account.account_id),
        )
        self.conn.commit()

    def convert_currency(self, amount: float, from_currency_id: int, to_currency_id: int) -> float:
        """
        加分项2：汇率转换功能。

        将金额从一种货币转换为另一种货币。

        :param amount: 原始金额
        :param from_currency_id: 源币种ID
        :param to_currency_id: 目标币种ID
        :return: 转换后的金额
        """
        if from_currency_id == to_currency_id:
            return amount

        from_currency = self.currencies.get(from_currency_id)
        to_currency = self.currencies.get(to_currency_id)

        if not from_currency or not to_currency:
            return amount

        amount_in_cny = amount * from_currency.rate_to_cny
        amount_in_target = amount_in_cny / to_currency.rate_to_cny

        return round(amount_in_target, 2)

    def add_account(self, name: str, account_type: str, currency_id: int = 1, balance: float = 0.0) -> Account:
        """
        加分项2：添加新账户。

        :param name: 账户名称
        :param account_type: 账户类型
        :param currency_id: 币种ID
        :param balance: 初始余额
        :return: 新建的账户对象
        """
        if self.current_user is None:
            raise ValueError("当前无有效用户")

        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO accounts (user_id, name, type, balance, currency_id) VALUES (?, ?, ?, ?, ?)",
            (self.current_user.user_id, name, account_type, balance, currency_id),
        )
        self.conn.commit()

        account = Account(
            account_id=cursor.lastrowid,
            user_id=self.current_user.user_id,
            name=name,
            type=account_type,
            balance=balance,
            currency_id=currency_id,
        )
        self.accounts[account.account_id] = account
        return account

    def get_accounts(self) -> List[Account]:
        """获取当前用户的所有账户。"""
        return list(self.accounts.values())

    def update_currency_rate(self, currency_id: int, new_rate: float) -> bool:
        """
        加分项2：更新币种汇率。

        :param currency_id: 币种ID
        :param new_rate: 新的汇率（相对于人民币）
        :return: 是否更新成功
        """
        if currency_id not in self.currencies:
            return False

        cursor = self.conn.cursor()
        cursor.execute(
            "UPDATE currencies SET rate_to_cny = ? WHERE currency_id = ?",
            (new_rate, currency_id),
        )
        self.conn.commit()

        if cursor.rowcount > 0:
            self.currencies[currency_id].rate_to_cny = new_rate
            return True
        return False

    def get_total_balance_in_cny(self) -> float:
        """
        加分项2：计算用户所有账户的总余额（换算成人民币）。

        :return: 总余额（人民币）
        """
        total = 0.0
        for account in self.accounts.values():
            currency = self.currencies.get(account.currency_id)
            if currency:
                total += account.balance * currency.rate_to_cny
        return round(total, 2)

    def search_transactions(
        self,
        keyword: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        txn_type: Optional[str] = None,
        category_id: Optional[int] = None,
        min_amount: Optional[float] = None,
        max_amount: Optional[float] = None,
    ) -> List[Transaction]:
        """
        高级搜索：根据多条件查询交易记录。

        :param keyword: 关键词搜索（备注中包含）
        :param start_date: 开始日期（YYYY-MM-DD）
        :param end_date: 结束日期（YYYY-MM-DD）
        :param txn_type: 交易类型（income/expense）
        :param category_id: 分类ID
        :param min_amount: 最小金额
        :param max_amount: 最大金额
        :return: 匹配的交易记录列表
        """
        results = list(self.transactions)

        if self.current_user is not None:
            results = [t for t in results if t.user_id == self.current_user.user_id]

        if keyword:
            keyword_lower = keyword.lower()
            results = [
                t for t in results
                if keyword_lower in t.note.lower()
            ]

        if start_date:
            results = [t for t in results if t.date >= start_date]

        if end_date:
            results = [t for t in results if t.date <= end_date]

        if txn_type:
            results = [t for t in results if t.type == txn_type]

        if category_id is not None:
            results = [t for t in results if t.category_id == category_id]

        if min_amount is not None:
            results = [t for t in results if t.amount >= min_amount]

        if max_amount is not None:
            results = [t for t in results if t.amount <= max_amount]

        return results

    def backup_database(self, backup_path: Optional[str] = None) -> str:
        """
        备份数据库文件。

        :param backup_path: 备份文件路径，默认为 expense_tracker_YYYYMMDD_HHMMSS.db
        :return: 备份文件的完整路径
        """
        import shutil

        if not os.path.exists(DB_PATH):
            raise FileNotFoundError("数据库文件不存在，无法备份。")

        if backup_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = f"expense_tracker_backup_{timestamp}.db"

        shutil.copy2(DB_PATH, backup_path)
        return os.path.abspath(backup_path)

    def restore_database(self, backup_path: str) -> bool:
        """
        从备份文件恢复数据库。

        :param backup_path: 备份文件路径
        :return: 是否恢复成功
        """
        import shutil

        if not os.path.exists(backup_path):
            raise FileNotFoundError(f"备份文件不存在：{backup_path}")

        if self.conn:
            self.close()

        shutil.copy2(backup_path, DB_PATH)

        self.conn = sqlite3.connect(DB_PATH)
        self._load_all_data()

        return True

    def close(self) -> None:
        """关闭数据库连接。"""
        if self.conn:
            self.conn.close()
            self.conn = None
