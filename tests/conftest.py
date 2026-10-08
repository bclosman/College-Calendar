
import pytest
from fastapi.testclient import TestClient

from backend import database
from backend.main import app


@pytest.fixture
def db(tmp_path, monkeypatch):
    test_path = tmp_path / "test.db"

    monkeypatch.setattr(
        database,
        "DB_PATH",
        test_path
    )

    database.init_db()

    return database


@pytest.fixture
def client(db):
    with TestClient(app) as test_client:
        yield test_client
