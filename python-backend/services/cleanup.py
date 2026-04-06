"""
Cleanup service — 30-day data expiration.

Deletes non-permanent documents from both vector and BM25 stores,
and all chats older than the configured max age.
"""

from datetime import datetime, timedelta

from services.vector_store import VectorStore
from services.bm25_store import BM25Store
from services.chat_store import ChatStore


def run_cleanup(
    vector_store: VectorStore,
    bm25_store: BM25Store,
    chat_store: ChatStore,
    max_age_days: int = 30,
) -> dict:
    """
    Run cleanup on all stores.

    Deletes:
    - Non-permanent documents older than max_age_days from vector and BM25 stores.
    - All chats older than max_age_days.

    Returns a summary dict with deletion counts.
    """

    cutoff = datetime.utcnow() - timedelta(days=max_age_days)


    docs_vector = vector_store.cleanup_expired(cutoff)
    docs_bm25 = bm25_store.cleanup_expired(cutoff)
    chats = chat_store.cleanup_expired(cutoff)


    return {
        "documents_deleted": max(docs_vector, docs_bm25),
        "chats_deleted": chats,
        "cutoff": cutoff.isoformat(),
    }
