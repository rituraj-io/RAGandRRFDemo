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
from services.chat_store import ChatStore
from routers.documents import create_documents_router


@pytest.fixture()
def app_with_services(tmp_path):
    """Create a FastAPI app with document services."""
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
    return app


@pytest.fixture()
def client(app_with_services):
    return TestClient(app_with_services)


def test_ingest_document_returns_doc_id_and_chunks(client):
    """POST /api/documents chunks text and returns doc_id + chunk count."""
    response = client.post("/api/documents", json={
        "title": "Test Doc",
        "content": "This is a test. " * 30,  # ~480 chars, should produce multiple chunks
    })

    assert response.status_code == 201
    data = response.json()
    assert "doc_id" in data
    assert "chunks" in data
    assert data["chunks"] > 1


def test_ingest_short_text_single_chunk(client):
    """Short text produces a single chunk."""
    response = client.post("/api/documents", json={
        "title": "Short",
        "content": "Hello world.",
    })

    assert response.status_code == 201
    assert response.json()["chunks"] == 1


def test_delete_document_removes_all_chunks(client):
    """DELETE /api/documents/{doc_id} removes all chunks."""
    create_resp = client.post("/api/documents", json={
        "title": "To Delete",
        "content": "Some content here. " * 30,
    })
    doc_id = create_resp.json()["doc_id"]

    delete_resp = client.delete(f"/api/documents/{doc_id}")
    assert delete_resp.status_code == 200
    assert delete_resp.json()["deleted"] == doc_id


def test_list_documents(client):
    """GET /api/documents returns ingested documents."""
    client.post("/api/documents", json={
        "title": "Doc 1", "content": "First document content.",
    })

    response = client.get("/api/documents")
    assert response.status_code == 200
    docs = response.json()["documents"]
    assert len(docs) >= 1
