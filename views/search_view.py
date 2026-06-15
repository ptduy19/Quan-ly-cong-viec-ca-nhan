"""
Duypt2 Task Manager — Search View.

Real-time search with advanced filters across all task fields.
"""
import customtkinter as ctk

from config.settings import (
    FONT_FAMILY, FONT_SIZE_XS, FONT_SIZE_SM, FONT_SIZE_MD,
    FONT_SIZE_XL, STATUS_CONFIG, PRIORITY_CONFIG, DARK
)
from models.task_model import TaskModel
from models.category_model import CategoryModel
from widgets.task_card import TaskCard
from utils.icon_manager import IconManager


class SearchView(ctk.CTkFrame):
    """Search and filter view with real-time results."""

    def __init__(self, master, theme: dict = None, on_task_action=None, **kwargs):
        self.theme = theme or DARK
        self.on_task_action = on_task_action
        super().__init__(master, fg_color="transparent", **kwargs)

        self.task_model = TaskModel()
        self.category_model = CategoryModel()
        self._search_after_id = None

        self._build_ui()

    def _build_ui(self):
        t = self.theme

        # ── Header ──────────────────────────────────────────────────────
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(20, 10))

        ctk.CTkLabel(
            header,
            text=" Tìm kiếm công việc",
            image=IconManager.get_icon("\uf002", color=t["text_primary"], size=24),
            compound="left",
            font=(FONT_FAMILY, FONT_SIZE_XL, "bold"),
            text_color=t["text_primary"],
            anchor="w",
        ).pack(side="left")

        # ── Search bar ──────────────────────────────────────────────────
        search_frame = ctk.CTkFrame(
            self, fg_color=t["bg_card"], corner_radius=12,
            border_width=1, border_color=t["border"],
        )
        search_frame.pack(fill="x", padx=20, pady=(0, 10))

        self.search_entry = ctk.CTkEntry(
            search_frame,
            placeholder_text="\uf002 Tìm theo tên, mô tả, người phụ trách...",
            font=(FONT_FAMILY, FONT_SIZE_MD),
            fg_color=t["bg_input"],
            border_color=t["border"],
            text_color=t["text_primary"],
            height=44,
        )
        self.search_entry.pack(fill="x", padx=12, pady=12)
        self.search_entry.bind("<KeyRelease>", self._on_search_key)

        # ── Filter chips ────────────────────────────────────────────────
        filter_frame = ctk.CTkFrame(self, fg_color="transparent")
        filter_frame.pack(fill="x", padx=20, pady=(0, 8))

        # Status filters
        self._status_var = ctk.StringVar(value="all")
        status_row = ctk.CTkFrame(filter_frame, fg_color="transparent")
        status_row.pack(fill="x", pady=2)

        ctk.CTkLabel(
            status_row, text="Trạng thái:",
            font=(FONT_FAMILY, FONT_SIZE_XS),
            text_color=t["text_muted"],
        ).pack(side="left", padx=(0, 8))

        for key, cfg in [("all", {"label": "Tất cả", "color": t["text_secondary"]})] + \
                        [(k, v) for k, v in STATUS_CONFIG.items()]:
            btn = ctk.CTkButton(
                status_row,
                text=cfg["label"],
                font=(FONT_FAMILY, FONT_SIZE_XS),
                width=80, height=26, corner_radius=13,
                fg_color=t["bg_card"] if key != "all" else t["bg_input"],
                hover_color=t["bg_input"] if key != "all" else t["border"],
                text_color=cfg["color"],
                command=lambda k=key: self._set_status_filter(k),
            )
            btn.pack(side="left", padx=2)

        # Priority filters
        prio_row = ctk.CTkFrame(filter_frame, fg_color="transparent")
        prio_row.pack(fill="x", pady=2)

        ctk.CTkLabel(
            prio_row, text="Ưu tiên:",
            font=(FONT_FAMILY, FONT_SIZE_XS),
            text_color=t["text_muted"],
        ).pack(side="left", padx=(0, 8))

        self._priority_var = ctk.StringVar(value="all")
        for key, cfg in [("all", {"label": "Tất cả", "color": t["text_secondary"]})] + \
                        [(k, v) for k, v in PRIORITY_CONFIG.items()]:
            btn = ctk.CTkButton(
                prio_row,
                text=cfg["label"],
                font=(FONT_FAMILY, FONT_SIZE_XS),
                width=80, height=26, corner_radius=13,
                fg_color=t["bg_card"] if key != "all" else t["bg_input"],
                hover_color=t["bg_input"] if key != "all" else t["border"],
                text_color=cfg["color"],
                command=lambda k=key: self._set_priority_filter(k),
            )
            btn.pack(side="left", padx=2)

        # ── Results count ───────────────────────────────────────────────
        self.results_label = ctk.CTkLabel(
            self, text="Nhập từ khóa để tìm kiếm",
            font=(FONT_FAMILY, FONT_SIZE_XS),
            text_color=t["text_muted"], anchor="w",
        )
        self.results_label.pack(fill="x", padx=24, pady=(0, 4))

        # ── Results list ────────────────────────────────────────────────
        self.results_frame = ctk.CTkScrollableFrame(
            self, fg_color="transparent",
            scrollbar_button_color=t["scrollbar"],
        )
        self.results_frame.pack(fill="both", expand=True, padx=20, pady=(0, 10))

    def _set_status_filter(self, value):
        self._status_var.set(value)
        self._do_search()

    def _set_priority_filter(self, value):
        self._priority_var.set(value)
        self._do_search()

    def _on_search_key(self, event):
        """Debounced search on key release."""
        if self._search_after_id:
            self.after_cancel(self._search_after_id)
        self._search_after_id = self.after(300, self._do_search)

    def _do_search(self):
        """Execute search with current query and filters."""
        query = self.search_entry.get().strip()
        status = self._status_var.get()
        priority = self._priority_var.get()

        if not query and status == "all" and priority == "all":
            for child in self.results_frame.winfo_children():
                child.destroy()
            self.results_label.configure(text="Nhập từ khóa để tìm kiếm")
            return

        tasks = self.task_model.search_tasks(
            query=query if query else "",
            status=status if status != "all" else None,
            priority=priority if priority != "all" else None,
        )

        # If no text query but filters applied, get all with filters
        if not query and (status != "all" or priority != "all"):
            tasks = self.task_model.get_all_tasks(
                status=status if status != "all" else None,
                priority=priority if priority != "all" else None,
            )

        self.results_label.configure(text=f"Tìm thấy {len(tasks)} kết quả")

        for child in self.results_frame.winfo_children():
            child.destroy()

        if not tasks:
            ctk.CTkLabel(
                self.results_frame,
                text="Không tìm thấy kết quả nào",
                font=(FONT_FAMILY, FONT_SIZE_MD),
                text_color=self.theme["text_muted"],
            ).pack(pady=40)
            return

        for task in tasks:
            card = TaskCard(
                self.results_frame,
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
        self._do_search()
