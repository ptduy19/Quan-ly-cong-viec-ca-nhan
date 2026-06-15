"""
Duypt2 Task Manager — Task Form Dialog.

Modal dialog for creating and editing tasks with full field support,
including a quick-input NLP text box.
"""
import customtkinter as ctk
from datetime import datetime

from config.settings import (
    FONT_FAMILY, FONT_SIZE_XS, FONT_SIZE_SM, FONT_SIZE_MD, FONT_SIZE_LG,
    FONT_SIZE_XL, PRIORITY_CONFIG, DARK
)
from models.category_model import CategoryModel
from utils.icon_manager import IconManager


class TaskFormDialog(ctk.CTkToplevel):
    """
    Modal dialog for adding or editing a task.

    Args:
        master: Parent window.
        theme: Current theme dict.
        task: Existing task dict for editing (None for new task).
        on_save: Callback(data_dict) when Save is pressed.
    """

    def __init__(self, master, theme: dict = None, task: dict = None,
                 on_save=None, **kwargs):
        super().__init__(master, **kwargs)
        self.theme = theme or DARK
        self.task = task
        self.on_save = on_save
        self.result = None

        # Window setup
        self.title("Chỉnh sửa công việc" if task else "Thêm công việc mới")
        self.geometry("550x580")
        self.resizable(False, False)
        self.configure(fg_color=self.theme["bg_modal"])

        # Make modal
        self.transient(master)
        self.grab_set()

        # Center on parent
        self.update_idletasks()
        x = master.winfo_x() + (master.winfo_width() // 2) - 275
        y = master.winfo_y() + (master.winfo_height() // 2) - 340
        self.geometry(f"+{x}+{y}")

        # Load categories
        self.categories = CategoryModel().get_all()
        self.cat_names = [c["name"] for c in self.categories]

        self._build_ui()

        if task:
            self._populate_fields(task)

    def _build_ui(self):
        t = self.theme

        # ── Header ───────────────────────────────────────────────────────
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(20, 10))
        ctk.CTkLabel(
            header,
            text=f" {'Chỉnh sửa công việc' if self.task else 'Thêm công việc mới'}",
            image=IconManager.get_icon("\uf040" if self.task else "\uf067", color=t["text_primary"], size=20),
            compound="left",
            font=(FONT_FAMILY, FONT_SIZE_XL, "bold"),
            text_color=t["text_primary"],
        ).pack(side="left")


        # ── Scrollable form area ─────────────────────────────────────────
        form = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            scrollbar_button_color=t["scrollbar"],
        )
        form.pack(fill="both", expand=True, padx=20, pady=(0, 10))

        # Title
        self._add_label(form, "Tên công việc *")
        self.entry_title = ctk.CTkEntry(
            form, placeholder_text="Nhập tên công việc",
            font=(FONT_FAMILY, FONT_SIZE_SM),
            fg_color=t["bg_input"], border_color=t["border"],
            text_color=t["text_primary"], height=38,
        )
        self.entry_title.pack(fill="x", pady=(0, 10))

        # Description
        self._add_label(form, "Mô tả")
        self.entry_desc = ctk.CTkTextbox(
            form, height=70,
            font=(FONT_FAMILY, FONT_SIZE_SM),
            fg_color=t["bg_input"], border_color=t["border"],
            text_color=t["text_primary"],
        )
        self.entry_desc.pack(fill="x", pady=(0, 10))

        # Date row
        date_frame = ctk.CTkFrame(form, fg_color="transparent")
        date_frame.pack(fill="x", pady=(0, 10))
        date_frame.grid_columnconfigure((0, 1), weight=1)

        # Start date
        left = ctk.CTkFrame(date_frame, fg_color="transparent")
        left.grid(row=0, column=0, sticky="ew", padx=(0, 5))
        self._add_label(left, "Ngày bắt đầu")
        self.entry_start_date = ctk.CTkEntry(
            left, placeholder_text="YYYY-MM-DD",
            font=(FONT_FAMILY, FONT_SIZE_SM),
            fg_color=t["bg_input"], border_color=t["border"],
            text_color=t["text_primary"], height=36,
        )
        self.entry_start_date.pack(fill="x")

        # Deadline date
        right = ctk.CTkFrame(date_frame, fg_color="transparent")
        right.grid(row=0, column=1, sticky="ew", padx=(5, 0))
        self._add_label(right, "Deadline (ngày) *")
        self.entry_deadline_date = ctk.CTkEntry(
            right, placeholder_text="YYYY-MM-DD",
            font=(FONT_FAMILY, FONT_SIZE_SM),
            fg_color=t["bg_input"], border_color=t["border"],
            text_color=t["text_primary"], height=36,
        )
        self.entry_deadline_date.pack(fill="x")

        # Time + Priority row
        tp_frame = ctk.CTkFrame(form, fg_color="transparent")
        tp_frame.pack(fill="x", pady=(0, 10))
        tp_frame.grid_columnconfigure((0, 1), weight=1)

        # Deadline time
        tl = ctk.CTkFrame(tp_frame, fg_color="transparent")
        tl.grid(row=0, column=0, sticky="ew", padx=(0, 5))
        self._add_label(tl, "Deadline (giờ)")
        self.entry_deadline_time = ctk.CTkEntry(
            tl, placeholder_text="HH:MM",
            font=(FONT_FAMILY, FONT_SIZE_SM),
            fg_color=t["bg_input"], border_color=t["border"],
            text_color=t["text_primary"], height=36,
        )
        self.entry_deadline_time.pack(fill="x")

        # Priority
        tr = ctk.CTkFrame(tp_frame, fg_color="transparent")
        tr.grid(row=0, column=1, sticky="ew", padx=(5, 0))
        self._add_label(tr, "Mức độ ưu tiên")
        priority_labels = [PRIORITY_CONFIG[k]["label"] for k in ["high", "medium", "low"]]
        self.combo_priority = ctk.CTkComboBox(
            tr, values=priority_labels,
            font=(FONT_FAMILY, FONT_SIZE_SM),
            fg_color=t["bg_input"], border_color=t["border"],
            text_color=t["text_primary"], button_color=t["accent"],
            dropdown_fg_color=t["bg_card"],
            dropdown_text_color=t["text_primary"],
            height=36,
        )
        self.combo_priority.set("Trung bình")
        self.combo_priority.pack(fill="x")

        # Category + Assignee row
        ca_frame = ctk.CTkFrame(form, fg_color="transparent")
        ca_frame.pack(fill="x", pady=(0, 10))
        ca_frame.grid_columnconfigure((0, 1), weight=1)

        cl = ctk.CTkFrame(ca_frame, fg_color="transparent")
        cl.grid(row=0, column=0, sticky="ew", padx=(0, 5))
        self._add_label(cl, "Nhóm công việc")
        self.combo_category = ctk.CTkComboBox(
            cl, values=self.cat_names if self.cat_names else ["Cá nhân"],
            font=(FONT_FAMILY, FONT_SIZE_SM),
            fg_color=t["bg_input"], border_color=t["border"],
            text_color=t["text_primary"], button_color=t["accent"],
            dropdown_fg_color=t["bg_card"],
            dropdown_text_color=t["text_primary"],
            height=36,
        )
        if self.cat_names:
            self.combo_category.set(self.cat_names[0])
        self.combo_category.pack(fill="x")

        cr = ctk.CTkFrame(ca_frame, fg_color="transparent")
        cr.grid(row=0, column=1, sticky="ew", padx=(5, 0))
        self._add_label(cr, "Người phụ trách")
        self.entry_assignee = ctk.CTkEntry(
            cr, placeholder_text="Tên người phụ trách",
            font=(FONT_FAMILY, FONT_SIZE_SM),
            fg_color=t["bg_input"], border_color=t["border"],
            text_color=t["text_primary"], height=36,
        )
        self.entry_assignee.pack(fill="x")

        # ── Buttons ──────────────────────────────────────────────────────
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=(0, 20))

        ctk.CTkButton(
            btn_frame,
            text="Hủy",
            image=IconManager.get_icon("\uf00d", color=t["text_secondary"], size=14),
            compound="left",
            font=(FONT_FAMILY, FONT_SIZE_SM),
            width=100,
            height=40,
            corner_radius=8,
            fg_color=t["bg_input"],
            hover_color=t["border"],
            text_color=t["text_secondary"],
            command=self.destroy,
        ).pack(side="right", padx=(6, 0))

        ctk.CTkButton(
            btn_frame,
            text=" Lưu công việc",
            image=IconManager.get_icon("\uf0c7", color="#ffffff", size=14),
            compound="left",
            font=(FONT_FAMILY, FONT_SIZE_SM, "bold"),
            width=140,
            height=40,
            corner_radius=8,
            fg_color=t["accent"],
            hover_color=t["accent_hover"],
            command=self._save,
        ).pack(side="right")

    def _add_label(self, parent, text: str):
        ctk.CTkLabel(
            parent,
            text=text,
            font=(FONT_FAMILY, FONT_SIZE_XS),
            text_color=self.theme["text_secondary"],
            anchor="w",
        ).pack(fill="x", pady=(0, 4))

    def _populate_fields(self, task: dict):
        """Fill form fields with existing task data for editing."""
        self.entry_title.insert(0, task.get("title", ""))

        desc = task.get("description", "")
        if desc:
            self.entry_desc.insert("1.0", desc)

        if task.get("start_date"):
            self.entry_start_date.insert(0, task["start_date"])

        self.entry_deadline_date.insert(0, task.get("deadline_date", ""))
        self.entry_deadline_time.insert(0, task.get("deadline_time", "23:59"))

        priority_map = {"high": "Cao", "medium": "Trung bình", "low": "Thấp"}
        self.combo_priority.set(priority_map.get(task.get("priority", "medium"), "Trung bình"))

        cat_name = task.get("category_name", "")
        if cat_name and cat_name in self.cat_names:
            self.combo_category.set(cat_name)

        self.entry_assignee.insert(0, task.get("assignee", ""))

    def _save(self):
        """Validate and return task data through on_save callback."""
        title = self.entry_title.get().strip()
        if not title:
            self.entry_title.configure(border_color=self.theme["danger"])
            return

        deadline_date = self.entry_deadline_date.get().strip()
        if not deadline_date:
            self.entry_deadline_date.configure(border_color=self.theme["danger"])
            return

        # Validate date format
        try:
            datetime.strptime(deadline_date, "%Y-%m-%d")
        except ValueError:
            self.entry_deadline_date.configure(border_color=self.theme["danger"])
            return

        deadline_time = self.entry_deadline_time.get().strip() or "23:59"

        # Map priority label back to key
        label_to_key = {v["label"]: k for k, v in PRIORITY_CONFIG.items()}
        priority = label_to_key.get(self.combo_priority.get(), "medium")

        # Map category name to ID
        cat_name = self.combo_category.get()
        category_id = None
        for c in self.categories:
            if c["name"] == cat_name:
                category_id = c["id"]
                break

        data = {
            "title": title,
            "description": self.entry_desc.get("1.0", "end-1c").strip(),
            "start_date": self.entry_start_date.get().strip() or datetime.now().strftime("%Y-%m-%d"),
            "deadline_date": deadline_date,
            "deadline_time": deadline_time,
            "priority": priority,
            "category_id": category_id,
            "assignee": self.entry_assignee.get().strip(),
        }

        if self.task:
            data["id"] = self.task["id"]

        self.result = data
        if self.on_save:
            self.on_save(data)
        self.destroy()
