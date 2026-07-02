import os
import sqlite3
from datetime import datetime, timezone

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "hadiths.db")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_annotation_tables():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS annotators (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            password_salt TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            token TEXT PRIMARY KEY,
            annotator_id INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (annotator_id) REFERENCES annotators(id) ON DELETE CASCADE
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS assignments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            annotator_id INTEGER NOT NULL,
            query_id TEXT NOT NULL,
            assigned_at TEXT NOT NULL,
            UNIQUE(annotator_id, query_id),
            FOREIGN KEY (annotator_id) REFERENCES annotators(id) ON DELETE CASCADE
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS annotations (
            annotator_id INTEGER NOT NULL,
            query_id TEXT NOT NULL,
            hadith_id INTEGER NOT NULL,
            label INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            PRIMARY KEY (annotator_id, query_id, hadith_id),
            FOREIGN KEY (annotator_id) REFERENCES annotators(id) ON DELETE CASCADE
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS annotation_progress (
            annotator_id INTEGER NOT NULL,
            query_id TEXT NOT NULL,
            current_index INTEGER DEFAULT 0,
            PRIMARY KEY (annotator_id, query_id),
            FOREIGN KEY (annotator_id) REFERENCES annotators(id) ON DELETE CASCADE
        )
    """)

    conn.commit()
    conn.close()


def now_iso():
    return datetime.now(timezone.utc).isoformat()
