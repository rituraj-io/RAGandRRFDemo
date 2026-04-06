"""
Tests for the SQLite chat store service.
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from datetime import datetime, timedelta
from services.chat_store import ChatStore


@pytest.fixture()
def store(tmp_path):
    return ChatStore(db_path=str(tmp_path / "chat.db"))


def test_create_chat(store):
    """Creating a chat returns a UUID."""
    chat_id = store.create_chat()
    assert isinstance(chat_id, str)
    assert len(chat_id) == 36


def test_add_and_get_messages(store):
    """Adding messages to a chat and retrieving them."""
    chat_id = store.create_chat()

    store.add_message(chat_id, role="user", content="Hello")
    store.add_message(chat_id, role="assistant", content="Hi there!")

    history = store.get_history(chat_id)
    assert len(history) == 2
    assert history[0]["role"] == "user"
    assert history[0]["content"] == "Hello"
    assert history[1]["role"] == "assistant"
    assert history[1]["content"] == "Hi there!"


def test_list_chats(store):
    """List chats returns all chats with preview."""
    chat_id = store.create_chat()
    store.add_message(chat_id, role="user", content="First message here")

    chats = store.list_chats()
    assert len(chats) == 1
    assert chats[0]["id"] == chat_id
    assert "created_at" in chats[0]
    assert chats[0]["preview"] == "First message here"


def test_delete_chat(store):
    """Deleting a chat removes it and its messages."""
    chat_id = store.create_chat()
    store.add_message(chat_id, role="user", content="Test")
    store.delete_chat(chat_id)

    chats = store.list_chats()
    assert len(chats) == 0

    history = store.get_history(chat_id)
    assert len(history) == 0


def test_cleanup_expired(store):
    """Cleanup removes chats older than cutoff."""
    chat_id = store.create_chat()
    store.add_message(chat_id, role="user", content="Old chat")

    # Force created_at to 31 days ago
    import sqlite3
    conn = sqlite3.connect(store._db_path)
    old_date = (datetime.utcnow() - timedelta(days=31)).isoformat()
    conn.execute("UPDATE chats SET created_at = ? WHERE id = ?", (old_date, chat_id))
    conn.commit()
    conn.close()

    cutoff = datetime.utcnow() - timedelta(days=30)
    deleted = store.cleanup_expired(cutoff)

    assert deleted == 1
    assert len(store.list_chats()) == 0


def test_create_chat_with_doc_id(store):
    """Chat can be created with a doc_id scope."""
    chat_id = store.create_chat(doc_id="doc-123")
    scope = store.get_scope(chat_id)
    assert scope == {"doc_id": "doc-123", "source": None}


def test_create_chat_with_source(store):
    """Chat can be created with a source scope."""
    chat_id = store.create_chat(source="sample")
    scope = store.get_scope(chat_id)
    assert scope == {"doc_id": None, "source": "sample"}


def test_delete_by_doc_id(store):
    """delete_by_doc_id removes the chat tied to a doc_id."""
    chat_id = store.create_chat(doc_id="doc-456")
    store.add_message(chat_id, "user", "Hello")

    store.delete_by_doc_id("doc-456")
    chats = store.list_chats()
    assert len(chats) == 0
