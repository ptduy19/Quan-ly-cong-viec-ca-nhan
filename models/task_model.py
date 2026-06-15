"""
Duypt2 Task Manager — Task Model.

Full CRUD operations for tasks with advanced querying capabilities.
"""
from datetime import datetime, timedelta

from models.database import DatabaseManager


class TaskModel:
    """Handles all task-related database operations."""

    def __init__(self):
        self.db = DatabaseManager()

    # ── Create ────────────────────────────────────────────────────────────────

    def create_task(self, title: str, deadline_date: str, deadline_time: str = "23:59",
                    description: str = "", start_date: str = None, priority: str = "medium",
                    category_id: int = None, assignee: str = "", user_id: int = 1,
                    status: str = "pending", progress: int = 0) -> dict:
        """Create a new task and return it as a dictionary."""
        if start_date is None:
            start_date = datetime.now().strftime("%Y-%m-%d")

        cursor = self.db.execute(
            """INSERT INTO tasks
               (title, description, start_date, deadline_date, deadline_time,
                priority, status, progress, category_id, assignee, user_id)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (title, description, start_date, deadline_date, deadline_time,
             priority, status, progress, category_id, assignee, user_id)
        )
        return self.get_task(cursor.lastrowid)

    # ── Read ──────────────────────────────────────────────────────────────────

    def get_task(self, task_id: int) -> dict | None:
        """Get a single task by ID, with category info joined."""
        return self.db.fetchone(
            """SELECT t.*, c.name as category_name, c.color as category_color, c.icon as category_icon
               FROM tasks t
               LEFT JOIN categories c ON t.category_id = c.id
               WHERE t.id = ?""",
            (task_id,)
        )

    def get_all_tasks(self, user_id: int = None, status: str = None,
                      priority: str = None, category_id: int = None,
                      order_by: str = "deadline_date ASC") -> list[dict]:
        """Get tasks with optional filtering and ordering."""
        query = """SELECT t.*, c.name as category_name, c.color as category_color, c.icon as category_icon
                   FROM tasks t
                   LEFT JOIN categories c ON t.category_id = c.id
                   WHERE 1=1"""
        params = []

        if user_id is not None:
            query += " AND t.user_id = ?"
            params.append(user_id)
        if status is not None:
            query += " AND t.status = ?"
            params.append(status)
        if priority is not None:
            query += " AND t.priority = ?"
            params.append(priority)
        if category_id is not None:
            query += " AND t.category_id = ?"
            params.append(category_id)

        # Sanitize order_by to prevent SQL injection
        allowed_orders = {
            "deadline_date ASC", "deadline_date DESC",
            "priority ASC", "priority DESC",
            "created_at ASC", "created_at DESC",
            "title ASC", "title DESC",
            "progress ASC", "progress DESC",
        }
        if order_by not in allowed_orders:
            order_by = "deadline_date ASC"

        query += f" ORDER BY {order_by}"
        return self.db.fetchall(query, tuple(params))

    def get_tasks_today(self) -> list[dict]:
        """Get all tasks due today."""
        today = datetime.now().strftime("%Y-%m-%d")
        return self.db.fetchall(
            """SELECT t.*, c.name as category_name, c.color as category_color, c.icon as category_icon
               FROM tasks t
               LEFT JOIN categories c ON t.category_id = c.id
               WHERE t.deadline_date = ? AND t.status != 'completed'
               ORDER BY t.deadline_time ASC""",
            (today,)
        )

    def get_tasks_due_soon(self, days: int = 3) -> list[dict]:
        """Get tasks due within the next N days (not completed)."""
        today = datetime.now().strftime("%Y-%m-%d")
        future = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")
        return self.db.fetchall(
            """SELECT t.*, c.name as category_name, c.color as category_color, c.icon as category_icon
               FROM tasks t
               LEFT JOIN categories c ON t.category_id = c.id
               WHERE t.deadline_date BETWEEN ? AND ?
                 AND t.status NOT IN ('completed')
               ORDER BY t.deadline_date ASC, t.deadline_time ASC""",
            (today, future)
        )

    def get_overdue_tasks(self) -> list[dict]:
        """Get all overdue tasks (past deadline, not completed)."""
        now = datetime.now()
        today = now.strftime("%Y-%m-%d")
        current_time = now.strftime("%H:%M")
        return self.db.fetchall(
            """SELECT t.*, c.name as category_name, c.color as category_color, c.icon as category_icon
               FROM tasks t
               LEFT JOIN categories c ON t.category_id = c.id
               WHERE t.status NOT IN ('completed')
                 AND (t.deadline_date < ? OR (t.deadline_date = ? AND t.deadline_time < ?))
               ORDER BY t.deadline_date ASC""",
            (today, today, current_time)
        )

    def get_completed_tasks(self, limit: int = 50) -> list[dict]:
        """Get recently completed tasks."""
        return self.db.fetchall(
            """SELECT t.*, c.name as category_name, c.color as category_color, c.icon as category_icon
               FROM tasks t
               LEFT JOIN categories c ON t.category_id = c.id
               WHERE t.status = 'completed'
               ORDER BY t.updated_at DESC
               LIMIT ?""",
            (limit,)
        )

    def get_tasks_by_date(self, date_str: str) -> list[dict]:
        """Get all tasks for a specific date (YYYY-MM-DD)."""
        return self.db.fetchall(
            """SELECT t.*, c.name as category_name, c.color as category_color, c.icon as category_icon
               FROM tasks t
               LEFT JOIN categories c ON t.category_id = c.id
               WHERE t.deadline_date = ?
               ORDER BY t.deadline_time ASC""",
            (date_str,)
        )

    def get_tasks_in_range(self, start_date: str, end_date: str) -> list[dict]:
        """Get tasks within a date range (for calendar view)."""
        return self.db.fetchall(
            """SELECT t.*, c.name as category_name, c.color as category_color, c.icon as category_icon
               FROM tasks t
               LEFT JOIN categories c ON t.category_id = c.id
               WHERE t.deadline_date BETWEEN ? AND ?
               ORDER BY t.deadline_date ASC, t.deadline_time ASC""",
            (start_date, end_date)
        )

    # ── Update ────────────────────────────────────────────────────────────────

    def update_task(self, task_id: int, **kwargs) -> dict | None:
        """Update task fields dynamically. Only whitelisted fields are allowed."""
        allowed_fields = {
            "title", "description", "start_date", "deadline_date", "deadline_time",
            "priority", "status", "progress", "category_id", "assignee",
            "notified_1day", "notified_1hour", "notified_overdue"
        }
        updates = {k: v for k, v in kwargs.items() if k in allowed_fields}
        if not updates:
            return self.get_task(task_id)

        updates["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        set_clause = ", ".join(f"{k} = ?" for k in updates)
        values = list(updates.values()) + [task_id]

        self.db.execute(f"UPDATE tasks SET {set_clause} WHERE id = ?", tuple(values))
        return self.get_task(task_id)

    def mark_completed(self, task_id: int) -> dict | None:
        """Mark a task as completed with progress = 100."""
        return self.update_task(task_id, status="completed", progress=100)

    def update_progress(self, task_id: int, progress: int) -> dict | None:
        """Update task progress. Auto-complete if progress >= 100."""
        progress = max(0, min(100, progress))
        status = "completed" if progress >= 100 else None
        kwargs = {"progress": progress}
        if status:
            kwargs["status"] = status
        return self.update_task(task_id, **kwargs)

    def move_task_to_date(self, task_id: int, new_date: str) -> dict | None:
        """Move a task to a new deadline date (for calendar drag)."""
        return self.update_task(task_id, deadline_date=new_date)

    # ── Delete ────────────────────────────────────────────────────────────────

    def delete_task(self, task_id: int) -> bool:
        """Delete a task by ID."""
        cursor = self.db.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        return cursor.rowcount > 0

    # ── Duplicate ─────────────────────────────────────────────────────────────

    def duplicate_task(self, task_id: int) -> dict | None:
        """Create a copy of an existing task with reset status."""
        original = self.get_task(task_id)
        if not original:
            return None
        return self.create_task(
            title=f"{original['title']} (bản sao)",
            description=original.get("description", ""),
            start_date=datetime.now().strftime("%Y-%m-%d"),
            deadline_date=original["deadline_date"],
            deadline_time=original["deadline_time"],
            priority=original["priority"],
            category_id=original.get("category_id"),
            assignee=original.get("assignee", ""),
            user_id=original.get("user_id", 1),
        )

    # ── Search ────────────────────────────────────────────────────────────────

    def search_tasks(self, query: str, status: str = None,
                     priority: str = None, category_id: int = None) -> list[dict]:
        """Full-text search across title, description, and assignee."""
        sql = """SELECT t.*, c.name as category_name, c.color as category_color, c.icon as category_icon
                 FROM tasks t
                 LEFT JOIN categories c ON t.category_id = c.id
                 WHERE (t.title LIKE ? OR t.description LIKE ? OR t.assignee LIKE ?)"""
        params = [f"%{query}%", f"%{query}%", f"%{query}%"]

        if status:
            sql += " AND t.status = ?"
            params.append(status)
        if priority:
            sql += " AND t.priority = ?"
            params.append(priority)
        if category_id:
            sql += " AND t.category_id = ?"
            params.append(category_id)

        sql += " ORDER BY t.deadline_date ASC"
        return self.db.fetchall(sql, tuple(params))

    # ── Statistics ────────────────────────────────────────────────────────────

    def get_stats(self) -> dict:
        """Get task statistics for the dashboard."""
        today = datetime.now().strftime("%Y-%m-%d")
        current_time = datetime.now().strftime("%H:%M")

        total = self.db.fetchone("SELECT COUNT(*) as cnt FROM tasks")["cnt"]
        pending = self.db.fetchone(
            "SELECT COUNT(*) as cnt FROM tasks WHERE status = 'pending'"
        )["cnt"]
        in_progress = self.db.fetchone(
            "SELECT COUNT(*) as cnt FROM tasks WHERE status = 'in_progress'"
        )["cnt"]
        completed = self.db.fetchone(
            "SELECT COUNT(*) as cnt FROM tasks WHERE status = 'completed'"
        )["cnt"]
        overdue = self.db.fetchone(
            """SELECT COUNT(*) as cnt FROM tasks
               WHERE status NOT IN ('completed')
                 AND (deadline_date < ? OR (deadline_date = ? AND deadline_time < ?))""",
            (today, today, current_time)
        )["cnt"]
        today_count = self.db.fetchone(
            "SELECT COUNT(*) as cnt FROM tasks WHERE deadline_date = ? AND status != 'completed'",
            (today,)
        )["cnt"]
        due_soon = self.db.fetchone(
            """SELECT COUNT(*) as cnt FROM tasks
               WHERE deadline_date BETWEEN ? AND ?
                 AND status NOT IN ('completed')""",
            (today, (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d"))
        )["cnt"]

        return {
            "total": total,
            "pending": pending,
            "in_progress": in_progress,
            "completed": completed,
            "overdue": overdue,
            "today": today_count,
            "due_soon": due_soon,
        }

    def get_weekly_stats(self) -> list[dict]:
        """Get completion stats for the last 7 days (for bar chart)."""
        results = []
        for i in range(6, -1, -1):
            date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            day_label = (datetime.now() - timedelta(days=i)).strftime("%a")
            completed = self.db.fetchone(
                "SELECT COUNT(*) as cnt FROM tasks WHERE status='completed' AND DATE(updated_at)=?",
                (date,)
            )["cnt"]
            total = self.db.fetchone(
                "SELECT COUNT(*) as cnt FROM tasks WHERE deadline_date = ?",
                (date,)
            )["cnt"]
            results.append({"date": date, "day": day_label, "completed": completed, "total": total})
        return results

    # ── Auto-update overdue ──────────────────────────────────────────────────

    def auto_mark_overdue(self):
        """Automatically mark past-deadline tasks as overdue."""
        now = datetime.now()
        today = now.strftime("%Y-%m-%d")
        current_time = now.strftime("%H:%M")
        self.db.execute(
            """UPDATE tasks SET status = 'overdue', updated_at = datetime('now','localtime')
               WHERE status IN ('pending', 'in_progress')
                 AND (deadline_date < ? OR (deadline_date = ? AND deadline_time < ?))""",
            (today, today, current_time)
        )
