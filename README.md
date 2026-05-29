# 智能个人记账助手（Smart Expense Tracker）

《Python 程序设计》课程大作业 —— 项目 1

---

## 1. 项目简介

### 背景

个人财务管理是日常生活中高频且刚需的场景。传统纸质记账或 Excel 表格方式存在录入繁琐、统计困难、数据易丢失等问题。本项目基于 Python 标准库与 SQLite，实现一套轻量级、可离线运行的个人收支管理系统，覆盖记账、查询、统计、图表分析与数据导入导出等完整流程，并支持命令行（CLI）与图形界面（GUI）两种交互方式。

### 应用场景

| 场景 | 说明 |
|------|------|
| 日常记账 | 记录餐饮、交通、工资等收入/支出明细 |
| 消费复盘 | 按分类汇总金额与笔数，了解消费结构 |
| 月度分析 | 生成支出饼图与收支趋势折线图，直观把握财务状况 |
| 异常提醒 | 基于历史均值自动标记异常大额支出（加分项） |
| 数据备份 | 支持 JSON/CSV 导出与导入，便于迁移与备份 |
| 课程演示 | 展示 OOP、数据结构、正则校验、文件 I/O、SQLite、matplotlib、tkinter 等综合技能 |

---

## 2. 功能特性

| 类别 | 序号 | 功能项 | 分值 | 说明 |
|------|------|--------|------|------|
| **基础** | 1 | OOP 设计 | 10 分 | `User` / `Category` / `Transaction` 三个类，含 `__repr__()` 与 `to_dict()` |
| **基础** | 2 | 数据结构管理 | 10 分 | 列表存交易、字典建索引、元组返回统计结果，增删改查 |
| **基础** | 3 | 菜单交互系统 | 10 分 | CLI：`while True` 循环；GUI：`mainloop()` 事件循环 + Button/Combobox/Radiobutton |
| **基础** | 4 | 正则表达式校验 | 10 分 | 日期 `YYYY-MM-DD`、金额正数两位小数、类型 income/expense |
| **基础** | 5 | 文件读写持久化 | 10 分 | JSON / CSV 导入导出 |
| **基础** | 6 | SQLite 数据库存储 | 10 分 | 自动建表，增删改查后自动提交 |
| **基础** | 7 | matplotlib 图表 | 10 分 | 月度支出饼图 + 近 6 个月收支趋势折线图 |
| **加分** | ★1 | 消费异常检测 | +10 分 | 支出超过同分类历史均值 × 1.5 倍时自动标红并弹窗提醒 |

**预置分类：**

- 支出：餐饮、交通、购物、娱乐、其他支出
- 收入：工资、奖金、其他收入

---

## 3. 技术架构

### MVC 分层设计

```
┌─────────────────────────────────────────────────────────┐
│  View（视图层）                                          │
│  main.py（CLI 命令行菜单）  gui.py（tkinter 图形界面）    │
└──────────────────────────┬──────────────────────────────┘
                           │ 用户输入 / 事件回调
┌──────────────────────────▼──────────────────────────────┐
│  Controller（控制层）                                     │
│  main.py 菜单分支  gui.py ExpenseTrackerGUI 事件处理     │
│  validator.py 输入校验                                   │
└──────────────────────────┬──────────────────────────────┘
                           │ 调用业务方法
┌──────────────────────────▼──────────────────────────────┐
│  Model（模型层）                                          │
│  models.py（User / Category / Transaction）              │
│  data_manager.py（内存数据结构 + SQLite CRUD）             │
│  file_handler.py（JSON/CSV 序列化）                        │
│  visualizer.py（matplotlib 图表）                        │
└──────────────────────────┬──────────────────────────────┘
                           │ 读写
┌──────────────────────────▼──────────────────────────────┐
│  持久化层                                                 │
│  expense_tracker.db（SQLite）  *.json / *.csv（文件）     │
└─────────────────────────────────────────────────────────┘
```

### 数据流示意

```
用户输入（日期/金额/分类）
    │
    ▼
validator.validate_date() / validate_amount() / validate_type()
    │ 校验通过
    ▼
data_manager.add_transaction()  ──►  save_transaction()  ──►  SQLite INSERT
    │                                    │
    │                                    ▼
    │                              transactions 列表（内存）
    │                              _index_by_category / _index_by_date（字典索引）
    ▼
check_anomaly()（加分项，实时计算，不写库）
    │
    ▼
GUI Treeview 刷新 / CLI 打印列表
```

### 技术栈

| 类型 | 技术 |
|------|------|
| 语言 | Python 3.10+ |
| 标准库 | sqlite3, json, csv, re, datetime, os, tkinter |
| 第三方库 | matplotlib（图表）、colorama（CLI 彩色输出，可选） |

---

## 4. 安装配置

### 环境要求

- 操作系统：Windows / macOS / Linux
- Python：3.10 及以上
- 磁盘：约 50 MB（含虚拟环境与依赖）

### 推荐：使用虚拟环境

```bash
# 进入项目目录
cd python_work

# 创建虚拟环境
python -m venv .venv

# 激活虚拟环境
# Windows PowerShell:
.\.venv\Scripts\Activate.ps1
# Windows CMD:
.\.venv\Scripts\activate.bat
# macOS / Linux:
source .venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 依赖说明（requirements.txt）

```
matplotlib
colorama>=0.4.6
```

- `matplotlib`：绘制饼图与折线图（基础项 7）
- `colorama`：Windows 终端红色异常标记（加分项 ★1，未安装时自动降级为纯文本 `[异常]`）

---

## 5. 使用方式

### 启动命令

| 命令 | 说明 |
|------|------|
| `python main.py` | 默认启动 **GUI** 图形界面 |
| `python main.py --gui` | 启动 GUI |
| `python main.py --cli` | 启动 **CLI** 命令行菜单 |
| `python gui.py` | 直接启动 GUI |

### 首次使用

1. 运行 `python main.py`，程序自动创建 `expense_tracker.db`
2. 自动建表：`users`、`categories`、`transactions`
3. 预置 8 个常用分类（餐饮、交通、工资等）
4. 创建默认用户「默认用户」，可直接开始记账

---

### CLI 命令行操作指南

启动后显示主菜单：

```
========================================
       智能个人记账助手
========================================
1. 记一笔（收入/支出）
2. 查看所有记录
3. 按分类统计
4. 生成月度报表（饼图+折线图）
5. 导出数据（JSON/CSV）
6. 导入数据（JSON/CSV）
7. 退出
========================================
请输入选项（1-7）：
```

#### 选项 1：记一笔

```
请输入类型（income=收入 / expense=支出）：expense

可选支出分类：
  [1] 餐饮
  [2] 交通
  ...
请输入分类编号：1
请输入日期（YYYY-MM-DD）：2024-06-15
请输入金额：35.50
备注（可留空）：午餐

记账成功！Transaction(...)
```

- 类型、日期、金额格式错误时会提示重新输入
- 金额须为正数，最多两位小数

#### 选项 2：查看所有记录

```
ID:5 | 2024-06-15 | 支出 | 餐饮 | ¥350.00 | 聚餐  [🔴 异常]  (该类历史均值: 45.00)
ID:4 | 2024-06-14 | 支出 | 交通 | ¥25.00 | 地铁
```

- 异常消费行尾标注 `[🔴 异常]`（colorama）或 `[异常]`（纯文本）
- 附带该类历史支出均值

#### 选项 3：按分类统计

```
1. 统计支出  2. 统计收入  3. 统计全部
请选择：1

支出分类统计（格式：分类名 | 总额 | 笔数）：
  餐饮 | ¥420.50 | 8 笔
  交通 | ¥150.00 | 6 笔
```

#### 选项 4：生成月度报表

```
请输入要查看的月份（YYYY-MM，用于饼图）：2024-06
```

- 弹出该月支出分类占比 **饼图**
- 随后弹出近 6 个月收支 **折线图**

#### 选项 5 / 6：导出 / 导入

- 导出：选择 JSON 或 CSV，指定文件路径
- 导入：读取 JSON/CSV，写入 SQLite 并合并到当前用户

---

### GUI 图形界面操作指南

主窗口标题：**Smart Expense Tracker**，左侧为功能导航，右侧为内容区。

#### 记一笔

| 控件 | 操作 |
|------|------|
| Radiobutton | 选择「收入」或「支出」 |
| 日期 Entry | 输入 `YYYY-MM-DD`，失焦时自动校验 |
| 分类 Combobox | 下拉选择，随类型自动过滤 |
| 金额 Entry | 输入正数金额，失焦时校验 |
| 备注 Entry | 可选 |
| 保存按钮 | 校验通过后写入 SQLite；若异常则弹窗警告 |

#### 查看记录

- `Treeview` 表格列：ID、日期、类型、分类、金额、备注
- 异常消费行：**红色加粗**显示
- 选中记录后点「删除选中」可删除并刷新

#### 分类统计

- Combobox 选择「全部 / 支出 / 收入」
- 点击「刷新统计」，Treeview 展示 `(分类名, 总额, 笔数)` 元组结果
- 顶部 Label 显示收入/支出总计与笔数

#### 月度报表

- Combobox 选择年月（如 `2024-06`）
- 点击「生成报表」：上方嵌入 **饼图**，下方嵌入 **折线图**（不弹新窗口）
- 「导出图表为 PNG」：保存到指定目录

#### 导出 / 导入数据

- 点击左侧「导出数据」或「导入数据」
- 通过系统文件对话框选择路径与格式（JSON / CSV）

#### 退出

- 点击「退出」，确认后关闭数据库连接并退出程序

---

## 6. 项目结构

```
python_work/
├── main.py                 # 程序入口（CLI / GUI 双模式）
├── gui.py                  # tkinter 图形界面（ExpenseTrackerGUI）
├── models.py               # 数据模型（User, Category, Transaction）
├── data_manager.py         # 业务逻辑 + SQLite + 异常检测
├── validator.py            # 正则表达式输入校验
├── file_handler.py         # JSON / CSV 导入导出
├── visualizer.py           # matplotlib 图表生成
├── requirements.txt        # 项目依赖
├── README.md               # 项目说明文档
├── expense_tracker.db      # SQLite 数据库（首次运行自动生成）
└── .venv/                  # Python 虚拟环境（本地创建，可选）
```

### 文件与评分项对应表

| 文件 | 对应评分项 | 核心内容 |
|------|-----------|----------|
| `models.py` | 基础项 1 | `User`, `Category`, `Transaction` 类 |
| `data_manager.py` | 基础项 2、6；加分项 ★1 | 列表/字典/元组、`init_db()`、CRUD、`check_anomaly()` |
| `main.py` | 基础项 3 | `run_cli()` → `while True` 菜单循环 |
| `gui.py` | 基础项 3（GUI 版） | `ExpenseTrackerGUI` → `mainloop()` 事件循环 |
| `validator.py` | 基础项 4 | `validate_date()`, `validate_amount()`, `validate_type()` |
| `file_handler.py` | 基础项 5 | `export_to_json/csv()`, `import_from_json/csv()` |
| `visualizer.py` | 基础项 7 | `plot_monthly_pie()`, `plot_monthly_trend()`, `get_*_figure()` |

---

## 7. 评分项对应（助教查阅）

> 以下精确到函数/方法名，便于逐项核验。

### 基础项 1：OOP 设计（10 分）

| 类 / 方法 | 文件 | 说明 |
|-----------|------|------|
| `User` | `models.py` | 属性：`user_id`, `username`, `created_at` |
| `User.__repr__()` | `models.py` | 可读字符串表示 |
| `User.to_dict()` | `models.py` | 序列化为字典 |
| `Category` | `models.py` | 属性：`category_id`, `name`, `type` |
| `Category.__repr__()` / `to_dict()` | `models.py` | 同上 |
| `Transaction` | `models.py` | 属性：`transaction_id`, `user_id`, `date`, `amount`, `category_id`, `type`, `note` |
| `Transaction.__repr__()` / `to_dict()` | `models.py` | 同上 |
| `DEFAULT_CATEGORIES` | `models.py` | 预置分类常量 |
| `ExpenseTrackerGUI(tk.Tk)` | `gui.py` | GUI 视图控制器，持有 `DataManager` |

### 基础项 2：数据结构管理（10 分）

| 方法 / 属性 | 文件 | 数据结构 |
|-------------|------|----------|
| `DataManager.transactions` | `data_manager.py` | `list[Transaction]` 存储会话交易 |
| `DataManager._index_by_category` | `data_manager.py` | `dict[int, list]` 按分类索引 |
| `DataManager._index_by_date` | `data_manager.py` | `dict[str, list]` 按日期索引 |
| `DataManager.get_category_stats()` | `data_manager.py` | 返回 `list[tuple[str, float, int]]` |
| `DataManager.add_transaction()` | `data_manager.py` | 增 |
| `DataManager.delete_transaction()` | `data_manager.py` | 删 |
| `DataManager.get_all_transactions()` | `data_manager.py` | 查 |
| `DataManager.update_transaction()` | `data_manager.py` | 改 |
| `DataManager.find_by_category()` | `data_manager.py` | 按分类查 |
| `DataManager.find_by_date()` | `data_manager.py` | 按日期查 |

### 基础项 3：选择与循环实现菜单交互（10 分）

| 方法 | 文件 | 说明 |
|------|------|------|
| `run_cli()` | `main.py` | `while True` 主循环 |
| `print_menu()` | `main.py` | 打印 7 项菜单 |
| `if/elif/else` 分支 | `main.py` | 选项 1–7 分发 |
| `input_with_retry()` | `main.py` | 输入错误循环重试 |
| `run_gui()` / `ExpenseTrackerGUI.mainloop()` | `gui.py` | GUI 事件循环（等价替代 `while True`） |
| `ttk.Button` / `Combobox` / `Radiobutton` | `gui.py` | GUI 分支选择 |
| `tk.Menu` | `gui.py` | 顶部菜单栏 |

### 基础项 4：正则表达式校验（10 分）

| 函数 / 常量 | 文件 | 正则 / 规则 |
|-------------|------|-------------|
| `DATE_PATTERN` | `validator.py` | `^\d{4}-\d{2}-\d{2}$` + 合法日期 |
| `AMOUNT_PATTERN` | `validator.py` | `^\d+(\.\d{1,2})?$`，正数 |
| `TYPE_PATTERN` | `validator.py` | `income` / `expense` |
| `validate_date()` | `validator.py` | 失败抛 `ValueError` |
| `validate_amount()` | `validator.py` | 失败抛 `ValueError` |
| `validate_type()` | `validator.py` | 失败抛 `ValueError` |
| `validate_year_month()` | `validator.py` | `YYYY-MM` 格式 |
| `_validate_date_field()` | `gui.py` | Entry 失焦校验 |
| `_validate_amount_field()` | `gui.py` | Entry 失焦校验 |

### 基础项 5：文件读写持久化（10 分）

| 函数 | 文件 | 说明 |
|------|------|------|
| `export_to_json()` | `file_handler.py` | 导出 JSON |
| `export_to_csv()` | `file_handler.py` | 导出 CSV |
| `import_from_json()` | `file_handler.py` | 导入 JSON → `list[Transaction]` |
| `import_from_csv()` | `file_handler.py` | 导入 CSV → `list[Transaction]` |
| `export_data()` | `main.py` | CLI 菜单选项 5 |
| `import_data()` | `main.py` | CLI 菜单选项 6 |
| `_on_export()` | `gui.py` | GUI + `filedialog.asksaveasfilename` |
| `_on_import()` | `gui.py` | GUI + `filedialog.askopenfilename` |

### 基础项 6：SQLite 数据库存储（10 分）

| 方法 | 文件 | 说明 |
|------|------|------|
| `DataManager.init_db()` | `data_manager.py` | 建表 `users` / `categories` / `transactions` |
| `DataManager.save_transaction()` | `data_manager.py` | INSERT + commit |
| `DataManager.get_all_transactions()` | `data_manager.py` | SELECT 全部 |
| `DataManager.get_transactions_by_month()` | `data_manager.py` | 按 `YYYY-MM` 查询 |
| `DataManager.update_transaction()` | `data_manager.py` | UPDATE + commit |
| `DataManager.delete_transaction()` | `data_manager.py` | DELETE + commit |
| `DataManager.reload_from_db()` | `data_manager.py` | 同步内存列表 |
| `_refresh_records_table()` | `gui.py` | Treeview 展示 `get_all_transactions()` 结果 |

### 基础项 7：matplotlib 图表（10 分）

| 函数 | 文件 | 说明 |
|------|------|------|
| `plot_monthly_pie()` | `visualizer.py` | CLI 弹窗饼图（`plt.pie`） |
| `plot_monthly_trend()` | `visualizer.py` | CLI 弹窗折线图（`plt.plot`） |
| `get_monthly_pie_figure()` | `visualizer.py` | 返回 Figure，供 GUI 嵌入 |
| `get_monthly_trend_figure()` | `visualizer.py` | 返回 Figure，供 GUI 嵌入 |
| `_embed_figure()` | `gui.py` | `FigureCanvasTkAgg` 嵌入窗口 |
| `_render_charts()` | `gui.py` | 月度报表页生成图表 |
| `generate_monthly_report()` | `main.py` | CLI 菜单选项 4 |

### 加分项 ★1：消费异常检测（+10 分）

| 常量 / 方法 | 文件 | 说明 |
|-------------|------|------|
| `THRESHOLD = 1.5` | `data_manager.py` | 异常阈值倍数 |
| `check_anomaly(transaction)` | `data_manager.py` | 核心算法：支出 > 均值 × 1.5 |
| `get_category_avg()` | `data_manager.py` | 返回历史均值，供弹窗提示 |
| `_get_expense_history_amounts()` | `data_manager.py` | SQL 查询历史支出 |
| `view_all_transactions()` | `main.py` | CLI 异常行 `[🔴 异常]` 标记 |
| `_format_anomaly_suffix()` | `main.py` | colorama 红色输出 / 纯文本降级 |
| `_refresh_records_table()` | `gui.py` | Treeview `tag_configure('anomaly')` 红色加粗 |
| `_on_save_transaction()` | `gui.py` | 保存后 `messagebox.showwarning` 异常提醒 |

**算法逻辑（`check_anomaly`）：**

```
if transaction.type != 'expense': return False
history = 同用户同分类历史支出（不含当前记录）
if len(history) < 2: return False
avg = sum(history) / len(history)
return transaction.amount > avg * THRESHOLD
```

---

## 作者信息

- 课程：《Python 程序设计》
- 项目：项目 1 — 智能个人记账助手（Smart Expense Tracker）
- 得分：基础 70 分 + 加分 ★1（消费异常检测）
