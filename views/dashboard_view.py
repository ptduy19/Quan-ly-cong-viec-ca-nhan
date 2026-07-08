"""
Duypt2 Task Manager — Dashboard View.

Displays summary statistics, charts, and recent tasks.
"""
import customtkinter as ctk
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np

from config.settings import FONT_FAMILY, FONT_SIZE_SM, FONT_SIZE_LG, FONT_SIZE_XL, DARK
from models.task_model import TaskModel
from widgets.stat_card import StatCard
from widgets.task_card import TaskCard
from utils.icon_manager import IconManager


class DashboardView(ctk.CTkFrame):
    """Dashboard with stat cards, chart, and task lists."""

    def __init__(self, master, theme: dict = None, on_task_action=None,
                 on_navigate_tasks=None, **kwargs):
        self.theme = theme or DARK
        self.on_task_action = on_task_action
        self.on_navigate_tasks = on_navigate_tasks
        super().__init__(master, fg_color="transparent", **kwargs)

        self.task_model = TaskModel()
        self._build_ui()

    def _build_ui(self):
        t = self.theme

        # ── Scrollable container ─────────────────────────────────────────
        self.scroll = ctk.CTkScrollableFrame(
            self, fg_color="transparent",
            scrollbar_button_color=t["scrollbar"],
        )
        self.scroll.pack(fill="both", expand=True, padx=0, pady=0)

        # ── Header ──────────────────────────────────────────────────────
        header = ctk.CTkFrame(self.scroll, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(20, 10))

        today_str = datetime.now().strftime("%A, %d/%m/%Y")
        ctk.CTkLabel(
            header,
            text=" Dashboard",
            image=IconManager.get_icon("\uf080", color=t["text_primary"], size=24),
            compound="left",
            font=(FONT_FAMILY, FONT_SIZE_XL, "bold"),
            text_color=t["text_primary"],
            anchor="w",
        ).pack(side="left")

        ctk.CTkLabel(
            header,
            text=today_str,
            font=(FONT_FAMILY, FONT_SIZE_SM),
            text_color=t["text_muted"],
        ).pack(side="right")

        # ── Stat Cards Row ──────────────────────────────────────────────
        self.stats_frame = ctk.CTkFrame(self.scroll, fg_color="transparent")
        self.stats_frame.pack(fill="x", padx=20, pady=(0, 10))
        self.stats_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

        self.stat_cards = {}
        self._create_stat_cards()

        # ── Charts Section ──────────────────────────────────────────────
        chart_frame = ctk.CTkFrame(
            self.scroll,
            fg_color=t["bg_card"],
            corner_radius=14,
            border_width=1,
            border_color=t["border"],
        )
        chart_frame.pack(fill="x", padx=20, pady=(0, 10))

        ctk.CTkLabel(
            chart_frame,
            text=" Tiến độ tuần này",
            image=IconManager.get_icon("\uf201", color=t["text_primary"], size=18),
            compound="left",
            font=(FONT_FAMILY, FONT_SIZE_LG, "bold"),
            text_color=t["text_primary"],
            anchor="w",
        ).pack(fill="x", padx=16, pady=(16, 8))

        self.chart_container = ctk.CTkFrame(chart_frame, fg_color="transparent")
        self.chart_container.pack(fill="x", padx=16, pady=(0, 16))

        self._draw_bar_chart()

        # ── Status Donut Chart ──────────────────────────────────────────
        donut_frame = ctk.CTkFrame(
            self.scroll,
            fg_color=t["bg_card"],
            corner_radius=14,
            border_width=1,
            border_color=t["border"],
        )
        donut_frame.pack(fill="x", padx=20, pady=(0, 10))

        ctk.CTkLabel(
            donut_frame,
            text=" Phân bổ trạng thái",
            image=IconManager.get_icon("\uf140", color=t["text_primary"], size=18),
            compound="left",
            font=(FONT_FAMILY, FONT_SIZE_LG, "bold"),
            text_color=t["text_primary"],
            anchor="w",
        ).pack(fill="x", padx=16, pady=(16, 8))

        self.donut_container = ctk.CTkFrame(donut_frame, fg_color="transparent")
        self.donut_container.pack(fill="x", padx=16, pady=(0, 16))

        self._draw_status_summary()

        # ── Tasks Due Today ─────────────────────────────────────────────
        today_section = ctk.CTkFrame(self.scroll, fg_color="transparent")
        today_section.pack(fill="x", padx=20, pady=(0, 10))

        today_header = ctk.CTkFrame(today_section, fg_color="transparent")
        today_header.pack(fill="x", pady=(0, 8))

        today_title = ctk.CTkLabel(
            today_header,
            text=" Việc hôm nay",
            image=IconManager.get_icon("\uf06d", color=t["accent"], size=18),
            compound="left",
            font=(FONT_FAMILY, FONT_SIZE_LG, "bold"),
            text_color=t["accent"],
            anchor="w",
            cursor="hand2",
        )
        today_title.pack(side="left")
        today_title.bind("<Button-1>", lambda e: self._open_task_list("today"))

        self._add_view_all_link(today_header, "today")

        self.today_tasks_frame = ctk.CTkFrame(today_section, fg_color="transparent")
        self.today_tasks_frame.pack(fill="x")

        self._load_today_tasks()

        # ── Upcoming Tasks ──────────────────────────────────────────────
        upcoming_section = ctk.CTkFrame(self.scroll, fg_color="transparent")
        upcoming_section.pack(fill="x", padx=20, pady=(0, 20))

        upcoming_header = ctk.CTkFrame(upcoming_section, fg_color="transparent")
        upcoming_header.pack(fill="x", pady=(0, 8))

        upcoming_title = ctk.CTkLabel(
            upcoming_header,
            text=" Sắp đến hạn",
            image=IconManager.get_icon("\uf017", color=t["warning"], size=18),
            compound="left",
            font=(FONT_FAMILY, FONT_SIZE_LG, "bold"),
            text_color=t["warning"],
            anchor="w",
            cursor="hand2",
        )
        upcoming_title.pack(side="left")
        upcoming_title.bind("<Button-1>", lambda e: self._open_task_list("due_soon"))

        self._add_view_all_link(upcoming_header, "due_soon")

        self.upcoming_frame = ctk.CTkFrame(upcoming_section, fg_color="transparent")
        self.upcoming_frame.pack(fill="x")

        self._load_upcoming_tasks()

        # ── Overdue Tasks ────────────────────────────────────────────────
        overdue_section = ctk.CTkFrame(self.scroll, fg_color="transparent")
        overdue_section.pack(fill="x", padx=20, pady=(0, 10))

        overdue_header = ctk.CTkFrame(overdue_section, fg_color="transparent")
        overdue_header.pack(fill="x", pady=(0, 8))

        overdue_title = ctk.CTkLabel(
            overdue_header,
            text=" Quá hạn",
            image=IconManager.get_icon("\uf071", color=t["danger"], size=18),
            compound="left",
            font=(FONT_FAMILY, FONT_SIZE_LG, "bold"),
            text_color=t["danger"],
            anchor="w",
            cursor="hand2",
        )
        overdue_title.pack(side="left")
        overdue_title.bind("<Button-1>", lambda e: self._open_task_list("overdue"))

        self._add_view_all_link(overdue_header, "overdue")

        self.overdue_frame = ctk.CTkFrame(overdue_section, fg_color="transparent")
        self.overdue_frame.pack(fill="x")

        self._load_overdue_tasks()

        # ── Completed Tasks ──────────────────────────────────────────────
        completed_section = ctk.CTkFrame(self.scroll, fg_color="transparent")
        completed_section.pack(fill="x", padx=20, pady=(0, 20))

        completed_header = ctk.CTkFrame(completed_section, fg_color="transparent")
        completed_header.pack(fill="x", pady=(0, 8))

        completed_title = ctk.CTkLabel(
            completed_header,
            text=" Đã hoàn thành gần đây",
            image=IconManager.get_icon("\uf058", color=t["success"], size=18),
            compound="left",
            font=(FONT_FAMILY, FONT_SIZE_LG, "bold"),
            text_color=t["success"],
            anchor="w",
            cursor="hand2",
        )
        completed_title.pack(side="left")
        completed_title.bind("<Button-1>", lambda e: self._open_task_list("completed"))

        self._add_view_all_link(completed_header, "completed")

        self.completed_frame = ctk.CTkFrame(completed_section, fg_color="transparent")
        self.completed_frame.pack(fill="x")

        self._load_completed_tasks()

    def _create_stat_cards(self):
        t = self.theme
        stats = self.task_model.get_stats()

        configs = [
            ("today",     "\uf0ae", stats["today"],     "Việc hôm nay",   t.get("info", "#00f0ff")), # tasks
            ("due_soon",  "\uf017", stats["due_soon"],  "Sắp đến hạn",    t.get("warning", "#ffff00")), # clock
            ("completed", "\uf058", stats["completed"], "Hoàn thành",     t.get("success", "#39ff14")), # check-circle
            ("overdue",   "\uf071", stats["overdue"],   "Quá hạn",        t.get("danger", "#ff0055")), # exclamation-triangle
        ]

        for idx, (key, icon, value, label, color) in enumerate(configs):
            card = StatCard(
                self.stats_frame,
                icon=icon,
                value=value,
                label=label,
                accent_color=color,
                theme=self.theme,
                on_click=lambda f=key: self._open_task_list(f),
            )
            card.grid(row=0, column=idx, padx=5, pady=5, sticky="nsew")
            self.stat_cards[key] = card

    def _add_view_all_link(self, parent, filter_type: str):
        """Small link button to open the filtered task list."""
        t = self.theme
        ctk.CTkButton(
            parent,
            text="Xem danh sách →",
            font=(FONT_FAMILY, FONT_SIZE_SM),
            height=28,
            width=130,
            corner_radius=6,
            fg_color="transparent",
            hover_color=t["bg_input"],
            text_color=t["accent"],
            anchor="e",
            command=lambda: self._open_task_list(filter_type),
        ).pack(side="right")

    def _open_task_list(self, filter_type: str):
        if self.on_navigate_tasks:
            self.on_navigate_tasks(filter_type)

    def _draw_bar_chart(self):
        """Draw a beautiful gradient bar chart using Matplotlib."""
        t = self.theme
        weekly = self.task_model.get_weekly_stats()

        if not weekly:
            return

        # Prepare data
        days = [w["day"] for w in weekly]
        totals = [w["total"] for w in weekly]
        completeds = [w["completed"] for w in weekly]
        
        # Setup plot with dark/light background
        fig, ax = plt.subplots(figsize=(6, 2.5), facecolor=t["bg_card"], dpi=100)
        ax.set_facecolor(t["bg_card"])
        
        # Spines
        for spine in ax.spines.values():
            spine.set_visible(False)
        ax.spines['bottom'].set_visible(True)
        ax.spines['bottom'].set_color(t["border"])
        
        x = np.arange(len(days))
        width = 0.4

        # Background bars (Total)
        ax.bar(x, totals, width, color=t["bg_input"], label="Tổng cộng")
        
        # Foreground bars (Completed)
        ax.bar(x, completeds, width, color=t["success"], label="Hoàn thành")

        # Labels
        ax.set_xticks(x)
        ax.set_xticklabels(days, color=t["text_secondary"], fontfamily=FONT_FAMILY)
        ax.tick_params(axis='x', colors=t["text_secondary"])
        ax.tick_params(axis='y', colors=t["text_muted"])
        
        # No y ticks, just let matplotlib handle grid if we want, or clear
        ax.yaxis.grid(True, linestyle='--', alpha=0.1, color=t["text_primary"])

        fig.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=self.chart_container)
        canvas.draw()
        widget = canvas.get_tk_widget()
        widget.configure(bg=t["bg_card"], highlightthickness=0)
        widget.pack(fill="both", expand=True)
        
        # Close fig to prevent memory leak
        plt.close(fig)

    def _draw_status_summary(self):
        """Draw status distribution as a Matplotlib Donut Chart."""
        t = self.theme
        stats = self.task_model.get_stats()

        # Data map corresponding to themes
        labels = ["Chưa làm", "Đang làm", "Hoàn thành", "Quá hạn"]
        sizes = [stats["pending"], stats["in_progress"], stats["completed"], stats["overdue"]]
        colors = [t.get("text_muted", "#8b8fa3"), t.get("info", "#00f0ff"), t.get("success", "#39ff14"), t.get("danger", "#ff0055")]
        
        # Filter empty
        labels = [l for s, l in zip(sizes, labels) if s > 0]
        colors = [c for s, c in zip(sizes, colors) if s > 0]
        sizes = [s for s in sizes if s > 0]

        if not sizes:
            # Empty state
            ctk.CTkLabel(
                self.donut_container, text="Chưa có dữ liệu", text_color=t["text_muted"], font=(FONT_FAMILY, FONT_SIZE_SM)
            ).pack(pady=20)
            return

        fig, ax = plt.subplots(figsize=(6, 2.5), facecolor=t["bg_card"], dpi=100)
        ax.set_facecolor(t["bg_card"])
        
        # Pie chart with shadow
        status_keys = ["pending", "in_progress", "completed", "overdue"]
        wedges, texts, autotexts = ax.pie(
            sizes,
            labels=labels,
            colors=colors,
            autopct='%1.1f%%',
            shadow=True,
            startangle=90,
            textprops={'color': t["text_primary"], 'family': FONT_FAMILY},
            wedgeprops=dict(width=0.4, edgecolor=t["bg_card"]) # Donut shape
        )

        # Clickable segments — open filtered task list
        filtered_keys = [k for s, k in zip(
            [stats["pending"], stats["in_progress"], stats["completed"], stats["overdue"]],
            status_keys,
        ) if s > 0]
        for wedge, status_key in zip(wedges, filtered_keys):
            wedge.set_picker(5)

        def on_pick(event):
            if event.artist in wedges:
                idx = wedges.index(event.artist)
                if idx < len(filtered_keys):
                    self._open_task_list(filtered_keys[idx])

        # Make autotexts darker or inverse
        for autotext in autotexts:
            autotext.set_color(t.get("text_inverse", "#000000"))
            autotext.set_fontweight('bold')

        ax.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
        fig.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=self.donut_container)
        canvas.mpl_connect("pick_event", on_pick)
        canvas.draw()
        widget = canvas.get_tk_widget()
        widget.configure(bg=t["bg_card"], highlightthickness=0)
        widget.pack(fill="both", expand=True)
        
        plt.close(fig)

    def _load_today_tasks(self):
        tasks = self.task_model.get_tasks_today()
        self._render_task_list(self.today_tasks_frame, tasks, "Không có việc nào hôm nay 🎉")

    def _load_upcoming_tasks(self):
        tasks = self.task_model.get_tasks_due_soon(days=7)
        self._render_task_list(self.upcoming_frame, tasks, "Không có việc sắp đến hạn")

    def _load_overdue_tasks(self):
        tasks = self.task_model.get_overdue_tasks()
        self._render_task_list(self.overdue_frame, tasks, "Không có việc quá hạn ✅")

    def _load_completed_tasks(self):
        tasks = self.task_model.get_completed_tasks(limit=5)
        self._render_task_list(self.completed_frame, tasks, "Chưa có việc hoàn thành")

    def _render_task_list(self, container, tasks, empty_msg):
        for child in container.winfo_children():
            child.destroy()

        if not tasks:
            ctk.CTkLabel(
                container,
                text=empty_msg,
                font=(FONT_FAMILY, FONT_SIZE_SM),
                text_color=self.theme["text_muted"],
            ).pack(pady=20)
            return

        for task in tasks[:10]:
            card = TaskCard(
                container,
                task=task,
                theme=self.theme,
                on_click=lambda t: self._fire_action("edit", t),
                on_complete=lambda tid: self._fire_action("complete", tid),
                on_delete=lambda tid: self._fire_action("delete", tid),
                on_duplicate=lambda tid: self._fire_action("duplicate", tid),
                on_edit=lambda t: self._fire_action("edit", t),
            )
            card.pack(fill="x", pady=4)

    def _fire_action(self, action, data):
        if self.on_task_action:
            self.on_task_action(action, data)

    def refresh(self):
        """Reload all dashboard data."""
        # Update stat cards
        stats = self.task_model.get_stats()
        for key, card in self.stat_cards.items():
            card.update_value(stats.get(key, 0))

        # Reload task lists
        self._load_today_tasks()
        self._load_upcoming_tasks()
        self._load_overdue_tasks()
        self._load_completed_tasks()

        # Redraw charts
        for child in self.chart_container.winfo_children():
            child.destroy()
        self._draw_bar_chart()

        for child in self.donut_container.winfo_children():
            child.destroy()
        self._draw_status_summary()
