"""
Duypt2 Task Manager — Deadline Checker Service.

Background thread that monitors task deadlines and triggers notifications.
"""
import threading
import time
from datetime import datetime

from models.task_model import TaskModel
from services.notification_service import NotificationService


class DeadlineService:
    """Background service that checks deadlines and sends notifications."""

    def __init__(self, check_interval: int = 30):
        self.task_model = TaskModel()
        self.notifier = NotificationService()
        self.check_interval = check_interval
        self.running = False
        self._thread = None

    def start(self):
        """Start the background deadline checking thread."""
        if self.running:
            return
        self.running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def stop(self):
        """Stop the background thread."""
        self.running = False

    def _run_loop(self):
        """Main loop — checks deadlines every `check_interval` seconds."""
        while self.running:
            try:
                self._check_all_deadlines()
            except Exception as e:
                print(f"[DeadlineService] Error: {e}")

            # Sleep in 1-second intervals so we can exit quickly
            for _ in range(self.check_interval):
                if not self.running:
                    break
                time.sleep(1)

    def _check_all_deadlines(self):
        """Check all active tasks for upcoming or missed deadlines."""
        # Auto-mark overdue tasks
        self.task_model.auto_mark_overdue()

        # Get all non-completed tasks
        tasks = self.task_model.get_all_tasks()
        now = datetime.now()

        for task in tasks:
            if task["status"] == "completed":
                continue

            try:
                deadline = datetime.strptime(
                    f"{task['deadline_date']} {task['deadline_time']}",
                    "%Y-%m-%d %H:%M"
                )
            except (ValueError, TypeError):
                continue

            diff = deadline - now
            total_seconds = diff.total_seconds()

            # Milestone 1: 1 day before (notify once)
            if 0 < total_seconds <= 86400 and not task.get("notified_1day"):
                hours_left = int(total_seconds // 3600)
                self.notifier.send(
                    title="📅 Sắp đến hạn",
                    message=f"{task['title']} — còn {hours_left} giờ nữa",
                    urgency="warning"
                )
                self.task_model.update_task(task["id"], notified_1day=1)

            # Milestone 2: 1 hour before (notify once)
            elif 0 < total_seconds <= 3600 and not task.get("notified_1hour"):
                mins_left = int(total_seconds // 60)
                self.notifier.send(
                    title="⚠️ Gấp!",
                    message=f"{task['title']} — chỉ còn {mins_left} phút!",
                    urgency="critical"
                )
                self.task_model.update_task(task["id"], notified_1hour=1)

            # Milestone 3: Overdue (notify once)
            elif total_seconds <= 0 and not task.get("notified_overdue"):
                self.notifier.send(
                    title="🔴 Quá hạn!",
                    message=f"{task['title']} đã quá deadline!",
                    urgency="critical"
                )
                self.task_model.update_task(task["id"], notified_overdue=1)
