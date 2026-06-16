import sqlite3
import os

db_path = r'd:\VIETTEL\Python\Code\Quan ly cong viec\tasks.db'
if not os.path.exists(db_path):
    print("No db found at", db_path)
    exit(0)

conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row

# Get tables
tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
print("Tables:", tables)

# Get tasks
tasks = [dict(r) for r in conn.execute("SELECT id, title, status, deadline_date, deadline_time, notified_overdue FROM tasks").fetchall()]
print("Tasks:")
for t in tasks:
    print(t)

# Get notifications
if 'notifications' in tables:
    notifs = [dict(r) for r in conn.execute("SELECT * FROM notifications").fetchall()]
    print("Notifications:", notifs)
else:
    print("No notifications table.")

conn.close()
