import sqlite3
from pathlib import Path

# Database file path (data folder ke andar)
DB_PATH = Path(__file__).resolve().parent.parent / "data" / "jobs.db"


def init_db():
    """Database aur table banata hai agar pehle se nahi hai."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            company TEXT,
            location TEXT,
            job_type TEXT,
            requirements TEXT,
            apply_link TEXT UNIQUE,
            source TEXT,
            date_fetched TEXT
        )
    """)

    conn.commit()
    conn.close()
    print("Database ready:", DB_PATH)


if __name__ == "__main__":
    init_db()