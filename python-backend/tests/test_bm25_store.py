"""
Tests for the SQLite FTS5 BM25 store service.
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from datetime import datetime, timedelta
from hypothesis import HealthCheck, given, settings, strategies as st
from services.bm25_store import BM25Store, _sanitize_fts5


@pytest.fixture()
def store(tmp_path):
    return BM25Store(db_path=str(tmp_path / "bm25.db"))


def test_add_and_search(store):
    """Adding a document makes it searchable by BM25."""
    store.add(
        doc_id="doc1",
        title="Python Guide",
        content="Python is a programming language used for web development",
        metadata={},
        permanent=False,
    )
    results = store.search("programming language", limit=5)

    assert len(results) >= 1
    assert results[0]["id"] == "doc1"
    assert "score" in results[0]


def test_delete(store):
    """Deleting a document removes it from search."""
    store.add(doc_id="doc1", title="Test", content="test content here", metadata={}, permanent=False)
    store.delete("doc1")
    results = store.search("test content", limit=5)

    assert all(r["id"] != "doc1" for r in results)


def test_list_documents(store):
    """List returns all stored documents."""
    store.add(doc_id="doc1", title="First", content="first doc", metadata={}, permanent=False)
    store.add(doc_id="doc2", title="Second", content="second doc", metadata={}, permanent=True)
    docs = store.list_all()

    assert len(docs) == 2


def test_cleanup_expired(store):
    """Cleanup removes non-permanent docs older than cutoff."""
    store.add(doc_id="old", title="Old", content="old doc", metadata={}, permanent=False)
    store.add(doc_id="perm", title="Permanent", content="perm doc", metadata={}, permanent=True)

    # Force old doc's created_at to 31 days ago
    import sqlite3
    conn = sqlite3.connect(store._db_path)
    old_date = (datetime.utcnow() - timedelta(days=31)).isoformat()
    conn.execute("UPDATE documents SET created_at = ? WHERE id = ?", (old_date, "old"))
    conn.commit()
    conn.close()

    cutoff = datetime.utcnow() - timedelta(days=30)
    deleted_count = store.cleanup_expired(cutoff)

    assert deleted_count == 1
    docs = store.list_all()
    assert len(docs) == 1
    assert docs[0]["id"] == "perm"


def test_search_with_doc_id_filter(store):
    """Filtered search returns only chunks matching doc_id."""
    store.add(doc_id="chunk-a1", title="A1", content="cats are fluffy animals", metadata={"doc_id": "doc-a"}, permanent=False)
    store.add(doc_id="chunk-b1", title="B1", content="cats are cute pets", metadata={"doc_id": "doc-b"}, permanent=False)

    results = store.search("cats", limit=10, doc_id="doc-a")
    assert len(results) >= 1
    assert all(r["metadata"].get("doc_id") == "doc-a" for r in results)


def test_search_with_source_filter(store):
    """Filtered search by source returns only matching chunks."""
    store.add(doc_id="hp-1", title="HP", content="harry potter magic wand", metadata={"source": "hp-books"}, permanent=True)
    store.add(doc_id="custom-1", title="Custom", content="magic tricks for beginners", metadata={"doc_id": "doc-x"}, permanent=False)

    results = store.search("magic", limit=10, source="hp-books")
    assert len(results) >= 1
    assert all(r["metadata"].get("source") == "hp-books" for r in results)


def test_delete_by_doc_id(store):
    """delete_by_doc_id removes all chunks with matching doc_id."""
    store.add(doc_id="c1", title="C1", content="chunk one", metadata={"doc_id": "doc-a"}, permanent=False)
    store.add(doc_id="c2", title="C2", content="chunk two", metadata={"doc_id": "doc-a"}, permanent=False)
    store.add(doc_id="c3", title="C3", content="other chunk", metadata={"doc_id": "doc-b"}, permanent=False)

    store.delete_by_doc_id("doc-a")
    docs = store.list_all()
    assert len(docs) == 1
    assert docs[0]["id"] == "c3"


# =============================================================================
# FTS5 sanitization — structural safety tests
#
# See docs/superpowers/specs/2026-04-10-fts5-sanitization-design.md for the
# rationale. The goal of these three layers is to make it impossible for any
# user-supplied query to produce a sqlite3.OperationalError from FTS5 MATCH.
# =============================================================================


# ---- Layer 1: unit tests for _sanitize_fts5 --------------------------------

@pytest.mark.parametrize("query,expected", [
    ("", ""),
    ("   ", ""),
    ("Ron's sister, what?", '"Ron" "s" "sister" "what"'),
    ("AND OR NOT NEAR", '"AND" "OR" "NOT" "NEAR"'),
    ("!@#$%^&*()", ""),
    ("日本語 テスト", '"日本語" "テスト"'),
    ("Harry-Potter", '"Harry" "Potter"'),
])
def test_sanitize_fts5_produces_safe_phrase_grammar(query, expected):
    """The sanitizer extracts word tokens and phrase-wraps each one."""
    assert _sanitize_fts5(query) == expected


# ---- Layer 2: regression tests through BM25Store.search() ------------------

@pytest.fixture()
def store_with_doc(store):
    """A store pre-seeded with one indexed document for search regression tests."""
    store.add(
        doc_id="seed",
        title="Harry Potter",
        content="Harry Potter and his friend Ron Weasley fight magic",
        metadata={},
        permanent=False,
    )
    return store


@pytest.mark.parametrize("query", [
    "Who's there?",                    # apostrophe — previously crashed
    "Ron, Harry, Hermione",            # comma — previously crashed
    "Harry-Potter",                    # dash (FTS5 NOT operator)
    'She said "hello"',                # double quote (phrase delimiter)
    "foo (bar) [baz]",                 # parens and brackets
    "Ron AND Harry",                   # reserved word mixed with content
    "NOT magic",                       # leading reserved word
    "!@#$%^&*()",                      # all punctuation, no tokens
    "日本語",                            # pure Unicode
    "a" * 5000 + "!@#" * 100,          # long mixed input
    "",                                # empty
    "   ",                             # whitespace only
])
def test_search_does_not_raise_on_problematic_input(store_with_doc, query):
    """None of these previously-dangerous inputs should raise; all return a list."""
    result = store_with_doc.search(query)
    assert isinstance(result, list)


def test_search_happy_path_still_retrieves(store_with_doc):
    """The phrase-wrap rewrite must still retrieve real documents via BM25."""
    results = store_with_doc.search("Ron Harry")
    assert len(results) >= 1
    assert results[0]["id"] == "seed"


# ---- Layer 3: property test — the structural guarantee --------------------

@given(query=st.text())
@settings(
    max_examples=500,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
def test_search_never_raises_for_arbitrary_text(store_with_doc, query):
    """Hammer search() with arbitrary Unicode — must never raise anything.

    This is the proof that backs goal G1 of the design: FTS5 syntax errors
    from user input are now structurally impossible, not merely unobserved.
    """
    store_with_doc.search(query)
