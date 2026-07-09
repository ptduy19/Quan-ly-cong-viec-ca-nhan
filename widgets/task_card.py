"""
Duypt2 Task Manager — Task Card Widget.

A reusable card component displaying a single task with priority badge,
deadline indicator, progress bar, and action buttons.
"""
import customtkinter as ctk
from datetime import datetime

from config.settings import (
    FONT_FAMILY, FONT_SIZE_SM, FONT_SIZE_MD, FONT_SIZE_XS,
    PRIORITY_CONFIG, STATUS_CONFIG, DEADLINE_COLORS, DARK, LIGHT
)
from utils.icon_manager import IconManager


class TaskCard(ctk.CTkFrame):
    """
    A styled card widget representing a single task.

    Args:
        master: Parent widget.
        task: Task dictionary from the database.
        theme: Current theme dict (DARK or LIGHT).
        on_click: Callback(task) when card is clicked.
        on_complete: Callback(task_id) when complete button is pressed.
        on_delete: Callback(task_id) for delete action.
        on_duplicate: Callback(task_id) for duplicate action.
        on_edit: Callback(task) for edit action.
    """

    def __init__(self, master, task: dict, theme: dict = None,
                 on_click=None, on_complete=None, on_delete=None,
                 on_duplicate=None, on_edit=None, **kwargs):
        self.theme = theme or DARK
        self.task = task
        self.on_click = on_click
        self.on_complete = on_complete
        self.on_delete = on_delete
        self.on_duplicate = on_duplicate
        self.on_edit = on_edit

        super().__init__(
            master,
            fg_color=self.theme["bg_card"],
            corner_radius=12,
            border_width=1,
            border_color=self.theme["border"],
            **kwargs
        )

        self._build_card()

        # Hover effects
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        
        # Bind click event to the main frame and all children
        self._bind_click_event(self)

    def _build_card(self):
        """Build the card layout."""
        task = self.task
        t = self.theme

        # ── Top row: Priority dot + Title + Status badge ─────────────────
        top_frame = ctk.CTkFrame(self, fg_color="transparent")
        top_frame.pack(fill="x", padx=14, pady=(12, 4))

        # Priority dot
        priority_cfg = PRIORITY_CONFIG.get(task.get("priority", "medium"), PRIORITY_CONFIG["medium"])
        priority_dot = ctk.CTkLabel(
            top_frame,
            text="",
            image=IconManager.get_icon(priority_cfg["icon"], color=priority_cfg["color"], size=12),
            width=20,
        )
        priority_dot.pack(side="left", padx=(0, 6))

        # Title
        title_label = ctk.CTkLabel(
            top_frame,
            text=task.get("title", "Untitled"),
            font=(FONT_FAMILY, FONT_SIZE_MD, "bold"),
            text_color=t["text_primary"],
            anchor="w",
        )
        title_label.pack(side="left", fill="x", expand=True)

        # Status badge
        status = task.get("status", "pending")
        status_cfg = STATUS_CONFIG.get(status, STATUS_CONFIG["pending"])
        status_badge = ctk.CTkLabel(
            top_frame,
            text=f" {status_cfg['label']} ",
            image=IconManager.get_icon(status_cfg["icon"], color=status_cfg["color"], size=10),
            compound="left",
            font=(FONT_FAMILY, FONT_SIZE_XS),
            text_color=status_cfg["color"],
            fg_color="transparent",
            corner_radius=6,
            height=22,
        )
        status_badge.pack(side="right", padx=(6, 0))

        # ── Description (if present) ─────────────────────────────────────
        desc = task.get("description", "")
        if desc:
            desc_label = ctk.CTkLabel(
                self,
                text=desc[:100] + ("..." if len(desc) > 100 else ""),
                font=(FONT_FAMILY, FONT_SIZE_XS),
                text_color=t["text_secondary"],
                anchor="w",
                justify="left",
            )
            desc_label.pack(fill="x", padx=14, pady=(0, 4))

        # ── Meta row: deadline, category, assignee ───────────────────────
        meta_frame = ctk.CTkFrame(self, fg_color="transparent")
        meta_frame.pack(fill="x", padx=14, pady=(2, 4))

        # Deadline badge with color
        deadline_color = self._get_deadline_color()
        deadline_text = self._format_deadline()
        deadline_badge = ctk.CTkLabel(
            meta_frame,
            text=f" {deadline_text} ",
            image=IconManager.get_icon("\uf017", color=deadline_color, size=10),
            compound="left",
            font=(FONT_FAMILY, FONT_SIZE_XS),
            text_color=deadline_color,
            fg_color="transparent",
            corner_radius=6,
            height=22,
        )
        deadline_badge.pack(side="left", padx=(0, 6))

        # Category badge
        cat_name = task.get("category_name")
        cat_icon = task.get("category_icon", "\uf07b")
        cat_color = task.get("category_color", "#3498db")
        if cat_name:
            cat_badge = ctk.CTkLabel(
                meta_frame,
                text=f" {cat_name} ",
                image=IconManager.get_icon(cat_icon, color=cat_color, size=10),
                compound="left",
                font=(FONT_FAMILY, FONT_SIZE_XS),
                text_color=cat_color,
                fg_color="transparent",
                corner_radius=6,
                height=22,
            )
            cat_badge.pack(side="left", padx=(0, 6))

        # Assignee
        assignee = task.get("assignee", "")
        if assignee:
            assignee_label = ctk.CTkLabel(
                meta_frame,
                text=f" {assignee}",
                image=IconManager.get_icon("\uf007", color=t["text_muted"], size=10),
                compound="left",
                font=(FONT_FAMILY, FONT_SIZE_XS),
                text_color=t["text_muted"],
            )
            assignee_label.pack(side="left", padx=(0, 6))

        # ── Progress bar ─────────────────────────────────────────────────
        progress = task.get("progress", 0)
        progress_frame = ctk.CTkFrame(self, fg_color="transparent")
        progress_frame.pack(fill="x", padx=14, pady=(2, 4))

        progress_bar = ctk.CTkProgressBar(
            progress_frame,
            height=6,
            corner_radius=3,
            progress_color=self._get_progress_color(progress),
            fg_color=t["bg_input"],
        )
        progress_bar.pack(side="left", fill="x", expand=True, padx=(0, 8))
        progress_bar.set(progress / 100)

        progress_label = ctk.CTkLabel(
            progress_frame,
            text=f"{progress}%",
            font=(FONT_FAMILY, FONT_SIZE_XS),
            text_color=t["text_muted"],
            width=35,
        )
        progress_label.pack(side="right")

        # ── Action buttons ───────────────────────────────────────────────
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=14, pady=(2, 10))

        if task.get("status") != "completed":
            btn_complete = ctk.CTkButton(
                btn_frame,
                text=" Hoàn thành",
                image=IconManager.get_icon("\uf00c", color="#ffffff", size=12),
                font=(FONT_FAMILY, FONT_SIZE_SM),
                width=95,
                height=26,
                corner_radius=6,
                fg_color=t["success"],
                hover_color=t["success"],
                text_color=t["success"],
                command=lambda: self.on_complete(task["id"]) if self.on_complete else None,
            )
            btn_complete.pack(side="left", padx=(0, 4))

        btn_edit = ctk.CTkButton(
            btn_frame,
            text=" Sửa",
            image=IconManager.get_icon("\uf040", color=t["text_secondary"], size=12),
            font=(FONT_FAMILY, FONT_SIZE_SM),
            width=60,
            height=26,
            corner_radius=6,
            fg_color=t["info"],
            hover_color=t["info"],
            text_color=t["info"],
            command=lambda: self.on_edit(task) if self.on_edit else None,
        )
        btn_edit.pack(side="left", padx=(0, 4))

        btn_dup = ctk.CTkButton(
            btn_frame,
            text=" Sao chép",
            image=IconManager.get_icon("\uf0c5", color=t["text_secondary"], size=12),
            font=(FONT_FAMILY, FONT_SIZE_SM),
            width=80,
            height=26,
            corner_radius=6,
            fg_color=t["accent"],
            hover_color=t["accent"],
            text_color=t["accent"],
            command=lambda: self.on_duplicate(task["id"]) if self.on_duplicate else None,
        )
        btn_dup.pack(side="left", padx=(0, 4))

        btn_del = ctk.CTkButton(
            btn_frame,
            text="",
            image=IconManager.get_icon("\uf1f8", color=t["danger"], size=12),
            font=(FONT_FAMILY, FONT_SIZE_SM),
            width=30,
            height=26,
            corner_radius=6,
            fg_color=t["danger"],
            hover_color=t["danger"],
            text_color=t["danger"],
            command=lambda: self.on_delete(task["id"]) if self.on_delete else None,
        )
        btn_del.pack(side="right")

    def _format_deadline(self) -> str:
        """Format deadline as a human-readable relative string."""
        try:
            dl = datetime.strptime(
                f"{self.task['deadline_date']} {self.task['deadline_time']}",
                "%Y-%m-%d %H:%M"
            )
            now = datetime.now()
            diff = dl - now

            if diff.total_seconds() < 0:
                return f"Quá hạn {abs(diff.days)}d"
            elif diff.days == 0:
                hours = int(diff.total_seconds() // 3600)
                if hours == 0:
                    mins = int(diff.total_seconds() // 60)
                    return f"Còn {mins} phút"
                return f"Còn {hours}h"
            elif diff.days == 1:
                return "Ngày mai"
            else:
                return f"Còn {diff.days} ngày"
        except (ValueError, TypeError):
            return self.task.get("deadline_date", "N/A")

    def _get_deadline_color(self) -> str:
        """Get color based on time remaining."""
        try:
            dl = datetime.strptime(
                f"{self.task['deadline_date']} {self.task['deadline_time']}",
                "%Y-%m-%d %H:%M"
            )
            diff = (dl - datetime.now()).total_seconds()

            if self.task.get("status") == "completed":
                return DEADLINE_COLORS["safe"]
            if diff <= 0:
                return DEADLINE_COLORS["danger"]
            elif diff <= 3600:
                return DEADLINE_COLORS["urgent"]
            elif diff <= 86400:
                return DEADLINE_COLORS["warning"]
            return DEADLINE_COLORS["safe"]
        except (ValueError, TypeError):
            return DEADLINE_COLORS["safe"]

    def _get_progress_color(self, progress: int) -> str:
        if progress >= 75:
            return self.theme["success"]
        elif progress >= 40:
            return self.theme["warning"]
        return self.theme["accent"]

    def _on_enter(self, event):
        self.configure(
            fg_color=self.theme["bg_card_hover"],
            border_color=self.theme["accent"]
        )

    def _on_leave(self, event):
        self.configure(
            fg_color=self.theme["bg_card"],
            border_color=self.theme["border"]
        )

    def _on_card_click(self, event):
        if self.on_click:
            self.on_click(self.task)

    def _bind_click_event(self, widget):
        """Recursively bind click event to all child widgets except buttons."""
        if not isinstance(widget, ctk.CTkButton):
            try:
                widget.bind("<Button-1>", self._on_card_click)
            except Exception:
                pass
            
            for child in widget.winfo_children():
                self._bind_click_event(child)
