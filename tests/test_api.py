def test_get_assignments(client, db):
    db.save_assignment({
        "course_id": 235,
        "course_name": "CSCE 235",
        "name": "Homework 4",
        "due_at": "2026-10-12T23:59:00Z",
        "submitted": False,
        "url": "https://example.com"
    })

    response = client.get("/api/assignments")

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["name"] == "Homework 4"


def test_api_course_filter(client, db):
    for course_id in [235, 310]:
        db.save_assignment({
            "course_id": course_id,
            "course_name": f"CSCE {course_id}",
            "name": "Homework",
            "due_at": "2026-10-12T23:59:00Z",
            "submitted": False,
            "url": "https://example.com"
        })

    response = client.get(
        "/api/assignments",
        params={"course_id": 235}
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["course_id"] == 235


def test_invalid_limit(client):
    response = client.get(
        "/api/assignments",
        params={"limit": -1}
    )

    assert response.status_code == 422
