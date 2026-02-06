from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from src.api_server import app
from src.conversation import Conversation
from src.database.models import conversations, user_profiles
from src.database.utils import get_engine
from src.user_profile import UserProfile


@pytest.fixture()
def client(tmp_path, monkeypatch):
    db_path = tmp_path / "test.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")

    import src.database.utils as db_utils

    if db_utils._engine is not None:
        db_utils._engine.dispose()
    db_utils._engine = None
    db_utils._SessionLocal = None

    with TestClient(app) as test_client:
        yield test_client

    if db_utils._engine is not None:
        db_utils._engine.dispose()
    db_utils._engine = None
    db_utils._SessionLocal = None

    if db_path.exists():
        db_path.unlink()


class TestApiServer:
    def test_user(self, client: TestClient):
        response = client.post("/api/v1/users", json={"name": "Jan"})
        assert response.status_code == 201
        user = response.json()
        user_id = user["id"]

        engine = get_engine()
        with engine.connect() as conn:
            row = conn.execute(
                select(user_profiles.c.id, user_profiles.c.data).where(
                    user_profiles.c.id == user_id
                )
            ).one()
        assert row.data["name"] == "Jan"

        profile = UserProfile.load(user_id)
        profile.name = "Anna"
        profile.save()

        with engine.connect() as conn:
            row = conn.execute(
                select(user_profiles.c.data).where(user_profiles.c.id == user_id)
            ).one()
        assert row.data["name"] == "Anna"

        response = client.get(f"/api/v1/users/{user_id}")
        assert response.status_code == 200
        assert response.json()["name"] == "Anna"

    def test_conversation(self, client: TestClient):
        user = client.post("/api/v1/users", json={"name": "Jan"}).json()
        user_id = user["id"]

        created = []
        for _ in range(3):
            response = client.post("/api/v1/conversations", json={"user_id": user_id})
            assert response.status_code == 201
            created.append(response.json()["id"])

        response = client.get("/api/v1/conversations", params={"user_id": user_id})
        assert response.status_code == 200
        items = response.json()
        assert len(items) == 3

        response = client.get(f"/api/v1/conversations/{created[0]}")
        assert response.status_code == 200
        conversation = response.json()
        assert conversation["id"] == created[0]
        assert conversation["user_id"] == user_id

        engine = get_engine()
        with engine.connect() as conn:
            rows = conn.execute(
                select(conversations.c.id).where(conversations.c.user_id == user_id)
            ).all()
        assert len(rows) == 3

    def test_messages(self, client: TestClient, monkeypatch):
        from src.graphs.simple_generation_graph import SimpleGenerationGraph

        def fake_invoke(self, messages, user_profile):
            return "pong"

        monkeypatch.setattr(SimpleGenerationGraph, "invoke", fake_invoke)

        user = client.post("/api/v1/users", json={"name": "Jan"}).json()
        user_id = user["id"]
        conversation = client.post(
            "/api/v1/conversations", json={"user_id": user_id}
        ).json()
        conversation_id = conversation["id"]

        response = client.post(
            f"/api/v1/conversations/{conversation_id}/messages",
            json={"content": "Hello"},
        )
        assert response.status_code == 200
        assert response.json()["assistant"]["content"] == "pong"

        response = client.post(
            f"/api/v1/conversations/{conversation_id}/messages",
            json={"content": "How are you?"},
        )
        assert response.status_code == 200
        assert response.json()["assistant"]["content"] == "pong"

        response = client.get(
            f"/api/v1/conversations/{conversation_id}/messages"
        )
        assert response.status_code == 200
        messages = response.json()["messages"]
        assert len(messages) == 4

        loaded = Conversation.load(conversation_id)
        assert len(loaded.data.get("messages", [])) == 4