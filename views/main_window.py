"""
Duypt2 Task Manager — Main Window.

The primary application window with sidebar navigation, view switching,
system tray support, and task action orchestration.
"""
import customtkinter as ctk
import threading
import os

import pystray
from PIL import Image, ImageDraw
from tkinter import messagebox

from config.settings import (
    APP_NAME, FONT_FAMILY, FONT_FAMILY, FONT_SIZE_SM, FONT_SIZE_MD, FONT_SIZE_LG,
    FONT_SIZE_XS, NAV_ITEMS, SIDEBAR_WIDTH, SIDEBAR_COLLAPSED_WIDTH,
    WINDOW_DEFAULT_GEOMETRY, WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT,
    DARK, LIGHT
)
from utils.icon_manager import IconManager
from models.task_model import TaskModel
from models.user_model import UserModel
from views.dashboard_view import DashboardView
from views.task_list_view import TaskListView
from views.task_form import TaskFormDialog
from views.calendar_view import CalendarView
from views.search_view import SearchView
from views.settings_view import SettingsView


class MainWindow(ctk.CTk):
    """Main application window with sidebar and multi-view content area."""

    def __init__(self):
        super().__init__()
        
        IconManager.initialize()

        self.task_model = TaskModel()
        self.user_model = UserModel()
        self.tray_icon = None

        # Load user preferences
        user = self.user_model.get_default_user()
        theme_name = user.get("theme", "dark") if user else "dark"
        self.current_theme = DARK if theme_name == "dark" else LIGHT
        self._theme_name = theme_name

        # Window setup
        self.title(APP_NAME)
        self.geometry(WINDOW_DEFAULT_GEOMETRY)
        self.minsize(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT)
        ctk.set_appearance_mode("dark" if theme_name == "dark" else "light")
        self.configure(fg_color=self.current_theme["bg_primary"])

        # System tray on close
        self.protocol("WM_DELETE_WINDOW", self._hide_to_tray)

        # Track views
        self.views = {}
        self.current_view = None
        self._sidebar_expanded = True

        self._build_layout()
        self._navigate("dashboard")

    def _build_layout(self):
        """Build the main layout: sidebar + content area."""
        t = self.current_theme

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # ── Sidebar ─────────────────────────────────────────────────────
        self.sidebar = ctk.CTkFrame(
            self,
            fg_color=t["bg_sidebar"],
            width=SIDEBAR_WIDTH,
            corner_radius=0,
        )
        self.sidebar.grid(row=0, column=0, sticky="nsw")
        self.sidebar.grid_propagate(False)

        # App logo/title
        logo_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        logo_frame.pack(fill="x", padx=12, pady=(20, 24))

        ctk.CTkLabel(
            logo_frame,
            text="",
            image=IconManager.get_icon("\uf08d", color=t["accent"], size=24) # thumbtack
        ).pack(side="left", padx=(4, 8))

        self.logo_text = ctk.CTkLabel(
            logo_frame,
            text=APP_NAME.split(" ")[0],
            font=(FONT_FAMILY, FONT_SIZE_LG, "bold"),
            text_color=t["accent"],
        )
        self.logo_text.pack(side="left")

        # Nav items
        self.nav_buttons = {}
        for item in NAV_ITEMS:
            btn_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
            btn_frame.pack(fill="x", padx=8, pady=2)

            btn = ctk.CTkButton(
                btn_frame,
                text=f"  {item['label']}",
                image=IconManager.get_icon(item['icon'], color=t["text_secondary"], size=18),
                font=(FONT_FAMILY, FONT_SIZE_SM),
                anchor="w",
                height=42,
                corner_radius=10,
                fg_color="transparent",
                hover_color=t["bg_input"],
                text_color=t["text_secondary"],
                command=lambda nav_id=item["id"]: self._navigate(nav_id),
            )
            btn.pack(fill="x")
            self.nav_buttons[item["id"]] = btn

        # Spacer
        ctk.CTkFrame(self.sidebar, fg_color="transparent").pack(fill="both", expand=True)

        # Sidebar toggle button
        toggle_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        toggle_frame.pack(fill="x", padx=8, pady=(0, 12))

        self.toggle_btn = ctk.CTkButton(
            toggle_frame,
            text=" Thu gọn",
            image=IconManager.get_icon("\uf100", color=t["text_muted"], size=16),
            font=(FONT_FAMILY, FONT_SIZE_XS),
            height=32,
            corner_radius=8,
            fg_color=t["bg_input"],
            hover_color=t["border"],
            text_color=t["text_muted"],
            command=self._toggle_sidebar,
        )
        self.toggle_btn.pack(fill="x")

        # ── Content area ────────────────────────────────────────────────
        self.content = ctk.CTkFrame(
            self,
            fg_color=t["bg_primary"],
            corner_radius=0,
        )
        self.content.grid(row=0, column=1, sticky="nsew")

    def _navigate(self, view_id: str):
        """Switch to a different view."""
        # Update nav button styles
        t = self.current_theme
        
        # Get item color for the active tab
        active_color = t["accent"]
        for item in NAV_ITEMS:
            if item["id"] == view_id:
                active_color = item.get("color", t["accent"])
                break

        for nav_id, btn in self.nav_buttons.items():
            item = next(i for i in NAV_ITEMS if i["id"] == nav_id)
            if nav_id == view_id:
                btn.configure(
                    fg_color=t["bg_input"],
                    text_color=active_color,
                    image=IconManager.get_icon(item['icon'], color=active_color, size=18)
                )
            else:
                btn.configure(
                    fg_color="transparent",
                    text_color=t["text_secondary"],
                    image=IconManager.get_icon(item['icon'], color=t["text_secondary"], size=18)
                )

        # Remove current view
        if self.current_view:
            self.current_view.pack_forget()

        # Get or create view
        if view_id not in self.views:
            self.views[view_id] = self._create_view(view_id)

        self.current_view = self.views[view_id]
        self.current_view.pack(in_=self.content, fill="both", expand=True)

        # Refresh data when navigating
        if hasattr(self.current_view, "refresh"):
            self.current_view.refresh()

    def _create_view(self, view_id: str) -> ctk.CTkFrame:
        """Factory method to create views."""
        t = self.current_theme

        if view_id == "dashboard":
            return DashboardView(
                self.content, theme=t,
                on_task_action=self._handle_task_action,
            )
        elif view_id == "tasks":
            return TaskListView(
                self.content, theme=t,
                on_task_action=self._handle_task_action,
            )
        elif view_id == "calendar":
            return CalendarView(
                self.content, theme=t,
                on_task_action=self._handle_task_action,
            )
        elif view_id == "search":
            return SearchView(
                self.content, theme=t,
                on_task_action=self._handle_task_action,
            )
        elif view_id == "settings":
            return SettingsView(
                self.content, theme=t,
                on_theme_change=self._on_theme_change,
            )
        else:
            # Fallback empty frame
            frame = ctk.CTkFrame(self.content, fg_color="transparent")
            ctk.CTkLabel(frame, text=f"View: {view_id}").pack(pady=40)
            return frame

    def _handle_task_action(self, action: str, data):
        """Central handler for all task actions from any view."""
        if action == "add":
            self._open_task_form()
        elif action == "add_on_date":
            self._open_task_form(prefill_date=data)
        elif action == "edit":
            if isinstance(data, dict):
                self._open_task_form(task=data)
        elif action == "complete":
            self.task_model.mark_completed(data)
            self._refresh_all_views()
        elif action == "delete":
            if messagebox.askyesno("Xác nhận", "Bạn có chắc muốn xóa công việc này?"):
                self.task_model.delete_task(data)
                self._refresh_all_views()
        elif action == "duplicate":
            self.task_model.duplicate_task(data)
            self._refresh_all_views()

    def _open_task_form(self, task: dict = None, prefill_date: str = None):
        """Open the task creation/editing modal."""
        def on_save(data):
            if task and "id" in data:
                # Update existing task
                task_id = data.pop("id")
                self.task_model.update_task(task_id, **data)
            else:
                # Create new task
                self.task_model.create_task(**data)
            self._refresh_all_views()

        dialog = TaskFormDialog(
            self,
            theme=self.current_theme,
            task=task,
            on_save=on_save,
        )

        # Pre-fill date if adding from calendar
        if prefill_date and not task:
            dialog.entry_deadline_date.insert(0, prefill_date)

        dialog.wait_window()

    def _refresh_all_views(self):
        """Refresh all created views."""
        for view in self.views.values():
            if hasattr(view, "refresh"):
                try:
                    view.refresh()
                except Exception:
                    pass

    def _on_theme_change(self, mode: str):
        """Handle theme change from settings."""
        self.current_theme = DARK if mode == "dark" else LIGHT
        self._theme_name = mode
        ctk.set_appearance_mode(mode)

        # Recreate all views with new theme
        current_nav = None
        for nav_id, btn in self.nav_buttons.items():
            if self.views.get(nav_id) == self.current_view:
                current_nav = nav_id
                break

        if self.current_view:
            self.current_view.pack_forget()

        self.views.clear()
        self.current_view = None

        # Update sidebar colors
        t = self.current_theme
        self.configure(fg_color=t["bg_primary"])
        self.sidebar.configure(fg_color=t["bg_sidebar"])
        self.content.configure(fg_color=t["bg_primary"])

        for btn in self.nav_buttons.values():
            btn.configure(hover_color=t["bg_input"], text_color=t["text_secondary"])

        self.toggle_btn.configure(
            fg_color=t["bg_input"], text_color=t["text_muted"],
            hover_color=t["border"],
        )

        self.logo_text.configure(text_color=t["accent"])

        # Navigate back to current page
        if current_nav:
            self._navigate(current_nav)
        else:
            self._navigate("dashboard")

    def _toggle_sidebar(self):
        """Toggle sidebar between expanded and collapsed."""
        t = self.current_theme
        if self._sidebar_expanded:
            self.sidebar.configure(width=SIDEBAR_COLLAPSED_WIDTH)
            self.logo_text.pack_forget()
            for item in NAV_ITEMS:
                self.nav_buttons[item["id"]].configure(text=f"  {item['icon']}")
            self.toggle_btn.configure(text="▶")
            self._sidebar_expanded = False
        else:
            self.sidebar.configure(width=SIDEBAR_WIDTH)
            self.logo_text.pack(side="left")
            for item in NAV_ITEMS:
                self.nav_buttons[item["id"]].configure(text=f"  {item['icon']}   {item['label']}")
            self.toggle_btn.configure(text="◀ Thu gọn")
            self._sidebar_expanded = True

    # ── System Tray ──────────────────────────────────────────────────────

    def _hide_to_tray(self):
        """Minimize to system tray instead of closing."""
        self.withdraw()
        image = self._create_tray_icon()
        menu = pystray.Menu(
            pystray.MenuItem("Mở ứng dụng", self._show_from_tray),
            pystray.MenuItem("Thoát hoàn toàn", self._quit_app),
        )
        self.tray_icon = pystray.Icon(APP_NAME, image, APP_NAME, menu)
        threading.Thread(target=self.tray_icon.run, daemon=True).start()

    def _show_from_tray(self, icon, item):
        if self.tray_icon:
            self.tray_icon.stop()
            self.tray_icon = None
        self.after(0, self.deiconify)

    def _quit_app(self, icon, item):
        if self.tray_icon:
            self.tray_icon.stop()
        self.after(0, self.destroy)
        os._exit(0)

    def _create_tray_icon(self) -> Image.Image:
        """Create a simple tray icon."""
        size = 64
        img = Image.new("RGB", (size, size), "#6c5ce7")
        draw = ImageDraw.Draw(img)
        # Draw a checkmark
        draw.rectangle((size // 2, 0, size, size // 2), fill="#ffffff")
        draw.rectangle((0, size // 2, size // 2, size), fill="#ffffff")
        return img
