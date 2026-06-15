"""
Duypt2 Task Manager — Settings View.

Theme toggle, notification preferences, import/export, and user profile.
"""
import customtkinter as ctk
from tkinter import filedialog, messagebox

from config.settings import FONT_FAMILY, FONT_SIZE_SM, FONT_SIZE_MD, FONT_SIZE_XL, APP_NAME, APP_VERSION, DARK
from models.user_model import UserModel
from utils.icon_manager import IconManager
from services.import_export import ImportExportService


class SettingsView(ctk.CTkFrame):
    """Settings panel for theme, notifications, import/export, and profile."""

    def __init__(self, master, theme: dict = None, on_theme_change=None, **kwargs):
        self.theme = theme or DARK
        self.on_theme_change = on_theme_change
        super().__init__(master, fg_color="transparent", **kwargs)

        self.user_model = UserModel()
        self.import_export = ImportExportService()

        self._build_ui()

    def _build_ui(self):
        t = self.theme

        scroll = ctk.CTkScrollableFrame(
            self, fg_color="transparent",
            scrollbar_button_color=t["scrollbar"],
        )
        scroll.pack(fill="both", expand=True)

        # ── Header ──────────────────────────────────────────────────────
        header = ctk.CTkFrame(scroll, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(20, 16))
        
        ctk.CTkLabel(
            header,
            text=" Cài đặt",
            image=IconManager.get_icon("\uf013", color=t["text_primary"], size=24),
            compound="left",
            font=(FONT_FAMILY, FONT_SIZE_XL, "bold"),
            text_color=t["text_primary"],
            anchor="w",
        ).pack(side="left")

        # ── Theme Section ───────────────────────────────────────────────
        self._add_section(scroll, "🎨 Giao diện")

        theme_card = self._create_card(scroll)

        ctk.CTkLabel(
            theme_card,
            text="Chế độ hiển thị",
            font=(FONT_FAMILY, FONT_SIZE_SM),
            text_color=t["text_primary"],
        ).pack(anchor="w", padx=16, pady=(12, 4))

        theme_frame = ctk.CTkFrame(theme_card, fg_color="transparent")
        theme_frame.pack(fill="x", padx=16, pady=(0, 12))

        user = self.user_model.get_default_user()
        current_theme = user.get("theme", "dark") if user else "dark"

        for mode, label, icon in [("dark", "Dark Mode", "🌙"), ("light", "Light Mode", "☀️")]:
            is_active = current_theme == mode
            btn = ctk.CTkButton(
                theme_frame,
                text=f"{icon} {label}",
                font=(FONT_FAMILY, FONT_SIZE_SM),
                width=140, height=40, corner_radius=10,
                fg_color=t["accent"] if is_active else t["bg_input"],
                hover_color=t["accent_hover"] if is_active else t["border"],
                text_color="#ffffff" if is_active else t["text_secondary"],
                command=lambda m=mode: self._change_theme(m),
            )
            btn.pack(side="left", padx=(0, 8))

        # ── Import/Export Section ────────────────────────────────────────
        self._add_section(scroll, "📥 Nhập / Xuất dữ liệu")

        ie_card = self._create_card(scroll)

        btn_frame = ctk.CTkFrame(ie_card, fg_color="transparent")
        btn_frame.pack(fill="x", padx=16, pady=12)

        ctk.CTkButton(
            btn_frame,
            text="\uf019 Import CSV", # download
            font=(FONT_FAMILY, FONT_SIZE_SM),
            width=140, height=38, corner_radius=8,
            fg_color=t["success"],
            hover_color=t["bg_card"],
            text_color="#ffffff",
            command=self._import_csv,
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            btn_frame,
            text="\uf019 Import Excel", # download
            font=(FONT_FAMILY, FONT_SIZE_SM),
            width=140, height=38, corner_radius=8,
            fg_color=t["info"],
            hover_color=t["bg_card"],
            text_color="#ffffff",
            command=self._import_excel,
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            btn_frame,
            text="\uf093 Export CSV", # upload
            font=(FONT_FAMILY, FONT_SIZE_SM),
            width=120, height=38, corner_radius=8,
            fg_color=t["warning"],
            hover_color=t["bg_card"],
            text_color="#ffffff",
            command=self._export_csv,
        ).pack(side="left", padx=(0, 8))

        btn_frame2 = ctk.CTkFrame(ie_card, fg_color="transparent")
        btn_frame2.pack(fill="x", padx=16, pady=(0, 12))

        ctk.CTkButton(
            btn_frame2,
            text="\uf0ea Tạo file mẫu CSV", # copy
            font=(FONT_FAMILY, FONT_SIZE_SM),
            width=160, height=38, corner_radius=8,
            fg_color=t["accent"],
            hover_color=t["bg_card"],
            text_color="#ffffff",
            command=self._generate_template,
        ).pack(side="left")

        # ── App Info ────────────────────────────────────────────────────
        self._add_section(scroll, "ℹ️ Thông tin ứng dụng")

        info_card = self._create_card(scroll)

        info_text = f"""
{APP_NAME}
Phiên bản: {APP_VERSION}
Phát triển: Duypt2
Công nghệ: Python, CustomTkinter, SQLite
        """.strip()

        ctk.CTkLabel(
            info_card,
            text=info_text,
            font=(FONT_FAMILY, FONT_SIZE_SM),
            text_color=t["text_secondary"],
            justify="left",
            anchor="w",
        ).pack(padx=16, pady=12, anchor="w")

    def _add_section(self, parent, title):
        ctk.CTkLabel(
            parent,
            text=title,
            font=(FONT_FAMILY, FONT_SIZE_MD, "bold"),
            text_color=self.theme["text_primary"],
            anchor="w",
        ).pack(fill="x", padx=20, pady=(16, 6))

    def _create_card(self, parent) -> ctk.CTkFrame:
        t = self.theme
        card = ctk.CTkFrame(
            parent,
            fg_color=t["bg_card"],
            corner_radius=12,
            border_width=1,
            border_color=t["border"],
        )
        card.pack(fill="x", padx=20, pady=(0, 4))
        return card

    def _change_theme(self, mode):
        user = self.user_model.get_default_user()
        if user:
            self.user_model.update_theme(user["id"], mode)
        if self.on_theme_change:
            self.on_theme_change(mode)

    def _import_csv(self):
        filepath = filedialog.askopenfilename(
            title="Chọn file CSV",
            filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")],
        )
        if filepath:
            result = self.import_export.import_csv(filepath)
            msg = f"Đã import {result['success']} công việc."
            if result["errors"]:
                msg += f"\n\nLỗi ({len(result['errors'])}):\n" + "\n".join(result["errors"][:5])
            messagebox.showinfo("Import CSV", msg)

    def _import_excel(self):
        filepath = filedialog.askopenfilename(
            title="Chọn file Excel",
            filetypes=[("Excel Files", "*.xlsx"), ("All Files", "*.*")],
        )
        if filepath:
            result = self.import_export.import_excel(filepath)
            msg = f"Đã import {result['success']} công việc."
            if result["errors"]:
                msg += f"\n\nLỗi ({len(result['errors'])}):\n" + "\n".join(result["errors"][:5])
            messagebox.showinfo("Import Excel", msg)

    def _export_csv(self):
        filepath = filedialog.asksaveasfilename(
            title="Lưu file CSV",
            defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv")],
        )
        if filepath:
            self.import_export.export_csv(filepath)
            messagebox.showinfo("Export", f"Đã xuất thành công!\n{filepath}")

    def _generate_template(self):
        filepath = filedialog.asksaveasfilename(
            title="Lưu file mẫu",
            defaultextension=".csv",
            initialfile="template_import.csv",
            filetypes=[("CSV Files", "*.csv")],
        )
        if filepath:
            self.import_export.generate_template_csv(filepath)
            messagebox.showinfo("Template", f"Đã tạo file mẫu!\n{filepath}")

    def refresh(self):
        pass
