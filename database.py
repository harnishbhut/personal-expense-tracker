"""
database.py
-----------
This file handles everything related to our SQLite database.
It creates the database file, sets up the table, and provides
helper functions to connect to the database.

SQLite is a simple file-based database — no separate server needed.
The data is stored in 'expenses.db' in the same folder as the app.
"""

import sqlite3
import os

# The name of our database file
DATABASE = "expenses.db"


def get_db_connection():
    """
    Opens a connection to the SQLite database.

    'row_factory = sqlite3.Row' lets us access columns by name
    (e.g., row['title']) instead of by index (e.g., row[1]).
    """
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  # Access columns by name
    return conn


def init_db():
    """
    Creates the 'expenses' table if it doesn't exist yet.

    This function is called once when the app starts.
    If the table already exists, nothing happens (safe to re-run).
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # Create the expenses table
    # Each column stores a specific piece of information about an expense
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            title       TEXT    NOT NULL,
            amount      REAL    NOT NULL CHECK(amount > 0),
            category    TEXT    NOT NULL,
            date        TEXT    NOT NULL,
            description TEXT,
            created_at  TEXT    DEFAULT (datetime('now'))
        )
    """)

    conn.commit()   # Save changes
    conn.close()    # Always close the connection when done
    print("[OK] Database initialized - expenses.db is ready.")
