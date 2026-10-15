from collections.abc import Iterator
from pathlib import Path
from types import ModuleType

import pytest
from fastapi.testclient import TestClient

from backend import database
from backend.api import app


@pytest.fixture
def db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> ModuleType:
    test_path = tmp_path / "test.db"

    monkeypatch.setattr(
        database,
        "DB_PATH",
        test_path
    )

    database.init_db()

    return database


@pytest.fixture
def client(db: ModuleType) -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        yield test_client
