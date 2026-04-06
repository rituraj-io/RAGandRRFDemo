"""
Tests for the search API router.
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
from routers.search import create_search_router
from routers.documents import create_documents_router


@pytest.fixture()
def app_with_services(tmp_path):
    settings = Settings(
        chroma_path=str(tmp_path / "chroma"),
        sqlite_bm25_path=str(tmp_path / "bm25.db"),
    )

    embedding_svc = EmbeddingService(model_name=settings.embedding_model)
    vector_store = VectorStore(persist_path=settings.chroma_path, embedding_service=embedding_svc)
    bm25_store = BM25Store(db_path=settings.sqlite_bm25_path)

    app = FastAPI()
    app.include_router(create_documents_router(vector_store, bm25_store))
    app.include_router(create_search_router(vector_store, bm25_store))
    return app


@pytest.fixture()
def client(app_with_services):
    return TestClient(app_with_services)


@pytest.fixture(autouse=True)
def seed_documents(client):
    """Seed some documents for search tests."""
    client.post("/api/documents", json={
        "title": "Python Basics", "content": "Python is a high level programming language.", "metadata": {}, "permanent": False,
    })
    client.post("/api/documents", json={
        "title": "JavaScript Guide", "content": "JavaScript runs in the browser and on servers.", "metadata": {}, "permanent": False,
    })
    client.post("/api/documents", json={
        "title": "Rust Overview", "content": "Rust is a systems programming language focused on safety.", "metadata": {}, "permanent": False,
    })


def test_vector_search(client):
    """Vector search returns relevant results."""
    resp = client.get("/api/search", params={"q": "programming language", "mode": "vector", "limit": 2})

    assert resp.status_code == 200
    results = resp.json()["results"]
    assert len(results) <= 2
    assert all("score" in r for r in results)


def test_bm25_search(client):
    """BM25 search returns results matching keywords."""
    resp = client.get("/api/search", params={"q": "programming language", "mode": "bm25", "limit": 5})

    assert resp.status_code == 200
    results = resp.json()["results"]
    assert len(results) >= 1


def test_hybrid_search(client):
    """Hybrid search merges vector and BM25 results."""
    resp = client.get("/api/search", params={"q": "programming language", "mode": "hybrid", "limit": 5})

    assert resp.status_code == 200
    results = resp.json()["results"]
    assert len(results) >= 1


def test_default_mode_is_hybrid(client):
    """Default search mode is hybrid."""
    resp = client.get("/api/search", params={"q": "Python"})

    assert resp.status_code == 200
    assert "results" in resp.json()


def test_search_limit(client):
    """Limit parameter controls result count."""
    resp = client.get("/api/search", params={"q": "programming", "mode": "vector", "limit": 1})
    results = resp.json()["results"]
    assert len(results) == 1
