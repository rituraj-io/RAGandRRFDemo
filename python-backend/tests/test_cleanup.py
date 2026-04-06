"""
Tests for the cleanup service.
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from unittest.mock import MagicMock
from datetime import datetime, timedelta
from services.cleanup import run_cleanup


def test_run_cleanup_calls_all_stores():
    """Cleanup calls cleanup_expired on all three stores."""
    vector_store = MagicMock()
    bm25_store = MagicMock()
    chat_store = MagicMock()

    vector_store.cleanup_expired = MagicMock(return_value=2)
    bm25_store.cleanup_expired = MagicMock(return_value=2)
    chat_store.cleanup_expired = MagicMock(return_value=1)

    result = run_cleanup(vector_store, bm25_store, chat_store, max_age_days=30)

    assert vector_store.cleanup_expired.called
    assert bm25_store.cleanup_expired.called
    assert chat_store.cleanup_expired.called

    assert result["documents_deleted"] == 2
    assert result["chats_deleted"] == 1


def test_run_cleanup_uses_correct_cutoff():
    """Cleanup passes a cutoff date that is max_age_days ago."""
    vector_store = MagicMock()
    bm25_store = MagicMock()
    chat_store = MagicMock()

    vector_store.cleanup_expired = MagicMock(return_value=0)
    bm25_store.cleanup_expired = MagicMock(return_value=0)
    chat_store.cleanup_expired = MagicMock(return_value=0)

    run_cleanup(vector_store, bm25_store, chat_store, max_age_days=30)

    cutoff_arg = vector_store.cleanup_expired.call_args[0][0]
    expected_cutoff = datetime.utcnow() - timedelta(days=30)

    assert abs((cutoff_arg - expected_cutoff).total_seconds()) < 5
