import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "database.db"

def get_connection():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    connection = get_connection()

    try:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS assignments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                uid TEXT NOT NULL UNIQUE,
                course_id INTEGER NOT NULL,
                course_name TEXT NOT NULL,
                name TEXT NOT NULL,
                due_at TEXT,
                submitted INTEGER NOT NULL DEFAULT 0,
                url TEXT
            )
        """)

        connection.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                uid TEXT NOT NULL UNIQUE,
                calendar TEXT NOT NULL,
                name TEXT NOT NULL,
                start TEXT,
                end TEXT,
                url TEXT,
                UNIQUE(calendar, uid)
            )
        """)

        connection.commit()
    finally:
        connection.close()


def save_assignment(assignment):
    connection = get_connection()

    try:
        connection.execute("""
            INSERT INTO assignments (
                uid, course_id, course_name,
                name, due_at, submitted, url
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(uid) DO UPDATE SET
                course_id = excluded.course_id,
                course_name = excluded.course_name,
                name = excluded.name,
                due_at = excluded.due_at,
                url = excluded.url
            """, (
                assignment["uid"],
                assignment["course_id"],
                assignment["course_name"],
                assignment["name"],
                assignment["due_at"],
                int(assignment.get("submitted", False)),
                assignment["url"]
            ))

        connection.commit()
    finally:
        connection.close()


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

def print_assignments():
    connection = get_connection()

    rows = connection.execute("SELECT * FROM assignments").fetchall()

    for row in rows:
        print(dict(row))

    connection.close()

def save_event(event):
    connection = get_connection()

    try:
        connection.execute("""
            INSERT INTO events (
                uid, calendar, name,
                start, end, url
            )
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(uid) DO UPDATE SET
                calendar = excluded.calendar,
                name = excluded.name,
                start = excluded.start,
                end = excluded.end,
                url = excluded.url
            """, (
                event["uid"],
                event["calendar"],
                event["name"],
                event["start"],
                event["end"],
                event["url"]
            ))
        
        connection.commit()
    finally:
        connection.close()

def get_events(
    calendar: str | None = None,
    name: str | None = None,
    start: str | None = None,
    end: str | None = None,
    limit: int = 100
):
    if not 1 <= limit <= 500:
        raise ValueError("Limit must be between 1 and 500")

    query = "SELECT * FROM assignments"
    conditions = ["due_at IS NOT NULL"]
    params = []

    if calendar is not None:
        conditions.append("calendar = ?")
        params.append(calendar)

    if name is not None:
        conditions.append("name = ?")
        params.append(name)

    if start is not None:
        conditions.append("start >= ?")
        params.append(start)
    
    if end is not None:
        conditions.append("end <= ?")
        params.append(end)

    query += " WHERE " + " AND ".join(conditions)
    query += " ORDER BY start ASC LIMIT ?"
    params.append(limit)

    connection = get_connection()
    try:
        rows = connection.execute(query, params).fetchall()
        return [dict(row) for row in rows]
    finally:
        connection.close()


def print_events():
    connection = get_connection()

    rows = connection.execute("SELECT * FROM events").fetchall()

    for row in rows:
        print(dict(row))

    connection.close()