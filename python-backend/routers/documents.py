"""
Documents router — ingest, list, and delete documents.

All documents are stored in both ChromaDB (vector) and
SQLite FTS5 (BM25) with a shared document ID.
"""

import uuid

from fastapi import APIRouter
from pydantic import BaseModel, Field

from services.vector_store import VectorStore
from services.bm25_store import BM25Store


# -- Request/Response models --

class DocumentCreate(BaseModel):
    """Request body for creating a document."""
    title: str
    content: str
    metadata: dict = Field(default_factory=dict)
    permanent: bool = False


class DocumentResponse(BaseModel):
    """Response body after creating a document."""
    id: str


class DocumentListResponse(BaseModel):
    """Response body for listing documents."""
    documents: list[dict]


# -- Router factory --

def create_documents_router(vector_store: VectorStore, bm25_store: BM25Store) -> APIRouter:
    """Create the documents router with injected dependencies."""

    router = APIRouter(prefix="/api/documents", tags=["documents"])


    @router.post("", status_code=201, response_model=DocumentResponse)
    def ingest_document(body: DocumentCreate):
        """Ingest a document into both vector and BM25 stores."""
        doc_id = str(uuid.uuid4())

        vector_store.add(
            doc_id=doc_id,
            title=body.title,
            content=body.content,
            metadata=body.metadata,
            permanent=body.permanent,
        )

        bm25_store.add(
            doc_id=doc_id,
            title=body.title,
            content=body.content,
            metadata=body.metadata,
            permanent=body.permanent,
        )

        return {"id": doc_id}


    @router.get("", response_model=DocumentListResponse)
    def list_documents():
        """List all ingested documents."""
        docs = bm25_store.list_all()
        return {"documents": docs}


    @router.delete("/{doc_id}")
    def delete_document(doc_id: str):
        """Delete a document from both stores."""
        vector_store.delete(doc_id)
        bm25_store.delete(doc_id)
        return {"deleted": doc_id}


    return router
