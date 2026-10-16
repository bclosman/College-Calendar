import json
from pathlib import Path
from types import ModuleType

import pytest
from fastapi.testclient import TestClient

from backend import api


def test_calendar_display_config_omits_feed_urls(client: TestClient, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    config = tmp_path / "calendars.json"
    config.write_text(json.dumps({
        "calendars": [{"name": "Classes", "url": "https://example.com/private-feed", "color": "#527f9b"}],
        "assignment_colors": {"CSCE-235": "#8c72a7", "invalid": "red"}
    }), encoding="utf-8")
    monkeypatch.setattr(api, "CALENDAR_CONFIG_PATH", config)
    monkeypatch.setenv("TIME_ZONE", "America/Chicago")
    response = client.get("/api/calendars")
    assert response.status_code == 200
    assert response.json() == {
        "calendars": [{"name": "Classes", "color": "#527f9b"}],
        "assignment_colors": {"CSCE-235": "#8c72a7"},
        "timezone": "America/Chicago"
    }
    assert "private-feed" not in response.text
    assert "url" not in response.json()["calendars"][0]


def test_events_load_and_paginate(client: TestClient, db: ModuleType) -> None:
    db.save_events("Classes", [
        {"uid": f"event-{i}", "title": f"Class {i}", "start": "2026-10-15T09:00:00Z", "end": None, "url": ""}
        for i in range(503)
    ])
    first = client.get("/api/events", params={"limit": 500}).json()
    second = client.get("/api/events", params={"limit": 500, "offset": 500}).json()
    assert len(first) == 500
    assert len(second) == 3
    assert len({row["id"] for row in first + second}) == 503
    assert all(row["calendar"] == "Classes" for row in first + second)


def test_assignment_pagination_and_status(client: TestClient, db: ModuleType) -> None:
    for i in range(4):
        db.save_assignment({"id": i + 1, "course_code": "CSCE-235", "course_name": "CSCE 235", "course_id": 235, "name": f"Work {i}", "due_at": "2026-10-16T18:00:00Z", "submitted": i == 3, "url": "https://example.com"})
    response = client.get("/api/assignments", params={"submitted": "false", "limit": 2, "offset": 2})
    assert response.status_code == 200
    assert [row["id"] for row in response.json()] == [3]


def test_frontend_assets_and_invalid_offset(client: TestClient) -> None:
    assert "College Calendar" in client.get("/").text
    assert client.get("/static/app.js").status_code == 200
    assert client.get("/static/styles.css").status_code == 200
    assert client.get("/api/events", params={"offset": -1}).status_code == 422


def test_missing_calendar_config_and_recovery(client: TestClient, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    config = tmp_path / "missing-calendars.json"
    monkeypatch.setattr(api, "CALENDAR_CONFIG_PATH", config)
    response = client.get("/api/calendars")
    assert response.status_code == 404
    assert response.json() == {"detail": {"code": "calendar_config_missing", "message": "calendars.json was not found."}}
    assert str(tmp_path) not in response.text
    assert client.get("/api/events").status_code == 200
    assert client.get("/api/assignments").status_code == 200

    config.write_text(json.dumps({"calendars": [{"name": "Classes", "url": "https://example.com/private", "color": "#527f9b"}]}), encoding="utf-8")
    response = client.get("/api/calendars")
    assert response.status_code == 200
    assert response.json()["calendars"] == [{"name": "Classes", "color": "#527f9b"}]
    assert "https://example.com/private" not in response.text
