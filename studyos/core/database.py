import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "studyos.db")

def get_connection():
    db_dir = os.path.dirname(DB_PATH)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS subjects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        mastery_percentage INTEGER NOT NULL CHECK(mastery_percentage >= 0 AND mastery_percentage <= 100),
        importance TEXT NOT NULL,
        exam_date TEXT
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        subject_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        task_type TEXT NOT NULL,
        deadline TEXT NOT NULL,
        total_duration_minutes INTEGER NOT NULL,
        remaining_minutes INTEGER NOT NULL,
        importance TEXT NOT NULL,
        status TEXT NOT NULL,
        FOREIGN KEY (subject_id) REFERENCES subjects (id)
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS student_profile (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        available_minutes_per_day INTEGER NOT NULL
    )
    ''')

    conn.commit()
    conn.close()
    print("Database initialized successfully.")

if __name__ == "__main__":
    init_db()