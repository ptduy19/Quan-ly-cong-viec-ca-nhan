"""
Duypt2 Task Manager — User Model.

Local user profile management (no remote auth — local-only).
"""
from models.database import DatabaseManager


class UserModel:
    """Handles local user profile operations."""

    def __init__(self):
        self.db = DatabaseManager()

    def get_default_user(self) -> dict | None:
        """Get the default (first) user profile."""
        return self.db.fetchone("SELECT * FROM users ORDER BY id LIMIT 1")

    def get_user(self, user_id: int) -> dict | None:
        return self.db.fetchone("SELECT * FROM users WHERE id = ?", (user_id,))

    def update_theme(self, user_id: int, theme: str) -> dict | None:
        """Update user's theme preference ('dark' or 'light')."""
        if theme not in ("dark", "light"):
            theme = "dark"
        self.db.execute(
            "UPDATE users SET theme = ? WHERE id = ?", (theme, user_id)
        )
        return self.get_user(user_id)

    def update_display_name(self, user_id: int, display_name: str) -> dict | None:
        self.db.execute(
            "UPDATE users SET display_name = ? WHERE id = ?", (display_name, user_id)
        )
        return self.get_user(user_id)
