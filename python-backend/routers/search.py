"""
Search router — vector, BM25, and hybrid search.

Supports three modes: vector-only, bm25-only, and hybrid (RRF merge).
Default mode is hybrid. Every search must be scoped to either
a doc_id (custom text) or source=sample (HP books).
"""

from enum import Enum
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

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
        doc_id: Optional[str] = Query(None, description="Filter by parent document ID"),
        source: Optional[str] = Query(None, description="Filter by source (e.g. 'sample')"),
    ):
        """Search documents scoped to a doc_id or source."""

        if not doc_id and not source:
            raise HTTPException(status_code=400, detail="Either doc_id or source is required.")

        # Build filters for each store
        vector_where = None
        bm25_doc_id = None
        bm25_source = None

        if doc_id:
            vector_where = {"doc_id": doc_id}
            bm25_doc_id = doc_id
        elif source == "sample":
            vector_where = {"source": "hp-books"}
            bm25_source = "hp-books"

        if mode == SearchMode.vector:
            results = vector_store.search(q, limit=limit, where=vector_where)

        elif mode == SearchMode.bm25:
            results = bm25_store.search(q, limit=limit, doc_id=bm25_doc_id, source=bm25_source)

        else:
            vector_results = vector_store.search(q, limit=limit, where=vector_where)
            bm25_results = bm25_store.search(q, limit=limit, doc_id=bm25_doc_id, source=bm25_source)
            results = reciprocal_rank_fusion(vector_results, bm25_results, limit=limit)

        return {"results": results}


    return router
