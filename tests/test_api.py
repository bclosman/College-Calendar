from types import ModuleType

from fastapi.testclient import TestClient


def test_get_assignments(client: TestClient, db: ModuleType) -> None:
    db.save_assignment({
        "id": "123456",
        "course_code": 235,
        "course_name": "CSCE 235",
        "course_id": 235,
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


def test_api_course_filter(client: TestClient, db: ModuleType) -> None:
    for course_code in [235, 310]:
        db.save_assignment({
            "id": f"123{course_code}",
            "course_code": course_code,
            "course_name": f"CSCE {course_code}",
            "course_id": 235,
            "name": "Homework",
            "due_at": "2026-10-12T23:59:00Z",
            "submitted": False,
            "url": "https://example.com"
        })

    response = client.get(
        "/api/assignments",
        params={"course_code": 235}
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["course_code"] == 235


def test_invalid_limit(client: TestClient) -> None:
    response = client.get(
        "/api/assignments",
        params={"limit": -1}
    )

    assert response.status_code == 422
