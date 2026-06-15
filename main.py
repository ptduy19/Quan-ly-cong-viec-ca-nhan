"""
Duypt2 Task Manager — Application Entry Point.

Initializes the database, starts the deadline checker, and launches the main window.

Usage:
    python main.py
"""
import sys
import os

# Ensure the project root is in the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models.database import DatabaseManager
from services.deadline_service import DeadlineService
from views.main_window import MainWindow


def main():
    """Initialize and run the Duypt2 Task Manager application."""
    # 1. Initialize database (creates tables, migrates legacy data)
    print("[Duypt2] Initializing database...")
    db = DatabaseManager()

    # 2. Start background deadline checker
    print("[Duypt2] Starting deadline checker...")
    deadline_service = DeadlineService(check_interval=30)
    deadline_service.start()

    # 3. Launch the main window
    print("[Duypt2] Launching application...")
    app = MainWindow()

    try:
        app.mainloop()
    finally:
        # Cleanup
        print("[Duypt2] Shutting down...")
        deadline_service.stop()
        db.close()


if __name__ == "__main__":
    main()
