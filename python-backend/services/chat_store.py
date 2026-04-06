"""
Chat store service — SQLite-backed chat history.

Stores chat conversations and messages in a separate
SQLite database. All chats expire after 30 days.
"""

import os
import sqlite3
import uuid
from datetime import datetime


class ChatStore:
    """SQLite-backed storage for chat conversations and messages."""

    def __init__(self, db_path: str):
        self._db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._init_db()


    def _init_db(self) -> None:
        """Create the chats and messages tables."""
        conn = sqlite3.connect(self._db_path)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS chats (
                id TEXT PRIMARY KEY,
                doc_id TEXT,
                source TEXT,
                created_at TEXT NOT NULL
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (chat_id) REFERENCES chats(id) ON DELETE CASCADE
            )
        """)

        conn.execute("PRAGMA foreign_keys = ON")
        conn.commit()
        conn.close()


    def create_chat(self, doc_id: str | None = None, source: str | None = None) -> str:
        """Create a new chat conversation. Returns the chat ID.

        Args:
            doc_id: Parent document ID (for custom text scope).
            source: Source tag (for sample data scope).
        """
        chat_id = str(uuid.uuid4())

        conn = sqlite3.connect(self._db_path)
        conn.execute(
            "INSERT INTO chats (id, doc_id, source, created_at) VALUES (?, ?, ?, ?)",
            (chat_id, doc_id, source, datetime.utcnow().isoformat()),
        )
        conn.commit()
        conn.close()

        return chat_id


    def get_scope(self, chat_id: str) -> dict:
        """Get the scope (doc_id or source) for a chat."""
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row

        row = conn.execute(
            "SELECT doc_id, source FROM chats WHERE id = ?",
            (chat_id,),
        ).fetchone()

        conn.close()

        if not row:
            return {"doc_id": None, "source": None}

        return {"doc_id": row["doc_id"], "source": row["source"]}


    def add_message(self, chat_id: str, role: str, content: str) -> None:
        """Add a message to a chat."""
        conn = sqlite3.connect(self._db_path)

        conn.execute(
            "INSERT INTO messages (chat_id, role, content, created_at) VALUES (?, ?, ?, ?)",
            (chat_id, role, content, datetime.utcnow().isoformat()),
        )

        conn.commit()
        conn.close()


    def get_history(self, chat_id: str) -> list[dict]:
        """Get all messages for a chat, ordered by creation time."""
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row

        rows = conn.execute(
            "SELECT role, content, created_at FROM messages WHERE chat_id = ? ORDER BY id",
            (chat_id,),
        ).fetchall()

        conn.close()

        return [{"role": row["role"], "content": row["content"], "created_at": row["created_at"]} for row in rows]


    def list_chats(self) -> list[dict]:
        """List all chats with a preview of the first message."""
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row

        rows = conn.execute("""
            SELECT c.id, c.created_at,
                   (SELECT content FROM messages WHERE chat_id = c.id ORDER BY id LIMIT 1) AS preview
            FROM chats c
            ORDER BY c.created_at DESC
        """).fetchall()

        conn.close()

        return [
            {"id": row["id"], "created_at": row["created_at"], "preview": row["preview"] or ""}
            for row in rows
        ]


    def delete_chat(self, chat_id: str) -> None:
        """Delete a chat and all its messages."""
        conn = sqlite3.connect(self._db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("DELETE FROM chats WHERE id = ?", (chat_id,))
        conn.commit()
        conn.close()


    def delete_by_doc_id(self, doc_id: str) -> int:
        """Delete all chats tied to a parent document ID."""
        conn = sqlite3.connect(self._db_path)
        conn.execute("PRAGMA foreign_keys = ON")

        cursor = conn.execute(
            "DELETE FROM chats WHERE doc_id = ?",
            (doc_id,),
        )

        deleted = cursor.rowcount
        conn.commit()
        conn.close()

        return deleted


    def cleanup_expired(self, cutoff: datetime) -> int:
        """Delete all chats created before cutoff. Returns count deleted."""
        conn = sqlite3.connect(self._db_path)
        conn.execute("PRAGMA foreign_keys = ON")

        cursor = conn.execute(
            "DELETE FROM chats WHERE created_at < ?",
            (cutoff.isoformat(),),
        )

        deleted = cursor.rowcount
        conn.commit()
        conn.close()

        return deleted
