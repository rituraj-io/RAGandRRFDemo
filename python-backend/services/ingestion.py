"""
Ingestion service — auto-loads HP books on startup.

Checks each book individually against both stores (ChromaDB
and BM25). Only ingests books that are missing or incomplete
in either store. Uses deterministic UUIDs and upsert so
re-ingestion is always safe and idempotent.
"""

import logging
import os
import time
import uuid

from services.bm25_store import BM25Store
from services.chunking import BookData, chunk_chapter, parse_book
from services.embedding import EmbeddingService
from services.vector_store import VectorStore


logger = logging.getLogger(__name__)


# Deterministic namespace for uuid5 generation
_NAMESPACE = uuid.UUID("a1b2c3d4-e5f6-7890-abcd-ef1234567890")

EMBED_BATCH_SIZE = 64
SOURCE_TAG = "hp-books"


def _generate_doc_id(book_number: int, chapter_number: int, chunk_index: int) -> str:
    """Generate a deterministic UUID for a chunk — idempotent on re-ingestion."""
    key = f"{book_number}:{chapter_number}:{chunk_index}"
    return str(uuid.uuid5(_NAMESPACE, key))


def _make_title(book_title: str, chapter_number: int, chapter_title: str, chunk_index: int, total: int) -> str:
    """Format the display title for a chunk."""
    # Use short book name (drop "Harry Potter and the ")
    short = book_title.replace("Harry Potter and the ", "").replace("Harry Potter and ", "")
    return f"{short} — Ch.{chapter_number}: {chapter_title} [{chunk_index + 1}/{total}]"


def _book_needs_ingestion(
    vector_store: VectorStore,
    bm25_store: BM25Store,
    book_number: int,
    expected_chunks: int,
) -> bool:
    """Check if a book is missing or incomplete in either store."""
    chroma_count = vector_store.count_by_metadata({
        "source": SOURCE_TAG,
        "book_number": book_number,
    })
    bm25_count = bm25_store.count_by_source_and_book(SOURCE_TAG, book_number)

    if chroma_count < expected_chunks or bm25_count < expected_chunks:
        logger.info(
            "  Book %d: chroma=%d, bm25=%d, expected=%d — needs ingestion.",
            book_number, chroma_count, bm25_count, expected_chunks,
        )
        return True

    return False


def ingest_hp_books(
    vector_store: VectorStore,
    bm25_store: BM25Store,
    embedding_service: EmbeddingService,
    hp_books_path: str,
) -> None:
    """Ingest HP books that are missing or incomplete in either store.

    Checks each book individually so partial failures resume
    correctly. Uses deterministic IDs + upsert so re-ingesting
    an already-present book is safe (no duplicates).
    """
    if not os.path.isdir(hp_books_path):
        logger.warning("HP books directory not found at %s — skipping ingestion.", hp_books_path)
        return

    # Collect all files sorted by name (1-..., 2-..., etc.)
    book_files = sorted(
        f for f in os.listdir(hp_books_path)
        if f.endswith(".txt")
    )

    if not book_files:
        logger.warning("No .txt files found in %s — skipping ingestion.", hp_books_path)
        return

    start_time = time.time()
    total_ingested = 0
    total_skipped = 0

    for filename in book_files:
        book_number = int(filename.split("-")[0])
        filepath = os.path.join(hp_books_path, filename)

        book = parse_book(filepath, book_number)

        if not book.chapters:
            logger.warning("No chapters found in %s — skipping.", filename)
            continue

        # Chunk all chapters and collect everything
        all_ids = []
        all_titles = []
        all_contents = []
        all_metadatas = []

        for chapter in book.chapters:
            chunks = chunk_chapter(chapter.text)
            total_in_chapter = len(chunks)

            for idx, chunk_text in enumerate(chunks):
                doc_id = _generate_doc_id(book.book_number, chapter.number, idx)

                title = _make_title(
                    book.book_title, chapter.number, chapter.title, idx, total_in_chapter,
                )

                metadata = {
                    "source": SOURCE_TAG,
                    "book_number": book.book_number,
                    "book_title": book.book_title,
                    "chapter_number": chapter.number,
                    "chapter_title": chapter.title,
                    "chunk_index": idx,
                    "total_chunks_in_chapter": total_in_chapter,
                }

                all_ids.append(doc_id)
                all_titles.append(title)
                all_contents.append(chunk_text)
                all_metadatas.append(metadata)

        expected_chunks = len(all_ids)

        # Per-book check: skip only if both stores have all chunks
        if not _book_needs_ingestion(vector_store, bm25_store, book_number, expected_chunks):
            total_skipped += expected_chunks
            continue

        # Batch embed and upsert into both stores
        for batch_start in range(0, len(all_contents), EMBED_BATCH_SIZE):
            batch_end = batch_start + EMBED_BATCH_SIZE

            batch_ids = all_ids[batch_start:batch_end]
            batch_titles = all_titles[batch_start:batch_end]
            batch_contents = all_contents[batch_start:batch_end]
            batch_metas = all_metadatas[batch_start:batch_end]

            embeddings = embedding_service.embed_batch(batch_contents)

            vector_store.add_batch(
                doc_ids=batch_ids,
                titles=batch_titles,
                contents=batch_contents,
                metadatas=batch_metas,
                embeddings=embeddings,
                permanent=True,
            )

            bm25_store.add_batch(
                doc_ids=batch_ids,
                titles=batch_titles,
                contents=batch_contents,
                metadatas=batch_metas,
                permanent=True,
            )

        total_ingested += expected_chunks
        logger.info(
            "  Book %d (%s): %d chapters, %d chunks ingested.",
            book.book_number, book.book_title, len(book.chapters), expected_chunks,
        )

    elapsed = time.time() - start_time

    if total_ingested == 0:
        logger.info("All HP books already present in both stores — nothing to ingest.")
    else:
        logger.info(
            "HP books ingestion complete: %d chunks ingested, %d skipped in %.1fs",
            total_ingested, total_skipped, elapsed,
        )
