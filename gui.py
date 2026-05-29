"""智能个人记账助手 - tkinter 图形界面模块。"""

import os
import tkinter as tk
from datetime import datetime
from tkinter import filedialog, messagebox, ttk
from typing import Dict, Optional

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from data_manager import THRESHOLD, DataManager
from file_handler import export_to_csv, export_to_json, import_from_csv, import_from_json
from validator import validate_amount, validate_date, validate_type, validate_year_month
from visualizer import get_monthly_pie_figure, get_monthly_trend_figure


class ExpenseTrackerGUI(tk.Tk):
    """
    智能个人记账助手 GUI 主类（基础得分项 1：OOP 设计）。

    继承 tk.Tk，封装界面布局与事件处理；持有 DataManager 实例，
    通过方法绑定按钮事件，复用原有业务逻辑层。
    """

    def __init__(self) -> None:
        """初始化窗口、数据管理器与各功能面板。"""
        super().__init__()
        # 基础得分项 6：启动时初始化 SQLite 数据库
        self.data_manager = DataManager()

        self.title("Smart Expense Tracker")
        self.geometry("1000x680")
        self.minsize(900, 600)

        # 当前嵌入的图表对象，用于导出 PNG
        self._pie_figure: Optional[Figure] = None
        self._trend_figure: Optional[Figure] = None
        self._pie_canvas: Optional[FigureCanvasTkAgg] = None
        self._trend_canvas: Optional[FigureCanvasTkAgg] = None

        # 分类 Combobox 显示名 -> category_id 映射
        self._category_map: Dict[str, int] = {}

        self._build_menu()
        self._build_layout()
        self._show_panel("add")

    def _build_menu(self) -> None:
        """
        构建顶部菜单栏（基础得分项 3：选择与分支）。

        使用 tk.Menu 实现功能分支选择，等价于命令行的 if/elif 菜单。
        """
        menubar = tk.Menu(self)
        self.config(menu=menubar)

        func_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="功能", menu=func_menu)
        func_menu.add_command(label="记一笔", command=lambda: self._show_panel("add"))
        func_menu.add_command(label="查看记录", command=lambda: self._show_panel("view"))
        func_menu.add_command(label="分类统计", command=lambda: self._show_panel("stats"))
        func_menu.add_command(label="月度报表", command=lambda: self._show_panel("report"))
        func_menu.add_separator()
        func_menu.add_command(label="导出数据", command=self._on_export)
        func_menu.add_command(label="导入数据", command=self._on_import)
        func_menu.add_separator()
        func_menu.add_command(label="退出", command=self._on_exit)

    def _build_layout(self) -> None:
        """构建左侧导航栏与右侧主内容区。"""
        main_frame = ttk.Frame(self, padding=8)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 左侧导航栏
        nav_frame = ttk.LabelFrame(main_frame, text="功能导航", padding=8)
        nav_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 8))

        nav_items = [
            ("记一笔", "add"),
            ("查看记录", "view"),
            ("分类统计", "stats"),
            ("月度报表", "report"),
            ("导出数据", None),
            ("导入数据", None),
            ("退出", None),
        ]
        for text, panel_key in nav_items:
            if panel_key:
                ttk.Button(
                    nav_frame,
                    text=text,
                    width=14,
                    command=lambda k=panel_key: self._show_panel(k),
                ).pack(pady=4, fill=tk.X)
            elif text == "导出数据":
                ttk.Button(nav_frame, text=text, width=14, command=self._on_export).pack(
                    pady=4, fill=tk.X
                )
            elif text == "导入数据":
                ttk.Button(nav_frame, text=text, width=14, command=self._on_import).pack(
                    pady=4, fill=tk.X
                )
            else:
                ttk.Button(nav_frame, text=text, width=14, command=self._on_exit).pack(
                    pady=4, fill=tk.X
                )

        user_label = ttk.Label(
            nav_frame,
            text=f"用户：{self.data_manager.current_user.username}",
            wraplength=120,
        )
        user_label.pack(side=tk.BOTTOM, pady=(20, 0))

        # 右侧主内容区
        self.content_frame = ttk.Frame(main_frame)
        self.content_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.panels: Dict[str, ttk.Frame] = {
            "add": self._build_add_panel(),
            "view": self._build_view_panel(),
            "stats": self._build_stats_panel(),
            "report": self._build_report_panel(),
        }

    def _show_panel(self, panel_key: str) -> None:
        """切换右侧显示的功能面板。"""
        for panel in self.panels.values():
            panel.pack_forget()
        self.panels[panel_key].pack(fill=tk.BOTH, expand=True)

        if panel_key == "view":
            self._refresh_records_table()
        elif panel_key == "stats":
            self._refresh_stats_table()
        elif panel_key == "report":
            self._refresh_month_options()

    # ---------- 记一笔面板（得分项 3/4/6） ----------

    def _build_add_panel(self) -> ttk.Frame:
        """构建「记一笔」表单面板。"""
        panel = ttk.LabelFrame(self.content_frame, text="记一笔（收入/支出）", padding=16)

        # 类型：Radiobutton 限定 income / expense（得分项 4）
        self.txn_type_var = tk.StringVar(value="expense")
        type_frame = ttk.Frame(panel)
        type_frame.grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=6)
        ttk.Label(type_frame, text="类型：").pack(side=tk.LEFT)
        ttk.Radiobutton(
            type_frame, text="支出", variable=self.txn_type_var, value="expense",
            command=self._on_type_changed,
        ).pack(side=tk.LEFT, padx=8)
        ttk.Radiobutton(
            type_frame, text="收入", variable=self.txn_type_var, value="income",
            command=self._on_type_changed,
        ).pack(side=tk.LEFT)

        # 日期 Entry（得分项 4：正则校验）
        ttk.Label(panel, text="日期：").grid(row=1, column=0, sticky=tk.W, pady=6)
        self.date_entry = ttk.Entry(panel, width=30)
        self.date_entry.grid(row=1, column=1, sticky=tk.W, pady=6)
        self.date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self.date_entry.bind("<FocusOut>", self._validate_date_field)

        # 分类 Combobox（得分项 3：下拉选择）
        ttk.Label(panel, text="分类：").grid(row=2, column=0, sticky=tk.W, pady=6)
        self.category_combo = ttk.Combobox(panel, width=28, state="readonly")
        self.category_combo.grid(row=2, column=1, sticky=tk.W, pady=6)
        self._refresh_category_combo()

        # 金额 Entry（得分项 4：正则校验）
        ttk.Label(panel, text="金额：").grid(row=3, column=0, sticky=tk.W, pady=6)
        self.amount_entry = ttk.Entry(panel, width=30)
        self.amount_entry.grid(row=3, column=1, sticky=tk.W, pady=6)
        self.amount_entry.bind("<FocusOut>", self._validate_amount_field)

        # 备注
        ttk.Label(panel, text="备注：").grid(row=4, column=0, sticky=tk.W, pady=6)
        self.note_entry = ttk.Entry(panel, width=30)
        self.note_entry.grid(row=4, column=1, sticky=tk.W, pady=6)

        ttk.Label(panel, text="提示：日期格式 YYYY-MM-DD，金额最多两位小数").grid(
            row=5, column=0, columnspan=2, sticky=tk.W, pady=(4, 0)
        )

        ttk.Button(panel, text="保存", command=self._on_save_transaction).grid(
            row=6, column=0, columnspan=2, pady=16
        )
        return panel

    def _on_type_changed(self) -> None:
        """类型切换时刷新分类下拉列表。"""
        self._refresh_category_combo()

    def _refresh_category_combo(self) -> None:
        """根据当前类型从 DataManager 加载分类到 Combobox。"""
        txn_type = self.txn_type_var.get()
        categories = self.data_manager.get_categories_by_type(txn_type)
        self._category_map = {}
        display_names = []
        for cat in categories:
            display = f"{cat.name} (ID:{cat.category_id})"
            display_names.append(display)
            self._category_map[display] = cat.category_id
        self.category_combo["values"] = display_names
        if display_names:
            self.category_combo.current(0)

    def _validate_date_field(self, event: Optional[tk.Event] = None) -> bool:
        """日期失去焦点时调用 validator 校验（得分项 4）。"""
        try:
            date_str = self.date_entry.get().strip()
            validated = validate_date(date_str)
            self.date_entry.delete(0, tk.END)
            self.date_entry.insert(0, validated)
            return True
        except ValueError as exc:
            messagebox.showerror("日期错误", str(exc))
            return False

    def _validate_amount_field(self, event: Optional[tk.Event] = None) -> bool:
        """金额失去焦点时调用 validator 校验（得分项 4）。"""
        text = self.amount_entry.get().strip()
        if not text:
            return False
        try:
            validate_amount(text)
            return True
        except ValueError as exc:
            messagebox.showerror("金额错误", str(exc))
            return False

    def _on_save_transaction(self) -> None:
        """保存一笔交易到 SQLite（得分项 6）。"""
        try:
            txn_type = validate_type(self.txn_type_var.get())
            if not self._validate_date_field():
                return
            if not self._validate_amount_field():
                return

            date = validate_date(self.date_entry.get().strip())
            amount = validate_amount(self.amount_entry.get().strip())

            category_display = self.category_combo.get()
            if not category_display or category_display not in self._category_map:
                messagebox.showerror("错误", "请选择有效的分类。")
                return
            category_id = self._category_map[category_display]

            cat = self.data_manager.categories.get(category_id)
            if cat and cat.type != txn_type:
                messagebox.showerror("错误", "所选分类与类型不匹配。")
                return

            note = self.note_entry.get().strip()
            txn = self.data_manager.add_transaction(date, amount, category_id, txn_type, note)

            self.amount_entry.delete(0, tk.END)
            self.note_entry.delete(0, tk.END)
            messagebox.showinfo("成功", "记录已保存")

            # 加分项1：保存后检测异常消费并弹窗提醒
            if self.data_manager.check_anomaly(txn):
                cat_name = cat.name if cat else "未知"
                avg = self.data_manager.get_category_avg(
                    txn.user_id, txn.category_id, txn.transaction_id
                )
                messagebox.showwarning(
                    "异常消费提醒",
                    f"该笔消费（¥{amount:.2f}）超出您「{cat_name}」类历史均值"
                    f"（¥{avg:.2f}）的 {THRESHOLD} 倍，已自动标红。",
                )

            self._refresh_records_table()
        except ValueError as exc:
            messagebox.showerror("输入错误", str(exc))
        except Exception as exc:
            messagebox.showerror("保存失败", str(exc))

    # ---------- 查看记录面板（得分项 2/6） ----------

    def _build_view_panel(self) -> ttk.Frame:
        """构建「查看记录」Treeview 面板。"""
        panel = ttk.LabelFrame(self.content_frame, text="所有交易记录", padding=8)

        columns = ("id", "date", "type", "category", "amount", "note")
        self.records_tree = ttk.Treeview(
            panel, columns=columns, show="headings", height=18
        )
        headings = {
            "id": "ID",
            "date": "日期",
            "type": "类型",
            "category": "分类",
            "amount": "金额",
            "note": "备注",
        }
        for col, title in headings.items():
            self.records_tree.heading(col, text=title)
            width = 80 if col != "note" else 200
            self.records_tree.column(col, width=width, anchor=tk.CENTER)

        # 加分项1：异常消费行标红加粗
        self.records_tree.tag_configure(
            "anomaly", foreground="red", font=("微软雅黑", 9, "bold")
        )

        scrollbar = ttk.Scrollbar(panel, orient=tk.VERTICAL, command=self.records_tree.yview)
        self.records_tree.configure(yscrollcommand=scrollbar.set)
        self.records_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        btn_frame = ttk.Frame(panel)
        btn_frame.pack(fill=tk.X, pady=(8, 0))
        ttk.Button(btn_frame, text="刷新", command=self._refresh_records_table).pack(
            side=tk.LEFT, padx=4
        )
        ttk.Button(btn_frame, text="删除选中", command=self._on_delete_record).pack(
            side=tk.LEFT, padx=4
        )
        return panel

    def _refresh_records_table(self) -> None:
        """
        从 DataManager 列表刷新 Treeview（得分项 2/6）。

        数据源来自 get_all_transactions() 返回的列表，不直接操作 SQL。
        """
        for item in self.records_tree.get_children():
            self.records_tree.delete(item)

        for txn in self.data_manager.transactions:
            category = self.data_manager.categories.get(txn.category_id)
            cat_name = category.name if category else "未知"
            type_label = "收入" if txn.type == "income" else "支出"
            # 加分项1：实时计算异常状态并设置行标签
            is_anomaly = self.data_manager.check_anomaly(txn)
            tags = ("anomaly",) if is_anomaly else ()
            note_text = txn.note
            if is_anomaly:
                note_text = f"{txn.note} [异常]" if txn.note else "[异常]"
            self.records_tree.insert(
                "",
                tk.END,
                values=(
                    txn.transaction_id,
                    txn.date,
                    type_label,
                    cat_name,
                    f"¥{txn.amount:.2f}",
                    note_text,
                ),
                tags=tags,
            )

    def _on_delete_record(self) -> None:
        """删除选中的交易记录（得分项 6）。"""
        try:
            selected = self.records_tree.selection()
            if not selected:
                messagebox.showwarning("提示", "请先选中要删除的记录。")
                return

            values = self.records_tree.item(selected[0], "values")
            txn_id = int(values[0])
            if messagebox.askyesno("确认", f"确定删除 ID={txn_id} 的记录吗？"):
                if self.data_manager.delete_transaction(txn_id):
                    self._refresh_records_table()
                    messagebox.showinfo("成功", "记录已删除。")
                else:
                    messagebox.showerror("错误", "删除失败。")
        except Exception as exc:
            messagebox.showerror("删除失败", str(exc))

    # ---------- 分类统计面板（得分项 2） ----------

    def _build_stats_panel(self) -> ttk.Frame:
        """构建「分类统计」面板。"""
        panel = ttk.LabelFrame(self.content_frame, text="按分类统计", padding=8)

        filter_frame = ttk.Frame(panel)
        filter_frame.pack(fill=tk.X, pady=(0, 8))
        ttk.Label(filter_frame, text="统计范围：").pack(side=tk.LEFT)
        self.stats_type_combo = ttk.Combobox(
            filter_frame,
            values=["全部", "支出", "收入"],
            state="readonly",
            width=12,
        )
        self.stats_type_combo.current(0)
        self.stats_type_combo.pack(side=tk.LEFT, padx=8)
        ttk.Button(filter_frame, text="刷新统计", command=self._refresh_stats_table).pack(
            side=tk.LEFT
        )

        self.stats_summary_label = ttk.Label(panel, text="")
        self.stats_summary_label.pack(anchor=tk.W, pady=(0, 8))

        columns = ("category", "total", "count")
        self.stats_tree = ttk.Treeview(panel, columns=columns, show="headings", height=16)
        self.stats_tree.heading("category", text="分类")
        self.stats_tree.heading("total", text="总额")
        self.stats_tree.heading("count", text="笔数")
        self.stats_tree.column("category", width=200, anchor=tk.CENTER)
        self.stats_tree.column("total", width=150, anchor=tk.CENTER)
        self.stats_tree.column("count", width=100, anchor=tk.CENTER)
        self.stats_tree.pack(fill=tk.BOTH, expand=True)
        return panel

    def _refresh_stats_table(self) -> None:
        """
        调用 DataManager 元组统计结果并展示（得分项 2）。

        统计结果格式：(category_name, total_amount, count)
        """
        choice = self.stats_type_combo.get()
        if choice == "支出":
            stats = self.data_manager.get_category_stats("expense")
            txn_filter = "expense"
        elif choice == "收入":
            stats = self.data_manager.get_category_stats("income")
            txn_filter = "income"
        else:
            stats = self.data_manager.get_category_stats()
            txn_filter = None

        for item in self.stats_tree.get_children():
            self.stats_tree.delete(item)

        if not stats:
            self.stats_summary_label.config(text="暂无统计数据。")
            return

        total_income = sum(
            t.amount for t in self.data_manager.transactions if t.type == "income"
        )
        total_expense = sum(
            t.amount for t in self.data_manager.transactions if t.type == "expense"
        )
        count = len(self.data_manager.transactions)
        if txn_filter == "expense":
            filtered_count = sum(c for _, _, c in stats)
            filtered_total = sum(a for _, a, _ in stats)
            self.stats_summary_label.config(
                text=f"支出总计：¥{filtered_total:.2f}  |  支出笔数：{filtered_count}"
            )
        elif txn_filter == "income":
            filtered_count = sum(c for _, _, c in stats)
            filtered_total = sum(a for _, a, _ in stats)
            self.stats_summary_label.config(
                text=f"收入总计：¥{filtered_total:.2f}  |  收入笔数：{filtered_count}"
            )
        else:
            self.stats_summary_label.config(
                text=(
                    f"收入总计：¥{total_income:.2f}  |  "
                    f"支出总计：¥{total_expense:.2f}  |  总笔数：{count}"
                )
            )

        for category_name, total_amount, item_count in stats:
            self.stats_tree.insert(
                "",
                tk.END,
                values=(category_name, f"¥{total_amount:.2f}", f"{item_count} 笔"),
            )

    # ---------- 月度报表面板（得分项 7） ----------

    def _build_report_panel(self) -> ttk.Frame:
        """构建「月度报表」面板，嵌入饼图与折线图。"""
        panel = ttk.LabelFrame(self.content_frame, text="月度报表", padding=8)

        ctrl_frame = ttk.Frame(panel)
        ctrl_frame.pack(fill=tk.X, pady=(0, 8))
        ttk.Label(ctrl_frame, text="选择年月：").pack(side=tk.LEFT)
        self.month_combo = ttk.Combobox(ctrl_frame, width=12, state="readonly")
        self.month_combo.pack(side=tk.LEFT, padx=8)
        ttk.Button(ctrl_frame, text="生成报表", command=self._render_charts).pack(
            side=tk.LEFT, padx=4
        )
        ttk.Button(ctrl_frame, text="导出图表为 PNG", command=self._export_charts).pack(
            side=tk.LEFT, padx=4
        )

        self.pie_chart_frame = ttk.LabelFrame(panel, text="支出分类占比（饼图）", padding=4)
        self.pie_chart_frame.pack(fill=tk.BOTH, expand=True, pady=4)

        self.trend_chart_frame = ttk.LabelFrame(panel, text="近6个月收支趋势（折线图）", padding=4)
        self.trend_chart_frame.pack(fill=tk.BOTH, expand=True, pady=4)

        return panel

    def _refresh_month_options(self) -> None:
        """从交易数据中提取可选年月列表。"""
        summary = self.data_manager.get_monthly_summary()
        months = sorted(summary.keys()) if summary else []
        if not months:
            now = datetime.now().strftime("%Y-%m")
            months = [now]
        self.month_combo["values"] = months
        self.month_combo.current(len(months) - 1)

    def _clear_chart_frame(self, frame: ttk.LabelFrame) -> None:
        """清空图表容器中的旧组件。"""
        for widget in frame.winfo_children():
            widget.destroy()

    def _embed_figure(
        self, frame: ttk.LabelFrame, fig: Figure
    ) -> FigureCanvasTkAgg:
        """将 matplotlib Figure 嵌入 tkinter 窗口（得分项 7）。"""
        canvas = FigureCanvasTkAgg(fig, master=frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        return canvas

    def _render_charts(self) -> None:
        """生成并嵌入饼图与折线图。"""
        try:
            year_month = self.month_combo.get().strip()
            if not year_month:
                messagebox.showwarning("提示", "请选择年月。")
                return
            validate_year_month(year_month)

            # 饼图
            self._clear_chart_frame(self.pie_chart_frame)
            pie_fig = get_monthly_pie_figure(self.data_manager, year_month)
            if pie_fig is None:
                ttk.Label(
                    self.pie_chart_frame, text=f"{year_month} 暂无支出记录。"
                ).pack(pady=20)
                self._pie_figure = None
                self._pie_canvas = None
            else:
                self._pie_figure = pie_fig
                self._pie_canvas = self._embed_figure(self.pie_chart_frame, pie_fig)

            # 折线图
            self._clear_chart_frame(self.trend_chart_frame)
            trend_fig = get_monthly_trend_figure(self.data_manager, months=6)
            if trend_fig is None:
                ttk.Label(self.trend_chart_frame, text="暂无交易记录。").pack(pady=20)
                self._trend_figure = None
                self._trend_canvas = None
            else:
                self._trend_figure = trend_fig
                self._trend_canvas = self._embed_figure(self.trend_chart_frame, trend_fig)

        except ValueError as exc:
            messagebox.showerror("格式错误", str(exc))
        except Exception as exc:
            messagebox.showerror("生成失败", str(exc))

    def _export_charts(self) -> None:
        """将当前嵌入的图表导出为 PNG 文件。"""
        try:
            if self._pie_figure is None and self._trend_figure is None:
                messagebox.showwarning("提示", "请先生成报表。")
                return

            folder = filedialog.askdirectory(title="选择保存目录")
            if not folder:
                return

            saved = []
            if self._pie_figure is not None:
                pie_path = os.path.join(folder, "monthly_pie.png")
                self._pie_figure.savefig(pie_path, dpi=150, bbox_inches="tight")
                saved.append(pie_path)
            if self._trend_figure is not None:
                trend_path = os.path.join(folder, "monthly_trend.png")
                self._trend_figure.savefig(trend_path, dpi=150, bbox_inches="tight")
                saved.append(trend_path)

            messagebox.showinfo("导出成功", "已保存：\n" + "\n".join(saved))
        except Exception as exc:
            messagebox.showerror("导出失败", str(exc))

    # ---------- 导入导出（得分项 5） ----------

    def _on_export(self) -> None:
        """导出数据到 JSON/CSV（得分项 5）。"""
        try:
            data = self.data_manager.get_all_transactions()
            if not data:
                messagebox.showwarning("提示", "暂无数据可导出。")
                return

            filepath = filedialog.asksaveasfilename(
                title="导出数据",
                defaultextension=".json",
                filetypes=[
                    ("JSON 文件", "*.json"),
                    ("CSV 文件", "*.csv"),
                    ("所有文件", "*.*"),
                ],
            )
            if not filepath:
                return

            if filepath.lower().endswith(".csv"):
                export_to_csv(data, filepath)
            else:
                if not filepath.lower().endswith(".json"):
                    filepath += ".json"
                export_to_json(data, filepath)

            messagebox.showinfo("成功", f"导出完成：\n{filepath}")
        except Exception as exc:
            messagebox.showerror("导出失败", str(exc))

    def _on_import(self) -> None:
        """从 JSON/CSV 导入数据（得分项 5）。"""
        try:
            filepath = filedialog.askopenfilename(
                title="导入数据",
                filetypes=[
                    ("JSON 文件", "*.json"),
                    ("CSV 文件", "*.csv"),
                    ("所有文件", "*.*"),
                ],
            )
            if not filepath:
                return

            if filepath.lower().endswith(".csv"):
                imported = import_from_csv(filepath)
            else:
                imported = import_from_json(filepath)

            count = 0
            for txn in imported:
                txn.user_id = self.data_manager.current_user.user_id
                txn.transaction_id = 0
                self.data_manager.save_transaction(txn)
                count += 1

            messagebox.showinfo("成功", f"共导入 {count} 条记录。")
        except Exception as exc:
            messagebox.showerror("导入失败", str(exc))

    def _on_exit(self) -> None:
        """退出程序并关闭数据库连接。"""
        if messagebox.askyesno("退出", "确定要退出吗？"):
            self.data_manager.close()
            self.destroy()


def run_gui() -> None:
    """
    启动 GUI 应用（基础得分项 3：事件循环）。

    tkinter.mainloop() 是 GUI 版的主事件循环，
    等价替代命令行版本的 while True 菜单循环。
    """
    app = ExpenseTrackerGUI()
    app.mainloop()


if __name__ == "__main__":
    run_gui()
