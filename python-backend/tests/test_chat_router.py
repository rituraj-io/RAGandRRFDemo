"""
Tests for the chat API router with scoped data isolation.
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient
from fastapi import FastAPI

from services.chat_store import ChatStore
from services.chat import ChatService
from routers.chat import create_chat_router


@pytest.fixture()
def mock_chat_service():
    svc = MagicMock(spec=ChatService)
    svc.generate_response = MagicMock(return_value="I am a helpful response.")
    return svc


@pytest.fixture()
def mock_hybrid_search():
    """Mock scoped search function."""
    def search(query, limit=5, doc_id=None, source=None):
        return [{"id": "doc1", "title": "Test", "content": "Test content", "score": 0.9, "metadata": {}}]
    return search


@pytest.fixture()
def app(tmp_path, mock_chat_service, mock_hybrid_search):
    chat_store = ChatStore(db_path=str(tmp_path / "chat.db"))

    app = FastAPI()
    app.include_router(create_chat_router(
        chat_store=chat_store,
        chat_service=mock_chat_service,
        hybrid_search_fn=mock_hybrid_search,
        chat_enabled=True,
    ))
    return app


@pytest.fixture()
def client(app):
    return TestClient(app)


def test_chat_status_enabled(client):
    """GET /api/chat/status returns enabled when LLM key is set."""
    resp = client.get("/api/chat/status")
    assert resp.status_code == 200
    assert resp.json()["enabled"] is True


def test_create_chat_with_doc_id(client):
    """POST /api/chat with doc_id creates a scoped chat."""
    resp = client.post("/api/chat", json={"doc_id": "doc-123"})
    assert resp.status_code == 201
    assert "chat_id" in resp.json()


def test_create_chat_with_source(client):
    """POST /api/chat with source creates a sample-scoped chat."""
    resp = client.post("/api/chat", json={"source": "sample"})
    assert resp.status_code == 201
    assert "chat_id" in resp.json()


def test_create_chat_requires_scope(client):
    """POST /api/chat without doc_id or source returns 400."""
    resp = client.post("/api/chat", json={})
    assert resp.status_code == 400


def test_send_message_and_get_response(client):
    """POST /api/chat/{id}/message returns LLM response."""
    chat = client.post("/api/chat", json={"doc_id": "doc-123"}).json()
    chat_id = chat["chat_id"]

    resp = client.post(f"/api/chat/{chat_id}/message", json={"message": "Hello"})

    assert resp.status_code == 200
    data = resp.json()
    assert data["response"] == "I am a helpful response."
    assert "sources" in data


def test_get_chat_history(client):
    """GET /api/chat/{id} returns message history."""
    chat = client.post("/api/chat", json={"source": "sample"}).json()
    chat_id = chat["chat_id"]
    client.post(f"/api/chat/{chat_id}/message", json={"message": "Hello"})

    resp = client.get(f"/api/chat/{chat_id}")

    assert resp.status_code == 200
    history = resp.json()["messages"]
    assert len(history) == 2
    assert history[0]["role"] == "user"
    assert history[1]["role"] == "assistant"


def test_list_chats(client):
    """GET /api/chat returns all chats."""
    client.post("/api/chat", json={"doc_id": "doc-1"})
    client.post("/api/chat", json={"source": "sample"})

    resp = client.get("/api/chat")

    assert resp.status_code == 200
    assert len(resp.json()["chats"]) == 2


def test_delete_chat(client):
    """DELETE /api/chat/{id} removes the chat."""
    chat = client.post("/api/chat", json={"doc_id": "doc-1"}).json()
    chat_id = chat["chat_id"]

    resp = client.delete(f"/api/chat/{chat_id}")
    assert resp.status_code == 200

    chats = client.get("/api/chat").json()["chats"]
    assert all(c["id"] != chat_id for c in chats)
