"""
Tests for the documents API router.
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
from routers.documents import create_documents_router


@pytest.fixture()
def app_with_services(tmp_path):
    """Create a FastAPI app with document services."""
    settings = Settings(
        chroma_path=str(tmp_path / "chroma"),
        sqlite_bm25_path=str(tmp_path / "bm25.db"),
    )

    embedding_svc = EmbeddingService(model_name=settings.embedding_model)
    vector_store = VectorStore(persist_path=settings.chroma_path, embedding_service=embedding_svc)
    bm25_store = BM25Store(db_path=settings.sqlite_bm25_path)

    app = FastAPI()
    app.include_router(create_documents_router(vector_store, bm25_store))
    return app


@pytest.fixture()
def client(app_with_services):
    return TestClient(app_with_services)


def test_ingest_document(client):
    """POST /api/documents ingests a document and returns its ID."""
    response = client.post("/api/documents", json={
        "title": "Test Doc",
        "content": "This is test content for ingestion.",
        "metadata": {"source": "unit-test"},
        "permanent": False,
    })

    assert response.status_code == 201
    data = response.json()
    assert "id" in data


def test_list_documents(client):
    """GET /api/documents returns ingested documents."""
    client.post("/api/documents", json={
        "title": "Doc 1", "content": "First document.", "metadata": {}, "permanent": False,
    })
    client.post("/api/documents", json={
        "title": "Doc 2", "content": "Second document.", "metadata": {}, "permanent": True,
    })

    response = client.get("/api/documents")

    assert response.status_code == 200
    docs = response.json()["documents"]
    assert len(docs) == 2


def test_delete_document(client):
    """DELETE /api/documents/{id} removes a document."""
    create_resp = client.post("/api/documents", json={
        "title": "To Delete", "content": "Will be deleted.", "metadata": {}, "permanent": False,
    })
    doc_id = create_resp.json()["id"]

    delete_resp = client.delete(f"/api/documents/{doc_id}")
    assert delete_resp.status_code == 200

    list_resp = client.get("/api/documents")
    ids = [d["id"] for d in list_resp.json()["documents"]]
    assert doc_id not in ids
