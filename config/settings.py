"""
Duypt2 Task Manager — Application Settings & Theme Configuration.

Defines color palettes, fonts, constants, and theme tokens for the entire app.
"""
import os

# ─── App Metadata ────────────────────────────────────────────────────────────
APP_NAME = "Duypt2 Task Manager"
APP_VERSION = "2.0.0"
APP_AUTHOR = "Duypt2"
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "tasks.db")
JSON_LEGACY_PATH = os.path.join(BASE_DIR, "tasks.json")

# ─── Window Defaults ─────────────────────────────────────────────────────────
WINDOW_MIN_WIDTH = 1000
WINDOW_MIN_HEIGHT = 650
WINDOW_DEFAULT_GEOMETRY = "1200x750"
SIDEBAR_WIDTH = 220
SIDEBAR_COLLAPSED_WIDTH = 60

# ─── Fonts ────────────────────────────────────────────────────────────────────
FONT_FAMILY = "Times New Roman"
FONT_FAMILY_MONO = "Consolas"

FONT_SIZE_XS = 11
FONT_SIZE_SM = 12
FONT_SIZE_MD = 13
FONT_SIZE_LG = 15
FONT_SIZE_XL = 18
FONT_SIZE_XXL = 24
FONT_SIZE_HERO = 32

# ─── Color Palettes ──────────────────────────────────────────────────────────

# Dark theme (Option 1A: Cyberpunk/Neon with Blue accent)
DARK = {
    "bg_primary":       "#0b0e14",   # Deep navy/black
    "bg_secondary":     "#121822",
    "bg_card":          "#171e2b",
    "bg_card_hover":    "#1e2636",
    "bg_sidebar":       "#080a0f",
    "bg_input":         "#212b3d",
    "bg_modal":         "#121822",
    "border":           "#2a364d",
    "border_focus":     "#00ccff",

    "text_primary":     "#e4e6ed",
    "text_secondary":   "#8b8fa3",
    "text_muted":       "#5c5f73",
    "text_inverse":     "#0b0e14",

    "accent":           "#00ccff",   # Electric Blue (Neon Cyan)
    "accent_hover":     "#00e5ff",
    "accent_light":     "#00ccff20",

    "success":          "#39ff14",   # Neon Green
    "success_bg":       "#39ff1418",
    "warning":          "#ffff00",   # Neon Yellow
    "warning_bg":       "#ffff0018",
    "danger":           "#ff0055",   # Neon Pink/Red
    "danger_bg":        "#ff005518",
    "info":             "#00f0ff",   # Cyan
    "info_bg":          "#00f0ff18",

    "chart_bg":         "#121822",
    "scrollbar":        "#2a364d",
    "scrollbar_hover":  "#3d4d6e",
}

# Light theme (Option 1B: Playful/Candy adapted to match Blue accent)
LIGHT = {
    "bg_primary":       "#f2f5fa",
    "bg_secondary":     "#ffffff",
    "bg_card":          "#ffffff",
    "bg_card_hover":    "#eef1f7",
    "bg_sidebar":       "#ffffff",
    "bg_input":         "#e8ecf4",
    "bg_modal":         "#ffffff",
    "border":           "#d1d8e5",
    "border_focus":     "#0099ff",

    "text_primary":     "#1e2636",
    "text_secondary":   "#5c5f73",
    "text_muted":       "#8b8fa3",
    "text_inverse":     "#ffffff",

    "accent":           "#0099ff",   # Bright Blue
    "accent_hover":     "#00b3ff",
    "accent_light":     "#0099ff15",

    "success":          "#00c46a",
    "success_bg":       "#00c46a12",
    "warning":          "#f5a623",
    "warning_bg":       "#f5a62312",
    "danger":           "#f73b54",
    "danger_bg":        "#f73b5412",
    "info":             "#00b3ff",
    "info_bg":          "#00b3ff12",

    "chart_bg":         "#ffffff",
    "scrollbar":        "#cbd2e0",
    "scrollbar_hover":  "#a0aabf",
}

# ─── Priority Config ─────────────────────────────────────────────────────────
PRIORITY_CONFIG = {
    "high":   {"label": "Cao",        "color": "#ff0055", "icon": "\uf102", "order": 1},  # angles-up
    "medium": {"label": "Trung bình", "color": "#ffff00", "icon": "\uf061", "order": 2},  # arrow-right
    "low":    {"label": "Thấp",       "color": "#39ff14", "icon": "\uf103", "order": 3},  # angles-down
}

# ─── Status Config ───────────────────────────────────────────────────────────
STATUS_CONFIG = {
    "pending":      {"label": "Chưa làm",        "color": "#8b8fa3", "icon": "\uf252"},  # hourglass
    "in_progress":  {"label": "Đang thực hiện",  "color": "#00f0ff", "icon": "\uf2f1"},  # sync
    "completed":    {"label": "Hoàn thành",       "color": "#39ff14", "icon": "\uf058"},  # check-circle
    "overdue":      {"label": "Quá hạn",         "color": "#ff0055", "icon": "\uf071"},  # exclamation-triangle
}

# ─── Deadline Color Thresholds ───────────────────────────────────────────────
DEADLINE_COLORS = {
    "safe":     "#39ff14",   # Neon Green
    "warning":  "#ffff00",   # Neon Yellow
    "danger":   "#ff0055",   # Neon Red
    "urgent":   "#ff0055",
}

# ─── Default Categories ──────────────────────────────────────────────────────
DEFAULT_CATEGORIES = [
    {"name": "Cá nhân",   "color": "#ff00ff", "icon": "\uf007"},  # user
    {"name": "Công việc",  "color": "#00ccff", "icon": "\uf0b1"},  # briefcase
    {"name": "Học tập",    "color": "#39ff14", "icon": "\uf19d"},  # graduation-cap
    {"name": "Dự án",      "color": "#ffff00", "icon": "\uf135"},  # rocket
]

# ─── Navigation Items ────────────────────────────────────────────────────────
NAV_ITEMS = [
    {"id": "dashboard",  "label": "Dashboard",   "icon": "\uf080", "color": "#00ccff"},  # chart-bar
    {"id": "tasks",      "label": "Công việc",    "icon": "\uf0ae", "color": "#39ff14"},  # tasks
    {"id": "calendar",   "label": "Lịch",         "icon": "\uf133", "color": "#ffff00"},  # calendar-days
    {"id": "search",     "label": "Tìm kiếm",     "icon": "\uf002", "color": "#ff00ff"},  # magnifying-glass
    {"id": "settings",   "label": "Cài đặt",      "icon": "\uf013", "color": "#ff0055"},  # gear
]

# ─── Notification Settings ───────────────────────────────────────────────────
NOTIFY_BEFORE_1DAY = True
NOTIFY_BEFORE_1HOUR = True
NOTIFY_ON_OVERDUE = True
DEADLINE_CHECK_INTERVAL_SECONDS = 30
