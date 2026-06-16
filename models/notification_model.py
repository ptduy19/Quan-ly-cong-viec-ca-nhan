"""
Duypt2 Task Manager — Notification Model.

Handles database operations for notifications.
"""
from models.database import DatabaseManager


class NotificationModel:
    """CRUD operations for notifications table."""

    def __init__(self):
        self.db = DatabaseManager()

    def get_all_notifications(self, limit: int = 100) -> list[dict]:
        """Fetch notifications, ordered by newest first."""
        query = "SELECT * FROM notifications ORDER BY created_at DESC LIMIT ?"
        return self.db.fetchall(query, (limit,))

    def get_unread_count(self) -> int:
        """Get the count of unread notifications."""
        query = "SELECT COUNT(*) as cnt FROM notifications WHERE is_read = 0"
        result = self.db.fetchone(query)
        return result["cnt"] if result else 0

    def add_notification(self, title: str, message: str, urgency: str = "info") -> int:
        """Add a new notification."""
        query = """
            INSERT INTO notifications (title, message, urgency)
            VALUES (?, ?, ?)
        """
        cursor = self.db.execute(query, (title, message, urgency))
        return cursor.lastrowid

    def mark_as_read(self, notification_id: int):
        """Mark a specific notification as read."""
        query = "UPDATE notifications SET is_read = 1 WHERE id = ?"
        self.db.execute(query, (notification_id,))

    def mark_all_as_read(self):
        """Mark all notifications as read."""
        query = "UPDATE notifications SET is_read = 1 WHERE is_read = 0"
        self.db.execute(query)

    def delete_notification(self, notification_id: int):
        """Delete a notification."""
        query = "DELETE FROM notifications WHERE id = ?"
        self.db.execute(query, (notification_id,))

    def clear_all(self):
        """Delete all notifications."""
        query = "DELETE FROM notifications"
        self.db.execute(query)
