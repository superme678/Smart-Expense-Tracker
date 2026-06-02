"""自然语言记账解析模块：解析用户的自然语言输入，提取日期、金额、分类等信息。"""

import re
from datetime import datetime, timedelta
from typing import Optional, Tuple, Dict


class NaturalParser:
    """自然语言解析器：将自然语言描述转换为记账数据。"""

    def __init__(self):
        """初始化解析器，定义关键词映射。"""
        self._category_keywords = {
            "餐饮": ["吃饭", "午餐", "午饭", "晚饭", "晚餐", "早餐", "早饭",
                    "外卖", "奶茶", "咖啡", "零食", "水果", "饮料", "餐",
                    "火锅", "烧烤", "聚餐", "点心", "面包", "蛋糕"],
            "交通": ["地铁", "公交", "打车", "滴滴", "出租", "加油", "停车",
                    "高铁", "火车", "机票", "机票", "车票", "高速", "过路费"],
            "购物": ["买", "购物", "超市", "淘宝", "京东", "拼多多", "衣服",
                    "鞋子", "化妆品", "日用品", "家电", "数码", "手机", "电脑"],
            "娱乐": ["电影", "游戏", "KTV", "旅游", "门票", "演出", "音乐会",
                    "酒吧", "桌游", "剧本杀", "密室"],
            "工资": ["工资", "薪水", "月薪", "发薪", "工资到账"],
            "奖金": ["奖金", "绩效", "年终奖", "提成", "红包"],
        }

        self._income_keywords = ["收入", "收到", "转入", "工资", "奖金", "红包", "转账"]
        self._expense_keywords = ["花", "买", "支付", "消费", "支出", "花费", "用了", "付了"]

    def parse(self, input_text: str) -> Optional[Dict[str, str]]:
        """
        解析自然语言输入，提取记账信息。

        :param input_text: 用户输入的自然语言文本
        :return: 包含日期、金额、分类、类型的字典，解析失败返回 None
        """
        result = {}

        date = self._parse_date(input_text)
        if not date:
            date = datetime.now().strftime("%Y-%m-%d")
        result["date"] = date

        amount = self._parse_amount(input_text)
        if not amount:
            return None
        result["amount"] = amount

        txn_type = self._parse_type(input_text)
        result["type"] = txn_type

        category = self._parse_category(input_text, txn_type)
        if not category:
            category = "其他收入" if txn_type == "income" else "其他支出"
        result["category"] = category

        note = self._extract_note(input_text)
        if note:
            result["note"] = note

        return result

    def _parse_date(self, text: str) -> Optional[str]:
        """
        解析日期信息。

        支持的格式：
        - 昨天、前天、今天、明天、后天
        - X天前、X天后
        - YYYY-MM-DD
        - MM-DD（默认当年）

        :param text: 输入文本
        :return: 格式化的日期字符串 YYYY-MM-DD
        """
        today = datetime.now()
        text = text.strip()

        if "昨天" in text:
            return (today - timedelta(days=1)).strftime("%Y-%m-%d")
        elif "前天" in text:
            return (today - timedelta(days=2)).strftime("%Y-%m-%d")
        elif "今天" in text or "今日" in text:
            return today.strftime("%Y-%m-%d")
        elif "明天" in text:
            return (today + timedelta(days=1)).strftime("%Y-%m-%d")
        elif "后天" in text:
            return (today + timedelta(days=2)).strftime("%Y-%m-%d")

        days_ago_match = re.search(r"(\d+)天前", text)
        if days_ago_match:
            days = int(days_ago_match.group(1))
            return (today - timedelta(days=days)).strftime("%Y-%m-%d")

        days_later_match = re.search(r"(\d+)天后", text)
        if days_later_match:
            days = int(days_later_match.group(1))
            return (today + timedelta(days=days)).strftime("%Y-%m-%d")

        full_date_match = re.search(r"(\d{4})[-/年](\d{1,2})[-/月](\d{1,2})[日号]?", text)
        if full_date_match:
            year, month, day = full_date_match.groups()
            return f"{year}-{int(month):02d}-{int(day):02d}"

        short_date_match = re.search(r"(\d{1,2})[-/月](\d{1,2})[日号]?", text)
        if short_date_match:
            month, day = short_date_match.groups()
            return f"{today.year}-{int(month):02d}-{int(day):02d}"

        return None

    def _parse_amount(self, text: str) -> Optional[str]:
        """
        解析金额信息。

        支持的格式：
        - 数字 + 元，如 35元、100元
        - 纯数字，如 35、100.5
        - 数字 + 块，如 35块

        :param text: 输入文本
        :return: 金额字符串
        """
        text_without_dates = re.sub(r"\d{4}[-/年]\d{1,2}[-/月]\d{1,2}[日号]?", "", text)
        text_without_dates = re.sub(r"\d{1,2}[-/月]\d{1,2}[日号]?", "", text_without_dates)
        text_without_dates = re.sub(r"(\d+)\s*天前", "", text_without_dates)
        text_without_dates = re.sub(r"(\d+)\s*天后", "", text_without_dates)

        amount_patterns = [
            r"(\d+(?:\.\d{1,2})?)\s*元",
            r"(\d+(?:\.\d{1,2})?)\s*块",
            r"(\d+(?:\.\d{1,2})?)\s*钱",
            r"(\d+(?:\.\d{1,2}))",
            r"(?<!\d)(\d{2,})(?!\d)",
        ]

        for pattern in amount_patterns:
            matches = re.findall(pattern, text_without_dates)
            if matches:
                return matches[-1]

        matches = re.findall(r"\d+(?:\.\d{1,2})?", text_without_dates)
        if matches:
            return matches[-1]

        return None

    def _parse_type(self, text: str) -> str:
        """
        解析交易类型（收入/支出）。

        :param text: 输入文本
        :return: "income" 或 "expense"
        """
        text_lower = text.lower()

        income_count = sum(1 for kw in self._income_keywords if kw in text_lower)
        expense_count = sum(1 for kw in self._expense_keywords if kw in text_lower)

        if income_count > expense_count:
            return "income"
        return "expense"

    def _parse_category(self, text: str, txn_type: str) -> Optional[str]:
        """
        根据交易类型解析分类。

        :param text: 输入文本
        :param txn_type: 交易类型（income/expense）
        :return: 分类名称
        """
        text_lower = text.lower()

        if txn_type == "income":
            target_categories = ["工资", "奖金"]
        else:
            target_categories = ["餐饮", "交通", "购物", "娱乐"]

        for category in target_categories:
            for keyword in self._category_keywords.get(category, []):
                if keyword in text_lower:
                    return category

        return None

    def _extract_note(self, text: str) -> Optional[str]:
        """
        提取备注信息（去除已解析的内容）。

        :param text: 输入文本
        :return: 备注字符串
        """
        cleaned = text

        cleaned = re.sub(r"\d+(?:\.\d{1,2})?\s*(元|块|钱)?", "", cleaned)
        cleaned = re.sub(r"(昨天|前天|今天|明天|后天|\d+天前|\d+天后)", "", cleaned)
        cleaned = re.sub(r"\d{4}[-/年]\d{1,2}[-/月]\d{1,2}[日号]?", "", cleaned)
        cleaned = re.sub(r"\d{1,2}[-/月]\d{1,2}[日号]?", "", cleaned)

        for kw in ["收入", "支出", "花了", "买了", "收到", "发了"]:
            cleaned = cleaned.replace(kw, "")

        cleaned = cleaned.strip()
        return cleaned if cleaned else None


if __name__ == "__main__":
    parser = NaturalParser()

    test_cases = [
        "昨天午饭花了35",
        "今天打车15元",
        "前天网购衣服299",
        "明天发工资8000",
        "3天前吃饭花了100",
        "收到红包500",
        "2024-01-15 买手机5999",
        "5天后旅游预算2000",
        "昨晚聚餐AA花了88",
    ]

    for test in test_cases:
        result = parser.parse(test)
        print(f"输入: {test}")
        print(f"解析结果: {result}")
        print("-" * 40)