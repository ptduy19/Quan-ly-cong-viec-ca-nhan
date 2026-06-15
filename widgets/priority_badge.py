"""
Duypt2 Task Manager — Priority Badge Widget.
"""
import customtkinter as ctk
from config.settings import FONT_FAMILY, FONT_SIZE_XS, PRIORITY_CONFIG


class PriorityBadge(ctk.CTkLabel):
    """Small colored badge indicating task priority."""

    def __init__(self, master, priority: str = "medium", **kwargs):
        cfg = PRIORITY_CONFIG.get(priority, PRIORITY_CONFIG["medium"])
        super().__init__(
            master,
            text=f" {cfg['icon']} {cfg['label']} ",
            font=(FONT_FAMILY, FONT_SIZE_XS),
            text_color=cfg["color"],
            fg_color=self.theme["bg_input"],
            corner_radius=6,
            height=22,
            **kwargs
        )
