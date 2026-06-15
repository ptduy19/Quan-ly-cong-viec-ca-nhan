"""
Duypt2 Task Manager — Desktop Notification Service.

Cross-platform desktop notifications using plyer.
"""
from plyer import notification as plyer_notification


class NotificationService:
    """Sends desktop toast notifications."""

    APP_NAME = "Duypt2 Task Manager"

    def send(self, title: str, message: str, urgency: str = "info", timeout: int = 10):
        """
        Send a desktop notification.

        Args:
            title: Notification title.
            message: Notification body text.
            urgency: One of 'info', 'warning', 'critical'.
            timeout: Seconds before notification auto-dismisses.
        """
        try:
            plyer_notification.notify(
                title=title,
                message=message,
                app_name=self.APP_NAME,
                timeout=timeout,
            )
        except Exception as e:
            print(f"[NotificationService] Error sending notification: {e}")
