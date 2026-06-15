"""
Duypt2 Task Manager — Calendar View.

Month/Week/Day calendar view showing tasks on their deadline dates.
Click to add/edit tasks. Navigate months with arrows.
"""
import customtkinter as ctk
from datetime import datetime, timedelta
import calendar

from config.settings import (
    FONT_FAMILY, FONT_SIZE_SM, FONT_SIZE_MD,
    FONT_SIZE_LG, FONT_SIZE_XL, FONT_SIZE_XS, DARK,
    STATUS_CONFIG, PRIORITY_CONFIG
)
from models.task_model import TaskModel
from utils.icon_manager import IconManager


class CalendarView(ctk.CTkFrame):
    """Calendar view with month grid, task indicators, and navigation."""

    def __init__(self, master, theme: dict = None, on_task_action=None, **kwargs):
        self.theme = theme or DARK
        self.on_task_action = on_task_action
        super().__init__(master, fg_color="transparent", **kwargs)

        self.task_model = TaskModel()
        self.current_date = datetime.now()
        self.view_mode = "month"  # month, week, day

        self._build_ui()
        self._render_calendar()

    def _build_ui(self):
        t = self.theme

        # ── Header with navigation ──────────────────────────────────────
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(20, 10))

        ctk.CTkLabel(
            header,
            text=" Lịch công việc",
            image=IconManager.get_icon("\uf133", color=t["text_primary"], size=24),
            compound="left",
            font=(FONT_FAMILY, FONT_SIZE_XL, "bold"),
            text_color=t["text_primary"],
            anchor="w",
        ).pack(side="left")

        # View mode buttons
        mode_frame = ctk.CTkFrame(header, fg_color="transparent")
        mode_frame.pack(side="right")

        for mode, label in [("month", "Tháng"), ("week", "Tuần"), ("day", "Ngày")]:
            btn = ctk.CTkButton(
                mode_frame,
                text=label,
                font=(FONT_FAMILY, FONT_SIZE_XS),
                width=60, height=30,
                corner_radius=6,
                fg_color=t["accent"] if self.view_mode == mode else t["bg_input"],
                hover_color=t["accent_hover"],
                text_color="#ffffff" if self.view_mode == mode else t["text_secondary"],
                command=lambda m=mode: self._set_view_mode(m),
            )
            btn.pack(side="left", padx=2)

        # ── Navigation bar ──────────────────────────────────────────────
        nav = ctk.CTkFrame(self, fg_color="transparent")
        nav.pack(fill="x", padx=20, pady=(0, 10))

        ctk.CTkButton(
            nav, text="", width=36, height=30, # angle-left
            image=IconManager.get_icon("\uf104", color=t["text_secondary"], size=16),
            font=(FONT_FAMILY, FONT_SIZE_SM),
            fg_color=t["bg_input"], hover_color=t["border"],
            text_color=t["text_secondary"], corner_radius=6,
            command=self._prev,
        ).pack(side="left", padx=2)

        self.month_label = ctk.CTkLabel(
            nav, text="",
            font=(FONT_FAMILY, FONT_SIZE_LG, "bold"),
            text_color=t["text_primary"],
        )
        self.month_label.pack(side="left", padx=10)

        ctk.CTkButton(
            nav, text="", width=36, height=30, # angle-right
            image=IconManager.get_icon("\uf105", color=t["text_secondary"], size=16),
            font=(FONT_FAMILY, FONT_SIZE_SM),
            fg_color=t["bg_input"], hover_color=t["border"],
            text_color=t["text_secondary"], corner_radius=6,
            command=self._next,
        ).pack(side="left", padx=2)

        ctk.CTkButton(
            nav, text="Hôm nay", width=80, height=30,
            font=(FONT_FAMILY, FONT_SIZE_XS),
            fg_color=t["accent"], hover_color=t["accent_hover"],
            text_color="#ffffff", corner_radius=6,
            command=self._go_today,
        ).pack(side="right")

        # ── Calendar grid container ─────────────────────────────────────
        self.calendar_frame = ctk.CTkScrollableFrame(
            self, fg_color="transparent",
            scrollbar_button_color=t["scrollbar"],
        )
        self.calendar_frame.pack(fill="both", expand=True, padx=20, pady=(0, 10))

    def _set_view_mode(self, mode):
        self.view_mode = mode
        self._render_calendar()

    def _prev(self):
        if self.view_mode == "month":
            if self.current_date.month == 1:
                self.current_date = self.current_date.replace(year=self.current_date.year - 1, month=12)
            else:
                self.current_date = self.current_date.replace(month=self.current_date.month - 1)
        elif self.view_mode == "week":
            self.current_date -= timedelta(days=7)
        else:
            self.current_date -= timedelta(days=1)
        self._render_calendar()

    def _next(self):
        if self.view_mode == "month":
            if self.current_date.month == 12:
                self.current_date = self.current_date.replace(year=self.current_date.year + 1, month=1)
            else:
                self.current_date = self.current_date.replace(month=self.current_date.month + 1)
        elif self.view_mode == "week":
            self.current_date += timedelta(days=7)
        else:
            self.current_date += timedelta(days=1)
        self._render_calendar()

    def _go_today(self):
        self.current_date = datetime.now()
        self._render_calendar()

    def _render_calendar(self):
        """Render the calendar based on current view mode."""
        for child in self.calendar_frame.winfo_children():
            child.destroy()

        if self.view_mode == "month":
            self._render_month()
        elif self.view_mode == "week":
            self._render_week()
        else:
            self._render_day()

    def _render_month(self):
        t = self.theme
        year = self.current_date.year
        month = self.current_date.month
        today = datetime.now().strftime("%Y-%m-%d")

        self.month_label.configure(text=f"Tháng {month}/{year}")

        # Get tasks for the month
        first_day = f"{year}-{month:02d}-01"
        last_day_num = calendar.monthrange(year, month)[1]
        last_day = f"{year}-{month:02d}-{last_day_num:02d}"
        tasks = self.task_model.get_tasks_in_range(first_day, last_day)

        # Group tasks by date
        tasks_by_date = {}
        for task in tasks:
            d = task["deadline_date"]
            tasks_by_date.setdefault(d, []).append(task)

        # Day headers
        days_vi = ["T2", "T3", "T4", "T5", "T6", "T7", "CN"]
        for col_idx, day_name in enumerate(days_vi):
            self.calendar_frame.grid_columnconfigure(col_idx, weight=1)
            ctk.CTkLabel(
                self.calendar_frame,
                text=day_name,
                font=(FONT_FAMILY, FONT_SIZE_SM, "bold"),
                text_color=t["text_muted"],
                height=30,
            ).grid(row=0, column=col_idx, sticky="ew", padx=2, pady=2)

        # Calendar days
        cal = calendar.Calendar(firstweekday=0)
        row = 1
        for day_date in cal.itermonthdates(year, month):
            col = day_date.weekday()
            date_str = day_date.strftime("%Y-%m-%d")
            is_current_month = day_date.month == month
            is_today = date_str == today
            day_tasks = tasks_by_date.get(date_str, [])

            # Day cell
            cell_color = t["bg_card"] if is_current_month else t["bg_primary"]
            if is_today:
                cell_color = t["bg_input"]

            cell = ctk.CTkFrame(
                self.calendar_frame,
                fg_color=cell_color,
                corner_radius=8,
                border_width=1 if is_today else 0,
                border_color=t["accent"] if is_today else t["border"],
                height=90,
            )
            cell.grid(row=row, column=col, padx=2, pady=2, sticky="nsew")
            cell.grid_propagate(False)
            cell.bind("<Button-1>", lambda e, d=date_str: self._on_day_click(d))

            # Day number
            day_color = t["text_primary"] if is_current_month else t["text_muted"]
            if is_today:
                day_color = t["accent"]

            ctk.CTkLabel(
                cell,
                text=str(day_date.day),
                font=(FONT_FAMILY, FONT_SIZE_SM, "bold" if is_today else "normal"),
                text_color=day_color,
                anchor="nw",
            ).pack(anchor="nw", padx=6, pady=(4, 0))

            # Task indicators (mini pills)
            for task in day_tasks[:3]:
                p_cfg = PRIORITY_CONFIG.get(task["priority"], PRIORITY_CONFIG["medium"])
                p_color = p_cfg["color"]
                pill = ctk.CTkLabel(
                    cell,
                    text=f"{p_cfg['icon']} {task['title'][:15]}",
                    font=(FONT_FAMILY, 10),
                    text_color="#ffffff",
                    fg_color=p_color,
                    corner_radius=4,
                    height=16,
                    anchor="w",
                )
                pill.pack(fill="x", padx=4, pady=1)
                pill.bind("<Button-1>", lambda e, t_=task: self._fire_action("edit", t_))

            if len(day_tasks) > 3:
                ctk.CTkLabel(
                    cell,
                    text=f"+{len(day_tasks) - 3} more",
                    font=(FONT_FAMILY, 8),
                    text_color=t["text_muted"],
                ).pack(anchor="w", padx=6)

            if col == 6:
                row += 1

        # Configure row heights
        for r in range(1, row + 1):
            self.calendar_frame.grid_rowconfigure(r, weight=1)

    def _render_week(self):
        t = self.theme
        # Find Monday of current week
        monday = self.current_date - timedelta(days=self.current_date.weekday())
        sunday = monday + timedelta(days=6)
        self.month_label.configure(
            text=f"{monday.strftime('%d/%m')} — {sunday.strftime('%d/%m/%Y')}"
        )

        today = datetime.now().strftime("%Y-%m-%d")
        tasks = self.task_model.get_tasks_in_range(
            monday.strftime("%Y-%m-%d"),
            sunday.strftime("%Y-%m-%d")
        )

        tasks_by_date = {}
        for task in tasks:
            d = task["deadline_date"]
            tasks_by_date.setdefault(d, []).append(task)

        days_vi = ["Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7", "CN"]

        for i in range(7):
            day_date = monday + timedelta(days=i)
            date_str = day_date.strftime("%Y-%m-%d")
            is_today = date_str == today
            day_tasks = tasks_by_date.get(date_str, [])

            # Day column
            col_color = t["bg_input"] if is_today else t["bg_card"]
            col_frame = ctk.CTkFrame(
                self.calendar_frame,
                fg_color=col_color,
                corner_radius=10,
                border_width=1,
                border_color=t["accent"] if is_today else t["border"],
            )
            col_frame.pack(fill="x", pady=4)
            col_frame.bind("<Button-1>", lambda e, d=date_str: self._on_day_click(d))

            # Day header
            header = ctk.CTkFrame(col_frame, fg_color="transparent")
            header.pack(fill="x", padx=12, pady=(10, 4))

            ctk.CTkLabel(
                header,
                text=f"{days_vi[i]} — {day_date.strftime('%d/%m')}",
                font=(FONT_FAMILY, FONT_SIZE_MD, "bold"),
                text_color=t["accent"] if is_today else t["text_primary"],
                anchor="w",
            ).pack(side="left")

            ctk.CTkLabel(
                header,
                text=f"{len(day_tasks)} việc",
                font=(FONT_FAMILY, FONT_SIZE_XS),
                text_color=t["text_muted"],
            ).pack(side="right")

            # Tasks
            for task in day_tasks:
                p_cfg = PRIORITY_CONFIG.get(task["priority"], PRIORITY_CONFIG["medium"])
                task_row = ctk.CTkFrame(col_frame, fg_color="transparent")
                task_row.pack(fill="x", padx=12, pady=2)

                ctk.CTkLabel(
                    task_row, text="●", font=(FONT_FAMILY, 10),
                    text_color=p_cfg["color"], width=16,
                ).pack(side="left")

                time_text = task.get("deadline_time", "")
                ctk.CTkLabel(
                    task_row,
                    text=f"{time_text} {task['title']}",
                    font=(FONT_FAMILY, FONT_SIZE_SM),
                    text_color=t["text_primary"], anchor="w",
                ).pack(side="left", fill="x", expand=True, padx=4)

                task_row.bind("<Button-1>", lambda e, t_=task: self._fire_action("edit", t_))

            if not day_tasks:
                ctk.CTkLabel(
                    col_frame,
                    text="Không có việc",
                    font=(FONT_FAMILY, FONT_SIZE_XS),
                    text_color=t["text_muted"],
                ).pack(padx=12, pady=6)

            # Bottom padding
            ctk.CTkFrame(col_frame, fg_color="transparent", height=6).pack()

    def _render_day(self):
        t = self.theme
        date_str = self.current_date.strftime("%Y-%m-%d")
        today = datetime.now().strftime("%Y-%m-%d")

        self.month_label.configure(text=self.current_date.strftime("%A, %d/%m/%Y"))

        tasks = self.task_model.get_tasks_by_date(date_str)

        is_today = date_str == today

        # Day header card
        day_card = ctk.CTkFrame(
            self.calendar_frame,
            fg_color=t["bg_input"] if is_today else t["bg_card"],
            corner_radius=12, border_width=1,
            border_color=t["accent"] if is_today else t["border"],
        )
        day_card.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(
            day_card,
            text=f"{'📌 Hôm nay — ' if is_today else ''}{len(tasks)} công việc",
            font=(FONT_FAMILY, FONT_SIZE_LG, "bold"),
            text_color=t["text_primary"],
        ).pack(padx=16, pady=12)

        # Timeline
        for hour in range(7, 24):
            hour_frame = ctk.CTkFrame(self.calendar_frame, fg_color="transparent")
            hour_frame.pack(fill="x", pady=1)

            ctk.CTkLabel(
                hour_frame,
                text=f"{hour:02d}:00",
                font=(FONT_FAMILY, FONT_SIZE_XS),
                text_color=t["text_muted"],
                width=50, anchor="e",
            ).pack(side="left", padx=(0, 8))

            line = ctk.CTkFrame(hour_frame, fg_color=t["border"], height=1)
            line.pack(side="left", fill="x", expand=True, pady=8)

            # Tasks at this hour
            hour_tasks = [
                task for task in tasks
                if task.get("deadline_time", "").startswith(f"{hour:02d}")
            ]
            for task in hour_tasks:
                p_cfg = PRIORITY_CONFIG.get(task["priority"], PRIORITY_CONFIG["medium"])
                task_pill = ctk.CTkFrame(
                    hour_frame,
                    fg_color=t["bg_card"],
                    corner_radius=6,
                )
                task_pill.pack(side="left", padx=4)

                ctk.CTkLabel(
                    task_pill,
                    text=f" {task['title']} ",
                    font=(FONT_FAMILY, FONT_SIZE_XS),
                    text_color=p_cfg["color"],
                ).pack(padx=4, pady=2)

                task_pill.bind("<Button-1>", lambda e, t_=task: self._fire_action("edit", t_))

    def _on_day_click(self, date_str):
        """Handle clicking on a day cell — open new task form for that date."""
        if self.on_task_action:
            self.on_task_action("add_on_date", date_str)

    def _fire_action(self, action, data):
        if self.on_task_action:
            self.on_task_action(action, data)

    def refresh(self):
        self._render_calendar()
