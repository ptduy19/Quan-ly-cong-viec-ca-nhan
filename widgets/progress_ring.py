"""
Duypt2 Task Manager — Circular Progress Ring Widget.

A Canvas-based circular progress indicator with animated fill and center text.
"""
import customtkinter as ctk
import math

from config.settings import DARK


class ProgressRing(ctk.CTkFrame):
    """Circular progress indicator rendered on a Canvas."""

    def __init__(self, master, value: int = 0, size: int = 120,
                 thickness: int = 10, color: str = "#6c5ce7",
                 bg_ring_color: str = None, theme: dict = None,
                 label: str = "", **kwargs):
        self.theme = theme or DARK
        super().__init__(master, fg_color="transparent", **kwargs)

        self._size = size
        self._thickness = thickness
        self._color = color
        self._bg_ring = bg_ring_color or self.theme["bg_input"]
        self._value = value
        self._label = label

        self.canvas = ctk.CTkCanvas(
            self,
            width=size,
            height=size + 20,
            bg=self.theme["bg_card"],
            highlightthickness=0,
        )
        self.canvas.pack()

        self._draw(value)

    def _draw(self, value: int):
        """Draw the progress ring with center percentage text."""
        self.canvas.delete("all")
        s = self._size
        t = self._thickness
        pad = t + 2

        # Background ring
        self.canvas.create_arc(
            pad, pad, s - pad, s - pad,
            start=90, extent=-360,
            style="arc", width=t,
            outline=self._bg_ring,
        )

        # Progress arc
        extent = -360 * (value / 100)
        if value > 0:
            self.canvas.create_arc(
                pad, pad, s - pad, s - pad,
                start=90, extent=extent,
                style="arc", width=t,
                outline=self._color,
            )

        # Center text
        center_x = s // 2
        center_y = s // 2
        self.canvas.create_text(
            center_x, center_y,
            text=f"{value}%",
            fill=self.theme["text_primary"],
            font=(self.theme.get("font", "Segoe UI"), int(s / 6), "bold"),
        )

        # Label below
        if self._label:
            self.canvas.create_text(
                center_x, s + 8,
                text=self._label,
                fill=self.theme["text_secondary"],
                font=(self.theme.get("font", "Segoe UI"), 10),
            )

    def set_value(self, value: int):
        """Update the progress value (0-100)."""
        self._value = max(0, min(100, value))
        self._draw(self._value)
