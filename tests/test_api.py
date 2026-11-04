from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("AEGIS_DATABASE_URL", f"sqlite:///{tmp_path / 'test.db'}")
    from apps.api import config
    config.get_settings.cache_clear()
    from apps.api import db
    db.settings = config.get_settings()
    db.engine = db.create_engine(db.settings.database_url, connect_args={"check_same_thread": False})
    db.SessionLocal.configure(bind=db.engine)
    from apps.api.main import app
    db.Base.metadata.create_all(bind=db.engine)
    return TestClient(app)


def auth(client: TestClient) -> dict[str, str]:
    response = client.post(
        "/auth/register",
        json={"email": "user@example.com", "password": "a-secure-password"},
    )
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_task_crud_and_ownership(client: TestClient):
    headers = auth(client)
    due = (datetime.now(UTC) + timedelta(hours=1)).isoformat()
    created = client.post("/tasks", headers=headers, json={"title": "Submit application", "due_at": due})
    assert created.status_code == 201
    task_id = created.json()["id"]
    assert client.get("/tasks", headers=headers).json()[0]["title"] == "Submit application"
    updated = client.patch(f"/tasks/{task_id}", headers=headers, json={"status": "completed"})
    assert updated.json()["status"] == "completed"
    assert client.get("/reminders", headers=headers).json()[0]["status"] == "cancelled"


def test_naive_deadline_is_rejected(client: TestClient):
    headers = auth(client)
    response = client.post("/tasks", headers=headers, json={"title": "Ambiguous", "due_at": "2026-11-05T08:00:00"})
    assert response.status_code == 422


def test_invalid_authentication_is_rejected(client: TestClient):
    assert client.get("/tasks", headers={"Authorization": "Bearer invalid"}).status_code == 401


def test_url_capture_is_attributed_and_deduplicated(client: TestClient):
    headers = auth(client)
    first = client.post("/sources", headers=headers, json={"url": "HTTPS://Example.com/opportunity#details"})
    assert first.status_code == 201
    assert first.json()["canonical_url"] == "https://example.com/opportunity"
    duplicate = client.post("/sources", headers=headers, json={"url": "https://example.com/opportunity"})
    assert duplicate.status_code == 201
    assert duplicate.json()["id"] == first.json()["id"]
