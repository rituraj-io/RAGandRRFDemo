"""
Search router — vector, BM25, and hybrid search.

Supports three modes: vector-only, bm25-only, and hybrid (RRF merge).
Default mode is hybrid.
"""

from enum import Enum

from fastapi import APIRouter, Query

from services.vector_store import VectorStore
from services.bm25_store import BM25Store
from services.hybrid_search import reciprocal_rank_fusion


# -- Search mode enum --

class SearchMode(str, Enum):
    """Supported search modes."""
    vector = "vector"
    bm25 = "bm25"
    hybrid = "hybrid"


# -- Router factory --

def create_search_router(vector_store: VectorStore, bm25_store: BM25Store) -> APIRouter:
    """Create the search router with injected dependencies."""

    router = APIRouter(prefix="/api/search", tags=["search"])


    @router.get("")
    def search(
        q: str = Query(..., description="Search query"),
        mode: SearchMode = Query(SearchMode.hybrid, description="Search mode"),
        limit: int = Query(10, ge=1, le=100, description="Number of results"),
    ):
        """Search documents by vector similarity, BM25 keywords, or hybrid."""

        if mode == SearchMode.vector:
            results = vector_store.search(q, limit=limit)

        elif mode == SearchMode.bm25:
            results = bm25_store.search(q, limit=limit)

        else:
            vector_results = vector_store.search(q, limit=limit)
            bm25_results = bm25_store.search(q, limit=limit)
            results = reciprocal_rank_fusion(vector_results, bm25_results, limit=limit)

        return {"results": results}


    return router
