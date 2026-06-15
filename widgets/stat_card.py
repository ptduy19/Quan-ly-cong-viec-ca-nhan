"""
Duypt2 Task Manager — Stat Card Widget.

A dashboard statistics card with icon, value, and label.
"""
import customtkinter as ctk
from config.settings import FONT_FAMILY, FONT_SIZE_SM, DARK
from utils.icon_manager import IconManager


class StatCard(ctk.CTkFrame):
    """A card widget for displaying a single statistic."""

    def __init__(self, master, icon: str, value: int, label: str,
                 accent_color: str, theme: dict = None, **kwargs):
        self.theme = theme or DARK
        
        # In Option 4A: Card background is solid vibrant color
        super().__init__(
            master,
            fg_color=accent_color,
            corner_radius=12,
            border_width=0,
            **kwargs
        )
        self.grid_propagate(False)

        # ── Icon ─────────────────────────────────────────────────────────
        icon_label = ctk.CTkLabel(
            self,
            text="",
            image=IconManager.get_icon(icon, color="#ffffff", size=36),
            anchor="center",
        )
        icon_label.pack(side="left", padx=(20, 10), pady=16)

        # ── Data ─────────────────────────────────────────────────────────
        data_frame = ctk.CTkFrame(self, fg_color="transparent")
        data_frame.pack(side="left", fill="both", expand=True, padx=(0, 20), pady=12)

        self.value_label = ctk.CTkLabel(
            data_frame,
            text=str(value),
            font=(FONT_FAMILY, 32, "bold"),
            text_color="#ffffff",
            anchor="sw",
        )
        self.value_label.pack(fill="x", expand=True)

        ctk.CTkLabel(
            data_frame,
            text=label,
            font=(FONT_FAMILY, FONT_SIZE_SM),
            text_color="#ffffff", # Faint white
            anchor="nw",
        ).pack(fill="x", expand=True)

    def update_value(self, new_value: int):
        self.value_label.configure(text=str(new_value))
