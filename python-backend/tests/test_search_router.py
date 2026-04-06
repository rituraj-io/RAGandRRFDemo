"""
Tests for the search API router with scoped filtering.
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI

from config import Settings
from services.embedding import EmbeddingService
from services.vector_store import VectorStore
from services.bm25_store import BM25Store
from services.chat_store import ChatStore
from routers.search import create_search_router
from routers.documents import create_documents_router


@pytest.fixture()
def app_with_services(tmp_path):
    settings = Settings(
        chroma_path=str(tmp_path / "chroma"),
        sqlite_bm25_path=str(tmp_path / "bm25.db"),
        sqlite_chat_path=str(tmp_path / "chat.db"),
    )

    embedding_svc = EmbeddingService(model_name=settings.embedding_model)
    vector_store = VectorStore(persist_path=settings.chroma_path, embedding_service=embedding_svc)
    bm25_store = BM25Store(db_path=settings.sqlite_bm25_path)
    chat_store = ChatStore(db_path=settings.sqlite_chat_path)

    app = FastAPI()
    app.include_router(create_documents_router(vector_store, bm25_store, embedding_svc, chat_store))
    app.include_router(create_search_router(vector_store, bm25_store))
    return app


@pytest.fixture()
def client(app_with_services):
    return TestClient(app_with_services)


def test_search_requires_scope(client):
    """Search without doc_id or source returns 400."""
    resp = client.get("/api/search", params={"q": "test"})
    assert resp.status_code == 400


def test_search_by_doc_id(client):
    """Search scoped to a doc_id returns only that doc's chunks."""
    resp1 = client.post("/api/documents", json={"title": "Doc A", "content": "Python is a programming language for data science"})
    doc_a = resp1.json()["doc_id"]

    resp2 = client.post("/api/documents", json={"title": "Doc B", "content": "JavaScript is used for web development"})
    doc_b = resp2.json()["doc_id"]

    results = client.get("/api/search", params={"q": "programming", "doc_id": doc_a}).json()["results"]

    # All results should belong to doc_a
    for r in results:
        assert r["metadata"].get("doc_id") == doc_a


def test_search_by_source_sample(client):
    """Search scoped to source=sample filters by hp-books source tag."""
    resp = client.get("/api/search", params={"q": "harry potter", "source": "sample"})
    assert resp.status_code == 200
    assert "results" in resp.json()


def test_search_modes_with_scope(client):
    """All search modes work with scoping."""
    resp = client.post("/api/documents", json={"title": "Test", "content": "Machine learning and artificial intelligence concepts"})
    doc_id = resp.json()["doc_id"]

    for mode in ["vector", "bm25", "hybrid"]:
        resp = client.get("/api/search", params={"q": "machine learning", "doc_id": doc_id, "mode": mode})
        assert resp.status_code == 200
