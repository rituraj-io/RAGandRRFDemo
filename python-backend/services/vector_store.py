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


    def add_batch(
        self,
        doc_ids: list[str],
        titles: list[str],
        contents: list[str],
        metadatas: list[dict],
        embeddings: list[list[float]],
        permanent: bool,
    ) -> None:
        """Add multiple documents with pre-computed embeddings."""
        now = datetime.utcnow().isoformat()

        chroma_metas = [
            {
                **meta,
                "title": title,
                "permanent": str(permanent).lower(),
                "created_at": now,
            }
            for meta, title in zip(metadatas, titles)
        ]

        self._collection.upsert(
            ids=doc_ids,
            embeddings=embeddings,
            documents=contents,
            metadatas=chroma_metas,
        )


    def count_by_metadata(self, where: dict) -> int:
        """Count documents matching a metadata filter."""
        results = self._collection.get(where=where, include=[])
        return len(results["ids"])


    def search(self, query: str, limit: int = 10, where: dict | None = None) -> list[dict]:
        """Search documents by vector similarity. Returns ranked results.

        Args:
            query: Search query text.
            limit: Max results to return.
            where: Optional ChromaDB metadata filter dict.
        """
        query_embedding = self._embedding_service.embed(query)

        query_kwargs = {
            "query_embeddings": [query_embedding],
            "n_results": limit,
            "include": ["documents", "metadatas", "distances"],
        }

        if where:
            query_kwargs["where"] = where

        results = self._collection.query(**query_kwargs)

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


    def delete_by_doc_id(self, doc_id: str) -> int:
        """Delete all chunks belonging to a parent document ID."""
        results = self._collection.get(
            where={"doc_id": doc_id},
            include=[],
        )
        chunk_ids = results["ids"]

        if chunk_ids:
            self._collection.delete(ids=chunk_ids)

        return len(chunk_ids)


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
