# 智能个人记账助手（Smart Expense Tracker）

《Python 程序设计》课程大作业 —— 项目 1：基于命令行的个人收支管理系统。

## 项目介绍

本项目实现了一个功能完整的智能个人记账助手，支持记账、查询、统计、图表可视化以及数据导入导出。采用面向对象设计，结合 SQLite 数据库实现数据持久化，适合作为 Python 课程综合实践项目。

## 安装方式

1. 确保已安装 Python 3.10 或以上版本。
2. 安装依赖：

```bash
pip install -r requirements.txt
```

或直接安装：

```bash
pip install matplotlib
```

## 运行方式

在项目根目录下执行：

```bash
python main.py
```

首次运行将自动创建 `expense_tracker.db` 数据库并预置常用分类。

## 功能说明（对应 7 个基础得分项）

| 序号 | 得分项 | 实现位置 | 说明 |
|------|--------|----------|------|
| 1 | OOP 设计 | `models.py` | `User`、`Category`、`Transaction` 三个类，含 `__repr__` 和 `to_dict()` |
| 2 | 数据结构管理 | `data_manager.py` | 列表存交易、字典建索引、元组返回统计结果，提供增删改查 |
| 3 | 菜单交互 | `main.py` | `while True` 主循环 + `if/elif/else` 分支，7 个菜单选项 |
| 4 | 正则校验 | `validator.py` | 校验日期、金额、类型格式，失败抛出 `ValueError` |
| 5 | 文件读写 | `file_handler.py` | JSON/CSV 导入导出，菜单选项 5、6 可直接调用 |
| 6 | SQLite 存储 | `data_manager.py` | 自动建表，增删改查后自动提交 |
| 7 | 图表可视化 | `visualizer.py` | 月度支出饼图 + 收支趋势折线图，菜单选项 4 调用 |

## 菜单功能

1. **记一笔** — 录入收入或支出
2. **查看所有记录** — 列出全部交易
3. **按分类统计** — 按分类汇总金额与笔数
4. **生成月度报表** — 饼图（指定月支出占比）+ 折线图（最近 6 个月趋势）
5. **导出数据** — 支持 JSON / CSV
6. **导入数据** — 支持 JSON / CSV
7. **退出**

## 文件结构

```
python_work/
├── main.py              # 主程序入口，命令行菜单
├── models.py            # 数据模型（User, Category, Transaction）
├── data_manager.py      # 内存数据结构 + SQLite 数据库操作
├── validator.py         # 正则表达式输入校验
├── file_handler.py      # JSON/CSV 文件导入导出
├── visualizer.py        # matplotlib 图表生成
├── requirements.txt     # 项目依赖
├── README.md            # 项目说明文档
└── expense_tracker.db   # SQLite 数据库（首次运行后自动生成）
```

## 预置分类

- **支出**：餐饮、交通、购物、娱乐、其他支出
- **收入**：工资、奖金、其他收入

## 技术栈

- Python 3.10+
- 标准库：sqlite3, json, csv, re, datetime, os
- 第三方库：matplotlib（图表绘制）
