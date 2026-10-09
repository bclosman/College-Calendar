def test_database_initialized(client, db):
    connection = db.get_connection()

    try:
        result = connection.execute("""
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
              AND name = 'assignments'
        """).fetchone()

        assert result is not None
    finally:
        connection.close()


def test_insert_assignment(db):
    assignment = {
        "course_id": 235,
        "course_name": "CSCE 235",
        "name": "Homework 4",
        "due_at": "2026-10-12T23:59:00Z",
        "submitted": False,
        "url": "https://example.com"
    }

    db.save_assignment(assignment)

    results = db.get_assignments()

    assert len(results) == 1
    assert results[0]["id"] == 101
    assert results[0]["name"] == "Homework 4"
    assert results[0]["course_id"] == 235


def test_update_assignment(db):
    assignment = {
        "course_id": 235,
        "course_name": "CSCE 235",
        "name": "Homework 4",
        "due_at": "2026-10-12T23:59:00Z",
        "submitted": False,
        "url": "https://example.com"
    }

    db.save_assignment(assignment)

    # Simulate Canvas changing the due date
    assignment["due_at"] = "2026-10-15T23:59:00Z"

    db.save_assignment(assignment)

    results = db.get_assignments()

    assert len(results) == 1
    assert results[0]["due_at"] == "2026-10-15T23:59:00Z"


def test_submitted_filter(db):
    assignment = {
        "course_id": 235,
        "course_name": "CSCE 235",
        "name": "Homework 4",
        "due_at": "2026-10-12T23:59:00Z",
        "submitted": True,
        "url": "https://example.com"
    }

    db.save_assignment(assignment)

    # When filtering for only unsubmitted assignments, should return 0
    assert len(db.get_assignments(submitted=False)) == 0

    # When not filtering, should find every assignment
    results = db.get_assignments()
    assert len(results) == 1
    assert results[0]["submitted"] == 1
