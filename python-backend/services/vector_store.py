"""
Vector store service — ChromaDB operations.

Handles adding, searching, listing, deleting, and cleaning up
documents in a persistent ChromaDB collection.
"""

import os
from datetime import datetime

import chromadb

from services.embedding import EmbeddingService


class VectorStore:
    """ChromaDB-backed vector store for document embeddings."""

    def __init__(self, persist_path: str, embedding_service: EmbeddingService):
        os.makedirs(persist_path, exist_ok=True)

        self._client = chromadb.PersistentClient(path=persist_path)
        self._embedding_service = embedding_service
        self._collection = self._client.get_or_create_collection(
            name="documents",
            metadata={"hnsw:space": "cosine"},
        )


    def add(self, doc_id: str, title: str, content: str, metadata: dict, permanent: bool) -> None:
        """Add a document to the vector store."""
        embedding = self._embedding_service.embed(content)

        doc_metadata = {
            **metadata,
            "title": title,
            "permanent": str(permanent).lower(),
            "created_at": datetime.utcnow().isoformat(),
        }

        self._collection.upsert(
            ids=[doc_id],
            embeddings=[embedding],
            documents=[content],
            metadatas=[doc_metadata],
        )


    def search(self, query: str, limit: int = 10) -> list[dict]:
        """Search documents by vector similarity. Returns ranked results."""
        query_embedding = self._embedding_service.embed(query)

        results = self._collection.query(
            query_embeddings=[query_embedding],
            n_results=limit,
            include=["documents", "metadatas", "distances"],
        )

        output = []
        for i in range(len(results["ids"][0])):
            meta = results["metadatas"][0][i]
            output.append({
                "id": results["ids"][0][i],
                "title": meta.get("title", ""),
                "content": results["documents"][0][i],
                "score": 1 - results["distances"][0][i],
                "metadata": {k: v for k, v in meta.items() if k not in ("title", "permanent", "created_at")},
            })

        return output


    def delete(self, doc_id: str) -> None:
        """Delete a document by ID."""
        self._collection.delete(ids=[doc_id])


    def list_all(self) -> list[dict]:
        """List all documents in the store."""
        results = self._collection.get(include=["documents", "metadatas"])

        output = []
        for i in range(len(results["ids"])):
            meta = results["metadatas"][i]
            output.append({
                "id": results["ids"][i],
                "title": meta.get("title", ""),
                "content": results["documents"][i],
                "permanent": meta.get("permanent", "false") == "true",
                "metadata": {k: v for k, v in meta.items() if k not in ("title", "permanent", "created_at")},
            })

        return output


    def cleanup_expired(self, cutoff: datetime) -> int:
        """Delete non-permanent documents created before cutoff. Returns count deleted."""
        results = self._collection.get(include=["metadatas"])
        to_delete = []

        for i, meta in enumerate(results["metadatas"]):
            if meta.get("permanent", "false") == "true":
                continue

            created_at = datetime.fromisoformat(meta.get("created_at", datetime.utcnow().isoformat()))
            if created_at < cutoff:
                to_delete.append(results["ids"][i])

        if to_delete:
            self._collection.delete(ids=to_delete)

        return len(to_delete)
