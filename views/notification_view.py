"""
Duypt2 Task Manager — Notification View.

Displays a list of notifications (read and unread).
"""
import customtkinter as ctk

from config.settings import (
    FONT_FAMILY, FONT_SIZE_XS, FONT_SIZE_SM, FONT_SIZE_MD,
    FONT_SIZE_XL, DARK
)
from models.notification_model import NotificationModel
from utils.icon_manager import IconManager
from tkinter import messagebox


class NotificationView(ctk.CTkFrame):
    """View to display and manage notifications."""

    def __init__(self, master, theme: dict = None, **kwargs):
        self.theme = theme or DARK
        super().__init__(master, fg_color="transparent", **kwargs)

        self.notification_model = NotificationModel()
        self._build_ui()

    def _build_ui(self):
        t = self.theme

        # ── Header ──────────────────────────────────────────────────────
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(20, 10))

        ctk.CTkLabel(
            header,
            text=" Thông báo",
            image=IconManager.get_icon("\uf0f3", color=t["text_primary"], size=24),
            compound="left",
            font=(FONT_FAMILY, FONT_SIZE_XL, "bold"),
            text_color=t["text_primary"],
            anchor="w",
        ).pack(side="left")

        # Action Buttons
        actions_frame = ctk.CTkFrame(header, fg_color="transparent")
        actions_frame.pack(side="right")

        ctk.CTkButton(
            actions_frame,
            text=" Đánh dấu đã đọc",
            image=IconManager.get_icon("\uf00c", color=t["success"], size=14),
            font=(FONT_FAMILY, FONT_SIZE_SM),
            height=32,
            corner_radius=8,
            fg_color=t["bg_card"],
            hover_color=t["bg_input"],
            text_color=t["success"],
            command=self._mark_all_read
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            actions_frame,
            text=" Xóa tất cả",
            image=IconManager.get_icon("\uf1f8", color=t["danger"], size=14),
            font=(FONT_FAMILY, FONT_SIZE_SM),
            height=32,
            corner_radius=8,
            fg_color=t["bg_card"],
            hover_color=t["bg_input"],
            text_color=t["danger"],
            command=self._clear_all
        ).pack(side="left", padx=5)

        # ── Results list ────────────────────────────────────────────────
        self.results_frame = ctk.CTkScrollableFrame(
            self, fg_color="transparent",
            scrollbar_button_color=t["scrollbar"],
        )
        self.results_frame.pack(fill="both", expand=True, padx=20, pady=(0, 10))

    def refresh(self):
        """Reload notifications."""
        for child in self.results_frame.winfo_children():
            child.destroy()

        notifications = self.notification_model.get_all_notifications()
        t = self.theme

        if not notifications:
            ctk.CTkLabel(
                self.results_frame,
                text="Không có thông báo nào",
                font=(FONT_FAMILY, FONT_SIZE_MD),
                text_color=t["text_muted"],
            ).pack(pady=40)
            return

        for notif in notifications:
            # Container
            bg_color = t["bg_input"] if notif["is_read"] else t["bg_card"]
            border_color = t["border"] if notif["is_read"] else t["accent"]

            card = ctk.CTkFrame(
                self.results_frame,
                fg_color=bg_color,
                corner_radius=10,
                border_width=1,
                border_color=border_color
            )
            card.pack(fill="x", pady=4)

            # Icon based on urgency
            urgency = notif.get("urgency", "info")
            if urgency == "critical":
                icon_char = "\uf071" # exclamation-triangle
                color = t["danger"]
            elif urgency == "warning":
                icon_char = "\uf06a" # exclamation-circle
                color = t["warning"]
            else:
                icon_char = "\uf05a" # info-circle
                color = t["info"]

            top_row = ctk.CTkFrame(card, fg_color="transparent")
            top_row.pack(fill="x", padx=12, pady=(10, 2))

            ctk.CTkLabel(
                top_row,
                text="",
                image=IconManager.get_icon(icon_char, color=color, size=16),
                width=24
            ).pack(side="left")

            title_font = (FONT_FAMILY, FONT_SIZE_MD, "normal" if notif["is_read"] else "bold")
            ctk.CTkLabel(
                top_row,
                text=notif["title"],
                font=title_font,
                text_color=t["text_primary"],
                anchor="w",
            ).pack(side="left", fill="x", expand=True, padx=(4, 0))

            date_str = notif["created_at"]
            if date_str:
                # Assuming format "YYYY-MM-DD HH:MM:SS"
                date_str = date_str[:16] # up to minutes
                
            ctk.CTkLabel(
                top_row,
                text=date_str,
                font=(FONT_FAMILY, FONT_SIZE_XS),
                text_color=t["text_muted"]
            ).pack(side="right")

            # Message
            msg_row = ctk.CTkFrame(card, fg_color="transparent")
            msg_row.pack(fill="x", padx=(40, 12), pady=(0, 10))

            ctk.CTkLabel(
                msg_row,
                text=notif["message"],
                font=(FONT_FAMILY, FONT_SIZE_SM),
                text_color=t["text_secondary"],
                anchor="w",
                justify="left",
            ).pack(side="left", fill="x", expand=True)

            # Mark as read action (if unread)
            if not notif["is_read"]:
                ctk.CTkButton(
                    msg_row,
                    text="Đã đọc",
                    width=60,
                    height=24,
                    corner_radius=6,
                    font=(FONT_FAMILY, FONT_SIZE_XS),
                    fg_color="transparent",
                    hover_color=t["border"],
                    text_color=t["text_secondary"],
                    command=lambda nid=notif["id"]: self._mark_read(nid)
                ).pack(side="right")

    def _mark_read(self, notif_id):
        self.notification_model.mark_as_read(notif_id)
        self.refresh()

    def _mark_all_read(self):
        self.notification_model.mark_all_as_read()
        self.refresh()

    def _clear_all(self):
        if messagebox.askyesno("Xác nhận", "Bạn có chắc muốn xoá tất cả thông báo không?"):
            self.notification_model.clear_all()
            self.refresh()
