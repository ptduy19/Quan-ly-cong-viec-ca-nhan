"""
Duypt2 Task Manager — SQLite Database Manager.

Thread-safe singleton database manager with auto-migration from legacy JSON.
"""
import sqlite3
import threading
import json
import os
from datetime import datetime

from config.settings import DB_PATH, JSON_LEGACY_PATH, DEFAULT_CATEGORIES


class DatabaseManager:
    """Thread-safe SQLite database manager using connection-per-thread pattern."""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._local = threading.local()
        self._db_path = DB_PATH
        self._init_database()

    def _get_connection(self) -> sqlite3.Connection:
        """Get a thread-local database connection."""
        if not hasattr(self._local, "connection") or self._local.connection is None:
            conn = sqlite3.connect(self._db_path)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA foreign_keys=ON")
            self._local.connection = conn
        return self._local.connection

    @property
    def conn(self) -> sqlite3.Connection:
        return self._get_connection()

    def execute(self, query: str, params: tuple = ()) -> sqlite3.Cursor:
        """Execute a single query with automatic commit."""
        cursor = self.conn.execute(query, params)
        self.conn.commit()
        return cursor

    def executemany(self, query: str, params_list: list) -> sqlite3.Cursor:
        """Execute a query for multiple parameter sets."""
        cursor = self.conn.executemany(query, params_list)
        self.conn.commit()
        return cursor

    def fetchone(self, query: str, params: tuple = ()) -> dict | None:
        """Fetch a single row as a dictionary."""
        cursor = self.conn.execute(query, params)
        row = cursor.fetchone()
        return dict(row) if row else None

    def fetchall(self, query: str, params: tuple = ()) -> list[dict]:
        """Fetch all rows as a list of dictionaries."""
        cursor = self.conn.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]

    def _init_database(self):
        """Create tables if they don't exist, then seed defaults."""
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                username    TEXT UNIQUE NOT NULL,
                display_name TEXT DEFAULT '',
                theme       TEXT DEFAULT 'dark',
                created_at  TEXT DEFAULT (datetime('now','localtime'))
            );

            CREATE TABLE IF NOT EXISTS categories (
                id    INTEGER PRIMARY KEY AUTOINCREMENT,
                name  TEXT UNIQUE NOT NULL,
                color TEXT DEFAULT '#3498db',
                icon  TEXT DEFAULT '📁'
            );

            CREATE TABLE IF NOT EXISTS tasks (
                id               INTEGER PRIMARY KEY AUTOINCREMENT,
                title            TEXT NOT NULL,
                description      TEXT DEFAULT '',
                start_date       TEXT,
                deadline_date    TEXT NOT NULL,
                deadline_time    TEXT NOT NULL DEFAULT '23:59',
                priority         TEXT CHECK(priority IN ('high','medium','low')) DEFAULT 'medium',
                status           TEXT CHECK(status IN ('pending','in_progress','completed','overdue')) DEFAULT 'pending',
                progress         INTEGER DEFAULT 0 CHECK(progress >= 0 AND progress <= 100),
                category_id      INTEGER REFERENCES categories(id) ON DELETE SET NULL,
                assignee         TEXT DEFAULT '',
                user_id          INTEGER REFERENCES users(id) ON DELETE CASCADE,
                recurrence       TEXT CHECK(recurrence IN ('none', 'daily', 'weekly', 'monthly')) DEFAULT 'none',
                notified_1day    INTEGER DEFAULT 0,
                notified_1hour   INTEGER DEFAULT 0,
                notified_overdue INTEGER DEFAULT 0,
                created_at       TEXT DEFAULT (datetime('now','localtime')),
                updated_at       TEXT DEFAULT (datetime('now','localtime'))
            );

            CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
            CREATE INDEX IF NOT EXISTS idx_tasks_deadline ON tasks(deadline_date);
            CREATE INDEX IF NOT EXISTS idx_tasks_priority ON tasks(priority);
            CREATE INDEX IF NOT EXISTS idx_tasks_category ON tasks(category_id);

            CREATE TABLE IF NOT EXISTS notifications (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                title       TEXT NOT NULL,
                message     TEXT NOT NULL,
                urgency     TEXT DEFAULT 'info',
                is_read     INTEGER DEFAULT 0,
                created_at  TEXT DEFAULT (datetime('now','localtime'))
            );
        """)

        # Add 'recurrence' column if missing (auto-migration for existing DBs)
        try:
            self.conn.execute("ALTER TABLE tasks ADD COLUMN recurrence TEXT CHECK(recurrence IN ('none', 'daily', 'weekly', 'monthly')) DEFAULT 'none'")
            self.conn.commit()
        except sqlite3.OperationalError:
            pass # Column already exists

        # Seed default categories if empty
        count = self.fetchone("SELECT COUNT(*) as cnt FROM categories")
        if count and count["cnt"] == 0:
            for cat in DEFAULT_CATEGORIES:
                self.execute(
                    "INSERT OR IGNORE INTO categories (name, color, icon) VALUES (?, ?, ?)",
                    (cat["name"], cat["color"], cat["icon"])
                )

        # Seed default user if empty
        count = self.fetchone("SELECT COUNT(*) as cnt FROM users")
        if count and count["cnt"] == 0:
            self.execute(
                "INSERT INTO users (username, display_name, theme) VALUES (?, ?, ?)",
                ("duypt2", "Duypt2", "dark")
            )

        # Migrate legacy JSON data
        self._migrate_from_json()

    def _migrate_from_json(self):
        """Migrate tasks from legacy tasks.json file if it exists."""
        if not os.path.exists(JSON_LEGACY_PATH):
            return

        try:
            with open(JSON_LEGACY_PATH, "r", encoding="utf-8") as f:
                legacy_tasks = json.load(f)
        except (json.JSONDecodeError, Exception):
            return

        if not legacy_tasks:
            return

        # Check if migration already happened
        existing = self.fetchone("SELECT COUNT(*) as cnt FROM tasks")
        if existing and existing["cnt"] > 0:
            return

        # Get default user and category
        user = self.fetchone("SELECT id FROM users LIMIT 1")
        category = self.fetchone("SELECT id FROM categories WHERE name = 'Công việc'")
        user_id = user["id"] if user else 1
        cat_id = category["id"] if category else 2

        for task in legacy_tasks:
            try:
                # Convert DD/MM/YYYY → YYYY-MM-DD
                date_parts = task.get("date", "").split("/")
                if len(date_parts) == 3:
                    iso_date = f"{date_parts[2]}-{date_parts[1]}-{date_parts[0]}"
                else:
                    iso_date = datetime.now().strftime("%Y-%m-%d")

                status = task.get("status", "pending")
                if status == "completed":
                    progress = 100
                else:
                    progress = task.get("progress", 0)

                self.execute(
                    """INSERT INTO tasks
                       (title, deadline_date, deadline_time, progress, assignee,
                        status, category_id, user_id, priority, recurrence)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        task.get("name", "Untitled"),
                        iso_date,
                        task.get("time", "23:59"),
                        progress,
                        task.get("reporter", ""),
                        status,
                        cat_id,
                        user_id,
                        "medium",
                        "none",
                    )
                )
            except Exception as e:
                print(f"Migration error for task: {e}")

        # Rename old file to prevent re-migration
        backup_path = JSON_LEGACY_PATH + ".migrated"
        try:
            os.rename(JSON_LEGACY_PATH, backup_path)
        except OSError:
            pass

    def close(self):
        """Close the thread-local connection."""
        if hasattr(self._local, "connection") and self._local.connection:
            self._local.connection.close()
            self._local.connection = None
