"""
Duypt2 Task Manager — Task List View.

Displays all tasks with filtering, sorting, and batch actions.
"""
import customtkinter as ctk
from tkinter import messagebox

from config.settings import (
    FONT_FAMILY, FONT_SIZE_SM, FONT_SIZE_MD, FONT_SIZE_LG,
    FONT_SIZE_XL, FONT_SIZE_XS, PRIORITY_CONFIG, STATUS_CONFIG, DARK
)
from models.task_model import TaskModel
from models.category_model import CategoryModel
from widgets.task_card import TaskCard
from utils.icon_manager import IconManager


class TaskListView(ctk.CTkFrame):
    """Full task list with filter bar, sort options, and task cards."""

    def __init__(self, master, theme: dict = None, on_task_action=None, **kwargs):
        self.theme = theme or DARK
        self.on_task_action = on_task_action
        super().__init__(master, fg_color="transparent", **kwargs)

        self.task_model = TaskModel()
        self.category_model = CategoryModel()

        # Current filter state
        self._filter_status = "all"
        self._filter_priority = "all"
        self._filter_category = "all"
        self._sort_by = "deadline_date ASC"
        self._dashboard_filter = None  # "today" | "due_soon" when opened from dashboard

        self._build_ui()
        self.load_tasks()

    def _build_ui(self):
        t = self.theme

        # ── Header ──────────────────────────────────────────────────────
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(20, 10))

        ctk.CTkLabel(
            header,
            text=" Quản lý công việc",
            image=IconManager.get_icon("\uf0ae", color=t["text_primary"], size=24),
            compound="left",
            font=(FONT_FAMILY, FONT_SIZE_XL, "bold"),
            text_color=t["text_primary"],
            anchor="w",
        ).pack(side="left")

        ctk.CTkButton(
            header,
            text="\uf067 Thêm công việc",
            font=(FONT_FAMILY, FONT_SIZE_SM, "bold"),
            width=140,
            height=36,
            corner_radius=8,
            fg_color=t["accent"],
            hover_color=t["accent_hover"],
            text_color="#ffffff",
            command=lambda: self._fire_action("add", None),
        ).pack(side="right")

        # ── Filter Bar ──────────────────────────────────────────────────
        filter_frame = ctk.CTkFrame(
            self, fg_color=t["bg_card"], corner_radius=10,
            border_width=1, border_color=t["border"],
        )
        filter_frame.pack(fill="x", padx=20, pady=(0, 10))

        inner = ctk.CTkFrame(filter_frame, fg_color="transparent")
        inner.pack(fill="x", padx=12, pady=10)

        # Status filter
        ctk.CTkLabel(
            inner, text="Trạng thái:", font=(FONT_FAMILY, FONT_SIZE_XS),
            text_color=t["text_secondary"],
        ).pack(side="left", padx=(0, 4))

        status_options = ["Tất cả", "Chưa làm", "Đang thực hiện", "Hoàn thành", "Quá hạn"]
        self.combo_status = ctk.CTkComboBox(
            inner, values=status_options, width=130, height=30,
            font=(FONT_FAMILY, FONT_SIZE_XS),
            fg_color=t["bg_input"], border_color=t["border"],
            text_color=t["text_primary"], button_color=t["accent"],
            dropdown_fg_color=t["bg_card"], dropdown_text_color=t["text_primary"],
            command=self._on_filter_change,
        )
        self.combo_status.set("Tất cả")
        self.combo_status.pack(side="left", padx=(0, 12))

        # Priority filter
        ctk.CTkLabel(
            inner, text="Ưu tiên:", font=(FONT_FAMILY, FONT_SIZE_XS),
            text_color=t["text_secondary"],
        ).pack(side="left", padx=(0, 4))

        prio_options = ["Tất cả", "Cao", "Trung bình", "Thấp"]
        self.combo_priority = ctk.CTkComboBox(
            inner, values=prio_options, width=120, height=30,
            font=(FONT_FAMILY, FONT_SIZE_XS),
            fg_color=t["bg_input"], border_color=t["border"],
            text_color=t["text_primary"], button_color=t["accent"],
            dropdown_fg_color=t["bg_card"], dropdown_text_color=t["text_primary"],
            command=self._on_filter_change,
        )
        self.combo_priority.set("Tất cả")
        self.combo_priority.pack(side="left", padx=(0, 12))

        # Sort
        ctk.CTkLabel(
            inner, text="Sắp xếp:", font=(FONT_FAMILY, FONT_SIZE_XS),
            text_color=t["text_secondary"],
        ).pack(side="left", padx=(0, 4))

        sort_options = ["Deadline ↑", "Deadline ↓", "Ưu tiên ↑", "Tên A-Z", "Tiến độ ↓"]
        self.combo_sort = ctk.CTkComboBox(
            inner, values=sort_options, width=120, height=30,
            font=(FONT_FAMILY, FONT_SIZE_XS),
            fg_color=t["bg_input"], border_color=t["border"],
            text_color=t["text_primary"], button_color=t["accent"],
            dropdown_fg_color=t["bg_card"], dropdown_text_color=t["text_primary"],
            command=self._on_sort_change,
        )
        self.combo_sort.set("Deadline ↑")
        self.combo_sort.pack(side="left")

        # ── Active filter banner (shown when navigated from dashboard) ───────
        self.filter_banner = ctk.CTkFrame(
            self, fg_color=t["bg_card"], corner_radius=8,
            border_width=1, border_color=t["accent"],
        )
        # Not packed yet — shown/hidden dynamically

        self._filter_banner_label = ctk.CTkLabel(
            self.filter_banner,
            text="",
            font=(FONT_FAMILY, FONT_SIZE_XS),
            text_color=t["accent"],
            anchor="w",
        )
        self._filter_banner_label.pack(side="left", padx=(12, 4), pady=6)

        ctk.CTkButton(
            self.filter_banner,
            text="× Xóa bộ lọc",
            font=(FONT_FAMILY, FONT_SIZE_XS),
            height=24, width=90, corner_radius=6,
            fg_color="transparent",
            hover_color=t["border"],
            text_color=t["text_muted"],
            command=self._clear_dashboard_filter,
        ).pack(side="right", padx=8, pady=6)

        # ── Task count label ────────────────────────────────────────────
        self.count_label = ctk.CTkLabel(
            self,
            text="",
            font=(FONT_FAMILY, FONT_SIZE_XS),
            text_color=t["text_muted"],
            anchor="w",
        )
        self.count_label.pack(fill="x", padx=24, pady=(0, 4))

        # ── Task list (scrollable) ──────────────────────────────────────
        self.task_scroll = ctk.CTkScrollableFrame(
            self, fg_color="transparent",
            scrollbar_button_color=t["scrollbar"],
        )
        self.task_scroll.pack(fill="both", expand=True, padx=20, pady=(0, 10))

    def _on_filter_change(self, value=None):
        """Handle filter combo change."""
        self._dashboard_filter = None
        self._hide_filter_banner()
        # Map Vietnamese labels back to keys
        status_map = {
            "Tất cả": "all", "Chưa làm": "pending",
            "Đang thực hiện": "in_progress", "Hoàn thành": "completed",
            "Quá hạn": "overdue",
        }
        prio_map = {
            "Tất cả": "all", "Cao": "high",
            "Trung bình": "medium", "Thấp": "low",
        }
        self._filter_status = status_map.get(self.combo_status.get(), "all")
        self._filter_priority = prio_map.get(self.combo_priority.get(), "all")
        self.load_tasks()

    def _on_sort_change(self, value=None):
        sort_map = {
            "Deadline ↑": "deadline_date ASC",
            "Deadline ↓": "deadline_date DESC",
            "Ưu tiên ↑": "priority ASC",
            "Tên A-Z": "title ASC",
            "Tiến độ ↓": "progress DESC",
        }
        self._sort_by = sort_map.get(self.combo_sort.get(), "deadline_date ASC")
        self.load_tasks()

    def apply_dashboard_filter(self, filter_type: str):
        """Apply a preset filter when navigating from the dashboard."""
        filter_labels = {
            "today":       "📅 Đang xem: Việc hôm nay",
            "due_soon":    "⏰ Đang xem: Sắp đến hạn",
            "overdue":     "🔴 Đang xem: Công việc quá hạn",
            "completed":   "✅ Đang xem: Hoàn thành",
            "pending":     "🗒️ Đang xem: Chưa làm",
            "in_progress": "⚡ Đang xem: Đang thực hiện",
            "all":         "📋 Đang xem: Tất cả công việc",
        }
        status_labels = {
            "all": "Tất cả",
            "pending": "Chưa làm",
            "in_progress": "Đang thực hiện",
            "completed": "Hoàn thành",
            "overdue": "Quá hạn",
        }

        if filter_type in ("today", "due_soon"):
            self._dashboard_filter = filter_type
            self.combo_status.set("Tất cả")
            self.combo_priority.set("Tất cả")
            self._filter_status = "all"
            self._filter_priority = "all"
        elif filter_type in status_labels:
            self._dashboard_filter = None
            self.combo_status.set(status_labels[filter_type])
            self.combo_priority.set("Tất cả")
            self._filter_status = filter_type if filter_type != "all" else "all"
            self._filter_priority = "all"
        else:
            self._dashboard_filter = None
            self.combo_status.set("Tất cả")
            self.combo_priority.set("Tất cả")
            self._filter_status = "all"
            self._filter_priority = "all"

        # Show banner
        banner_text = filter_labels.get(filter_type, f"Đang xem: {filter_type}")
        self._show_filter_banner(banner_text)

        self.load_tasks()

    def _clear_dashboard_filter(self):
        """Clear dashboard filter and show all tasks."""
        self._dashboard_filter = None
        self._filter_status = "all"
        self._filter_priority = "all"
        self.combo_status.set("Tất cả")
        self.combo_priority.set("Tất cả")
        self._hide_filter_banner()
        self.load_tasks()

    def _show_filter_banner(self, text: str):
        """Show the active filter banner with the given text."""
        self._filter_banner_label.configure(text=text)
        self.filter_banner.pack(fill="x", padx=20, pady=(0, 4), before=self.count_label)

    def _hide_filter_banner(self):
        """Hide the active filter banner."""
        self.filter_banner.pack_forget()

    def load_tasks(self):
        """Load and display tasks based on current filters."""
        if self._dashboard_filter == "today":
            tasks = self.task_model.get_tasks_today()
        elif self._dashboard_filter == "due_soon":
            tasks = self.task_model.get_tasks_due_soon(days=7)
        else:
            status = self._filter_status if self._filter_status != "all" else None
            priority = self._filter_priority if self._filter_priority != "all" else None

            tasks = self.task_model.get_all_tasks(
                status=status,
                priority=priority,
                order_by=self._sort_by,
            )

        # Clear existing cards
        for child in self.task_scroll.winfo_children():
            child.destroy()

        self.count_label.configure(text=f"Hiển thị {len(tasks)} công việc")

        if not tasks:
            ctk.CTkLabel(
                self.task_scroll,
                text="Chưa có công việc nào.\nNhấn ➕ Thêm mới để bắt đầu!",
                font=(FONT_FAMILY, FONT_SIZE_MD),
                text_color=self.theme["text_muted"],
                justify="center",
            ).pack(pady=60)
            return

        for task in tasks:
            card = TaskCard(
                self.task_scroll,
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
        """Alias for load_tasks — called by main window after data changes."""
        self.load_tasks()
