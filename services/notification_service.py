"""
Duypt2 Task Manager — Desktop Notification Service.

Cross-platform desktop notifications using plyer.
"""
from plyer import notification as plyer_notification
from models.notification_model import NotificationModel


class NotificationService:
    """Sends desktop toast notifications and saves them to history."""

    APP_NAME = "Duypt2 Task Manager"

    def __init__(self):
        self.notification_model = NotificationModel()

    def send(self, title: str, message: str, urgency: str = "info", timeout: int = 10):
        """
        Send a desktop notification and persist it to history.

        Args:
            title: Notification title.
            message: Notification body text.
            urgency: One of 'info', 'warning', 'critical'.
            timeout: Seconds before notification auto-dismisses.
        """
        # 1. Persist to history
        try:
            self.notification_model.add_notification(title, message, urgency)
        except Exception as e:
            print(f"[NotificationService] Error saving notification to db: {e}")

        # 2. Show desktop popup
        try:
            plyer_notification.notify(
                title=title,
                message=message,
                app_name=self.APP_NAME,
                timeout=timeout,
            )
        except Exception as e:
            print(f"[NotificationService] Error sending notification popup: {e}")
