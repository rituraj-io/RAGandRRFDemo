"""
Tests for the ChromaDB vector store service.
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from services.vector_store import VectorStore
from services.embedding import EmbeddingService


@pytest.fixture()
def embedding_svc():
    return EmbeddingService(model_name="all-MiniLM-L6-v2")


@pytest.fixture()
def store(tmp_path, embedding_svc):
    return VectorStore(persist_path=str(tmp_path / "chroma"), embedding_service=embedding_svc)


def test_add_and_search(store):
    """Adding a document makes it searchable by vector similarity."""
    store.add(
        doc_id="doc1",
        title="Python Guide",
        content="Python is a programming language",
        metadata={},
        permanent=False,
    )
    results = store.search("programming language", limit=5)

    assert len(results) >= 1
    assert results[0]["id"] == "doc1"
    assert results[0]["title"] == "Python Guide"
    assert "score" in results[0]


def test_delete(store):
    """Deleting a document removes it from search results."""
    store.add(doc_id="doc1", title="Test", content="test content", metadata={}, permanent=False)
    store.delete("doc1")
    results = store.search("test content", limit=5)

    assert all(r["id"] != "doc1" for r in results)


def test_list_documents(store):
    """List returns all stored documents."""
    store.add(doc_id="doc1", title="First", content="first doc", metadata={}, permanent=False)
    store.add(doc_id="doc2", title="Second", content="second doc", metadata={}, permanent=True)
    docs = store.list_all()

    assert len(docs) == 2
    ids = {d["id"] for d in docs}
    assert ids == {"doc1", "doc2"}


def test_cleanup_expired(store):
    """Cleanup removes non-permanent docs older than cutoff."""
    from datetime import datetime, timedelta

    store.add(doc_id="old", title="Old", content="old doc", metadata={}, permanent=False)
    store.add(doc_id="perm", title="Permanent", content="perm doc", metadata={}, permanent=True)

    # Force the old doc's created_at to 31 days ago
    cutoff = datetime.utcnow() - timedelta(days=30)
    store._collection.update(
        ids=["old"],
        metadatas=[{
            "title": "Old",
            "permanent": "false",
            "created_at": (datetime.utcnow() - timedelta(days=31)).isoformat(),
        }],
    )

    deleted_count = store.cleanup_expired(cutoff)

    assert deleted_count == 1
    docs = store.list_all()
    assert len(docs) == 1
    assert docs[0]["id"] == "perm"


def test_search_with_doc_id_filter(store):
    """Filtered search returns only chunks matching doc_id."""
    store.add(doc_id="chunk-a1", title="A1", content="cats are fluffy animals", metadata={"doc_id": "doc-a"}, permanent=False)
    store.add(doc_id="chunk-b1", title="B1", content="cats are cute pets", metadata={"doc_id": "doc-b"}, permanent=False)

    results = store.search("cats", limit=10, where={"doc_id": "doc-a"})
    assert len(results) >= 1
    assert all(r["metadata"].get("doc_id") == "doc-a" for r in results)


def test_search_with_source_filter(store):
    """Filtered search by source returns only matching chunks."""
    store.add(doc_id="hp-1", title="HP", content="harry potter magic wand", metadata={"source": "hp-books"}, permanent=True)
    store.add(doc_id="custom-1", title="Custom", content="magic tricks for beginners", metadata={"doc_id": "doc-x"}, permanent=False)

    results = store.search("magic", limit=10, where={"source": "hp-books"})
    assert len(results) >= 1
    assert all(r["metadata"].get("source") == "hp-books" for r in results)


def test_delete_by_doc_id(store):
    """delete_by_doc_id removes all chunks with matching doc_id."""
    store.add(doc_id="c1", title="C1", content="chunk one", metadata={"doc_id": "doc-a"}, permanent=False)
    store.add(doc_id="c2", title="C2", content="chunk two", metadata={"doc_id": "doc-a"}, permanent=False)
    store.add(doc_id="c3", title="C3", content="other chunk", metadata={"doc_id": "doc-b"}, permanent=False)

    store.delete_by_doc_id("doc-a")
    remaining = store.list_all()
    assert len(remaining) == 1
    assert remaining[0]["id"] == "c3"
