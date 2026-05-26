"""数据管理模块：内存数据结构 + SQLite 数据库持久化。"""

import os
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from models import DEFAULT_CATEGORIES, Category, Transaction, User

# 数据库文件路径
DB_PATH = "expense_tracker.db"


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
        self.current_user: Optional[User] = None
        self.conn: Optional[sqlite3.Connection] = None

        self.init_db()
        self._load_categories()
        self._ensure_default_user()
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
                FOREIGN KEY (user_id) REFERENCES users(user_id),
                FOREIGN KEY (category_id) REFERENCES categories(category_id)
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
            INSERT INTO transactions (user_id, date, amount, category_id, type, note)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                transaction.user_id,
                transaction.date,
                transaction.amount,
                transaction.category_id,
                transaction.type,
                transaction.note,
            ),
        )
        self.conn.commit()
        transaction.transaction_id = cursor.lastrowid
        self.transactions.append(transaction)
        self._rebuild_indexes()
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
            SET user_id=?, date=?, amount=?, category_id=?, type=?, note=?
            WHERE transaction_id=?
            """,
            (
                transaction.user_id,
                transaction.date,
                transaction.amount,
                transaction.category_id,
                transaction.type,
                transaction.note,
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
    ) -> Transaction:
        """
        新增一条收支记录（增）。

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

    def close(self) -> None:
        """关闭数据库连接。"""
        if self.conn:
            self.conn.close()
            self.conn = None
