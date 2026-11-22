"""
Database initialization and connection management.
"""
import sqlite3
import os
from contextlib import contextmanager
from config import Config


@contextmanager
def get_db():
    """
    Context manager for database connections.
    [FIX M3] Guarantees connection is always closed, even on errors.

    Usage:
        with get_db() as db:
            db.execute(...)
    """
    conn = sqlite3.connect(Config.DATABASE_PATH, timeout=15)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA synchronous = NORMAL")
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
    finally:
        conn.close()


def init_db():
    """Initialize the database with all required tables."""
    with get_db() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS admin (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username VARCHAR(50) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                email VARCHAR(100),
                must_change_password INTEGER DEFAULT 1
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS classes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                class_name VARCHAR(50) NOT NULL,
                section VARCHAR(10) NOT NULL,
                UNIQUE(class_name, section)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(100) NOT NULL,
                roll_no VARCHAR(20) UNIQUE NOT NULL,
                class_id INTEGER NOT NULL,
                photo_path VARCHAR(255) NOT NULL,
                face_encoding BLOB NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (class_id) REFERENCES classes(id) ON DELETE CASCADE
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS attendance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                date DATE NOT NULL,
                time TIME NOT NULL,
                status VARCHAR(10) DEFAULT 'Present',
                FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
                UNIQUE(student_id, date)
            )
        """)

        conn.commit()

    os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
