import sqlite3
from contextlib import contextmanager
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS expenses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    description TEXT NOT NULL CHECK (length(trim(description)) > 0),
    amount_cents INTEGER NOT NULL CHECK (amount_cents > 0),
    category TEXT NOT NULL,
    created_on TEXT NOT NULL DEFAULT (date('now'))
);
CREATE INDEX IF NOT EXISTS idx_expenses_category ON expenses(category);
"""


def connect(path: str = "expenses.db") -> sqlite3.Connection:
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(SCHEMA)
    return conn


@contextmanager
def transaction(conn: sqlite3.Connection):
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
