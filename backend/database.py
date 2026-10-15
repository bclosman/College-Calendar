import sqlite3
from datetime import date as Date
from pathlib import Path
from typing import Any

DB_PATH: Path = Path(__file__).resolve().parent.parent / "data" / "database.db"

def get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_db() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    connection = get_connection()

    try:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS assignments (
                id INTEGER PRIMARY KEY,
                course_code TEXT NOT NULL,
                course_name TEXT NOT NULL,
                course_id INTEGER NOT NULL,
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


def save_assignment(assignment: dict[str, Any]) -> None:
    connection = get_connection()

    try:
        connection.execute("""
            INSERT INTO assignments (
                id, course_code, course_name, course_id,
                name, due_at, submitted, url
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                course_code = excluded.course_code,
                course_name = excluded.course_name,
                course_id = excluded.course_id,
                name = excluded.name,
                due_at = excluded.due_at,
                submitted = excluded.submitted,
                url = excluded.url
            """, (
                assignment["id"],
                assignment["course_code"],
                assignment["course_name"],
                assignment["course_id"],
                assignment["name"],
                assignment["due_at"],
                int(assignment.get("submitted", False)),
                assignment["url"]
            ))

        connection.commit()
    finally:
        connection.close()


def get_assignments(
    course_code: int | None = None,
    start: str | None = None,
    end: str | None = None,
    submitted: bool | None = None,
    limit: int = 100,
    offset: int = 0
) -> list[dict[str, Any]]:
    if not 1 <= limit <= 500:
        raise ValueError("Limit must be between 1 and 500")

    query = "SELECT * FROM assignments"
    conditions = ["due_at IS NOT NULL"]
    params: list[str | int] = []

    if course_code is not None:
        conditions.append("course_code = ?")
        params.append(course_code)

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
    query += " ORDER BY due_at ASC, id ASC LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    connection = get_connection()
    try:
        rows = connection.execute(query, params).fetchall()
        return [dict(row) for row in rows]
    finally:
        connection.close()

def print_assignments() -> None:
    connection = get_connection()

    rows = connection.execute("SELECT * FROM assignments").fetchall()

    for row in rows:
        print(dict(row))

    connection.close()

def remove_assignments(date: Date) -> int:
    connection = get_connection()

    try:
        with connection:
            # Remove assignments older than 14 days
            row_count = connection.execute("""
                DELETE FROM assignments
                WHERE
                    (due_at < ?)
            """, (
                date.isoformat(),
            )).rowcount

            return row_count
    finally:
        connection.close()

def save_events(calendar_name: str, events: list[dict[str, Any]]) -> None:
    connection = get_connection()

    try:
        with connection:
            # Remove previous events for this calendar
            connection.execute(
                "DELETE FROM events WHERE calendar = ?",
                (calendar_name,)
            )

            # Insert the updated events
            connection.executemany("""
                INSERT INTO events (
                    uid, calendar, name,
                    start, end, url
                )
                VALUES (?, ?, ?, ?, ?, ?)
            """, [
                (
                    event["uid"],
                    calendar_name,
                    event["title"],
                    event["start"],
                    event["end"],
                    event.get("url", "")
                )
                for event in events
            ])
            
            connection.commit()
    finally:
        connection.close()

def get_events(
    calendar: str | None = None,
    name: str | None = None,
    start: str | None = None,
    end: str | None = None,
    limit: int = 100,
    offset: int = 0
) -> list[dict[str, Any]]:
    if not 1 <= limit <= 500:
        raise ValueError("Limit must be between 1 and 500")

    query = "SELECT * FROM events"
    conditions = ["start IS NOT NULL"]
    params: list[str | int] = []

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
    query += " ORDER BY start ASC, id ASC LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    connection = get_connection()
    try:
        rows = connection.execute(query, params).fetchall()
        return [dict(row) for row in rows]
    finally:
        connection.close()


def print_events() -> None:
    connection = get_connection()

    rows = connection.execute("SELECT * FROM events").fetchall()

    for row in rows:
        print(dict(row))

    connection.close()

def remove_events(date: Date) -> int:
    connection = get_connection()

    try:
        with connection:
            row_count = connection.execute("""
                DELETE FROM events
                WHERE
                    ("end" IS NOT NULL
                     AND "end" <= ?)
                    OR
                    ("end" IS NULL
                     AND "start" < ?)
            """, (
                date.isoformat(),
                date.isoformat()
            )).rowcount

            return row_count
    finally:
        connection.close()