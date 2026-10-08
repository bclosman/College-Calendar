import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "database.db"

def get_connection():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    connection = get_connection()

    try:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS assignments (
                id INTEGER PRIMARY KEY,
                course_id INTEGER NOT NULL,
                course_name TEXT NOT NULL,
                name TEXT NOT NULL,
                due_at TEXT,
                submitted INTEGER NOT NULL DEFAULT 0,
                url TEXT
            )
        """)

        connection.commit()
    finally:
        connection.close()


def save_assignment(assignment):
    conn = get_connection()

    try:
        conn.execute("""
            INSERT INTO assignments (
                id, course_id, course_name,
                name, due_at, submitted, url
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                course_id = excluded.course_id,
                course_name = excluded.course_name,
                name = excluded.name,
                due_at = excluded.due_at,
                submitted = excluded.submitted,
                url = excluded.url
        """, (
            assignment["id"],
            assignment["course_id"],
            assignment["course_name"],
            assignment["name"],
            assignment["due_at"],
            assignment["submitted"],
            assignment["url"]
        ))

        conn.commit()
    finally:
        conn.close()

def get_assignments(
    course_id: int | None = None,
    start: str | None = None,
    end: str | None = None,
    submitted: bool | None = None,
    limit: int = 100
):
    if not 1 <= limit <= 500:
        raise ValueError("Limit must be between 1 and 500")

    query = "SELECT * FROM assignments"
    conditions = ["due_at IS NOT NULL"]
    params = []

    if course_id is not None:
        conditions.append("course_id = ?")
        params.append(course_id)

    if start is not None:
        conditions.append("due_at >= ?")
        params.append(start)

    if end is not None:
        conditions.append("due_at <= ?")
        params.append(end)

    if submitted is not None:
        conditions.append("submitted = ?")
        params.append((int)(submitted))

    query += " WHERE " + " AND ".join(conditions)
    query += " ORDER BY due_at ASC LIMIT ?"
    params.append(limit)

    connection = get_connection()
    try:
        rows = connection.execute(query, params).fetchall()
        return [dict(row) for row in rows]
    finally:
        connection.close()

def save_event(event):
    pass