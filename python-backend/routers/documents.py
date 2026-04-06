"""
Documents router — ingest, list, and delete documents.

Ingestion chunks the text and stores each chunk in both
ChromaDB (vector) and SQLite FTS5 (BM25) with a shared doc_id.
"""

import uuid

from fastapi import APIRouter
from pydantic import BaseModel

from services.vector_store import VectorStore
from services.bm25_store import BM25Store
from services.embedding import EmbeddingService
from services.chat_store import ChatStore
from services.chunking import chunk_custom_text


# -- Request/Response models --

class DocumentCreate(BaseModel):
    """Request body for creating a document."""
    title: str
    content: str


class DocumentResponse(BaseModel):
    """Response body after creating a document."""
    doc_id: str
    chunks: int


class DocumentListResponse(BaseModel):
    """Response body for listing documents."""
    documents: list[dict]


# -- Router factory --

def create_documents_router(
    vector_store: VectorStore,
    bm25_store: BM25Store,
    embedding_service: EmbeddingService,
    chat_store: ChatStore,
) -> APIRouter:
    """Create the documents router with injected dependencies."""

    router = APIRouter(prefix="/api/documents", tags=["documents"])


    @router.post("", status_code=201, response_model=DocumentResponse)
    def ingest_document(body: DocumentCreate):
        """Ingest a document — chunks text and stores in both stores."""
        doc_id = str(uuid.uuid4())
        chunks = chunk_custom_text(body.content)

        if not chunks:
            return {"doc_id": doc_id, "chunks": 0}

        # Batch embed all chunks
        embeddings = embedding_service.embed_batch(chunks)

        # Build per-chunk data
        chunk_ids = [str(uuid.uuid4()) for _ in chunks]
        titles = [f"{body.title} [{i + 1}/{len(chunks)}]" for i in range(len(chunks))]
        metadatas = [{"doc_id": doc_id, "chunk_index": i} for i in range(len(chunks))]

        # Store in vector store
        vector_store.add_batch(
            doc_ids=chunk_ids,
            titles=titles,
            contents=chunks,
            metadatas=metadatas,
            embeddings=embeddings,
            permanent=False,
        )

        # Store in BM25 store
        bm25_store.add_batch(
            doc_ids=chunk_ids,
            titles=titles,
            contents=chunks,
            metadatas=metadatas,
            permanent=False,
        )

        return {"doc_id": doc_id, "chunks": len(chunks)}


    @router.get("", response_model=DocumentListResponse)
    def list_documents():
        """List all ingested documents."""
        docs = bm25_store.list_all()
        return {"documents": docs}


    @router.delete("/{doc_id}")
    def delete_document(doc_id: str):
        """Delete a document and all its chunks from both stores."""
        vector_store.delete_by_doc_id(doc_id)
        bm25_store.delete_by_doc_id(doc_id)
        chat_store.delete_by_doc_id(doc_id)
        return {"deleted": doc_id}


    return router
