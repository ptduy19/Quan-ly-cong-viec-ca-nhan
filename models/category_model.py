"""
Duypt2 Task Manager — Category Model.

CRUD operations for task categories/groups.
"""
from models.database import DatabaseManager


class CategoryModel:
    """Handles category/group database operations."""

    def __init__(self):
        self.db = DatabaseManager()

    def get_all(self) -> list[dict]:
        """Get all categories with task counts."""
        return self.db.fetchall(
            """SELECT c.*, COUNT(t.id) as task_count
               FROM categories c
               LEFT JOIN tasks t ON t.category_id = c.id
               GROUP BY c.id
               ORDER BY c.name"""
        )

    def get_by_id(self, category_id: int) -> dict | None:
        return self.db.fetchone("SELECT * FROM categories WHERE id = ?", (category_id,))

    def create(self, name: str, color: str = "#3498db", icon: str = "📁") -> dict | None:
        cursor = self.db.execute(
            "INSERT OR IGNORE INTO categories (name, color, icon) VALUES (?, ?, ?)",
            (name, color, icon)
        )
        if cursor.lastrowid:
            return self.get_by_id(cursor.lastrowid)
        return None

    def update(self, category_id: int, name: str = None,
               color: str = None, icon: str = None) -> dict | None:
        current = self.get_by_id(category_id)
        if not current:
            return None
        self.db.execute(
            "UPDATE categories SET name=?, color=?, icon=? WHERE id=?",
            (name or current["name"], color or current["color"],
             icon or current["icon"], category_id)
        )
        return self.get_by_id(category_id)

    def delete(self, category_id: int) -> bool:
        cursor = self.db.execute("DELETE FROM categories WHERE id = ?", (category_id,))
        return cursor.rowcount > 0
