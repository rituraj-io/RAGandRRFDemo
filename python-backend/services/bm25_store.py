"""
BM25 store service — SQLite FTS5 operations.

Handles adding, searching, listing, deleting, and cleaning up
documents in a SQLite database with FTS5 full-text search.
"""

import json
import os
import sqlite3
from datetime import datetime


class BM25Store:
    """SQLite FTS5-backed store for BM25 keyword search."""

    def __init__(self, db_path: str):
        self._db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._init_db()


    def _init_db(self) -> None:
        """Create the documents table and FTS5 virtual table."""
        conn = sqlite3.connect(self._db_path)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                metadata TEXT NOT NULL DEFAULT '{}',
                permanent INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL
            )
        """)

        conn.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS documents_fts
            USING fts5(title, content, content=documents, content_rowid=rowid)
        """)

        # Triggers to keep FTS5 index in sync with documents table
        conn.execute("""
            CREATE TRIGGER IF NOT EXISTS documents_ai AFTER INSERT ON documents BEGIN
                INSERT INTO documents_fts(rowid, title, content)
                VALUES (new.rowid, new.title, new.content);
            END
        """)

        conn.execute("""
            CREATE TRIGGER IF NOT EXISTS documents_ad AFTER DELETE ON documents BEGIN
                INSERT INTO documents_fts(documents_fts, rowid, title, content)
                VALUES ('delete', old.rowid, old.title, old.content);
            END
        """)

        conn.execute("""
            CREATE TRIGGER IF NOT EXISTS documents_au AFTER UPDATE ON documents BEGIN
                INSERT INTO documents_fts(documents_fts, rowid, title, content)
                VALUES ('delete', old.rowid, old.title, old.content);
                INSERT INTO documents_fts(rowid, title, content)
                VALUES (new.rowid, new.title, new.content);
            END
        """)

        conn.commit()
        conn.close()


    def add(self, doc_id: str, title: str, content: str, metadata: dict, permanent: bool) -> None:
        """Add a document to the BM25 store."""
        conn = sqlite3.connect(self._db_path)

        conn.execute(
            """
            INSERT OR REPLACE INTO documents (id, title, content, metadata, permanent, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (doc_id, title, content, json.dumps(metadata), int(permanent), datetime.utcnow().isoformat()),
        )

        conn.commit()
        conn.close()


    def add_batch(
        self,
        doc_ids: list[str],
        titles: list[str],
        contents: list[str],
        metadatas: list[dict],
        permanent: bool,
    ) -> None:
        """Add multiple documents in a single transaction."""
        conn = sqlite3.connect(self._db_path)
        now = datetime.utcnow().isoformat()

        conn.executemany(
            """
            INSERT OR REPLACE INTO documents (id, title, content, metadata, permanent, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            [
                (doc_id, title, content, json.dumps(meta), int(permanent), now)
                for doc_id, title, content, meta in zip(doc_ids, titles, contents, metadatas)
            ],
        )

        conn.commit()
        conn.close()


    def count_by_source_and_book(self, source: str, book_number: int) -> int:
        """Count documents matching a source tag and book number in metadata."""
        conn = sqlite3.connect(self._db_path)

        count = conn.execute(
            """
            SELECT COUNT(*) FROM documents
            WHERE json_extract(metadata, '$.source') = ?
              AND json_extract(metadata, '$.book_number') = ?
            """,
            (source, book_number),
        ).fetchone()[0]

        conn.close()
        return count


    def search(self, query: str, limit: int = 10, doc_id: str | None = None, source: str | None = None) -> list[dict]:
        """Search documents using FTS5 BM25 ranking.

        Args:
            query: Search query text.
            limit: Max results to return.
            doc_id: Filter to chunks belonging to this parent document.
            source: Filter to chunks with this source tag in metadata.
        """
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row

        sql = """
            SELECT d.id, d.title, d.content, d.metadata,
                   bm25(documents_fts) AS score
            FROM documents_fts
            JOIN documents d ON d.rowid = documents_fts.rowid
            WHERE documents_fts MATCH ?
        """
        params: list = [query]

        if doc_id:
            sql += " AND json_extract(d.metadata, '$.doc_id') = ?"
            params.append(doc_id)

        if source:
            sql += " AND json_extract(d.metadata, '$.source') = ?"
            params.append(source)

        sql += " ORDER BY score LIMIT ?"
        params.append(limit)

        rows = conn.execute(sql, params).fetchall()
        conn.close()

        return [
            {
                "id": row["id"],
                "title": row["title"],
                "content": row["content"],
                "score": -row["score"],
                "metadata": json.loads(row["metadata"]),
            }
            for row in rows
        ]


    def delete(self, doc_id: str) -> None:
        """Delete a document by ID."""
        conn = sqlite3.connect(self._db_path)
        conn.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
        conn.commit()
        conn.close()


    def delete_by_doc_id(self, doc_id: str) -> int:
        """Delete all chunks belonging to a parent document ID."""
        conn = sqlite3.connect(self._db_path)

        cursor = conn.execute(
            "DELETE FROM documents WHERE json_extract(metadata, '$.doc_id') = ?",
            (doc_id,),
        )

        deleted = cursor.rowcount
        conn.commit()
        conn.close()

        return deleted


    def list_all(self) -> list[dict]:
        """List all documents."""
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row

        rows = conn.execute(
            "SELECT id, title, content, metadata, permanent FROM documents"
        ).fetchall()

        conn.close()

        return [
            {
                "id": row["id"],
                "title": row["title"],
                "content": row["content"],
                "permanent": bool(row["permanent"]),
                "metadata": json.loads(row["metadata"]),
            }
            for row in rows
        ]


    def cleanup_expired(self, cutoff: datetime) -> int:
        """Delete non-permanent documents created before cutoff. Returns count deleted."""
        conn = sqlite3.connect(self._db_path)

        cursor = conn.execute(
            "DELETE FROM documents WHERE permanent = 0 AND created_at < ?",
            (cutoff.isoformat(),),
        )

        deleted = cursor.rowcount
        conn.commit()
        conn.close()

        return deleted
