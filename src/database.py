import sqlite3
from pathlib import Path

# Database file path (data folder ke andar)
DB_PATH = Path(__file__).resolve().parent.parent / "data" / "jobs.db"

def insert_jobs(jobs):
    """Fetch ki hui jobs ko database mein save karta hai (duplicates skip ho jayenge)."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    new_count = 0
    for job in jobs:
        try:
            cursor.execute("""
                INSERT INTO jobs (title, company, location, job_type, requirements, apply_link, source, date_fetched)
                VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'))
            """, (
                job.get("title"),
                job.get("company_name"),
                job.get("location"),
                ", ".join(job.get("job_types", [])),
                job.get("description"),
                job.get("url"),
                "Arbeitnow"
            ))
            new_count += 1
        except sqlite3.IntegrityError:
            # apply_link pehle se maujood hai — duplicate, skip karo
            pass

    conn.commit()
    conn.close()
    print(f"{new_count} nayi jobs save hui")


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