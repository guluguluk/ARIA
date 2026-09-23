"""
SQLite-backed permanent memory store for ARIA.
Enables local persistent storage of preferences, facts, and notes.
"""

import sqlite3
import os
from typing import Dict, Optional, Any
from pathlib import Path

class MemoryStore:
    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize the MemoryStore with a configurable SQLite database path.
        Defaults to 'aria_memory.db' in the project directory if not specified.
        """
        if db_path is None:
            base_dir = Path(__file__).resolve().parent.parent.parent
            db_path = str(base_dir / "aria_memory.db")
        
        self.db_path = db_path
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        """Create the memories table if it does not exist."""
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)

        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS memories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    memory_key TEXT UNIQUE NOT NULL,
                    content TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()

    def store_memory(self, key: str, content: str) -> bool:
        """
        Store a new memory or update it if the key already exists (upsert).
        Returns True on success.
        """
        if not key or not isinstance(key, str) or not key.strip():
            raise ValueError("Memory key must be a non-empty string.")
        if content is None or not isinstance(content, str):
            raise ValueError("Memory content must be a valid string.")

        cleaned_key = key.strip()
        cleaned_content = content.strip()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO memories (memory_key, content, created_at, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                ON CONFLICT(memory_key) DO UPDATE SET
                    content = excluded.content,
                    updated_at = CURRENT_TIMESTAMP
            """, (cleaned_key, cleaned_content))
            conn.commit()
        return True

    def get_memory(self, key: str) -> Optional[str]:
        """
        Retrieve memory content by key. Returns None if not found.
        """
        if not key or not isinstance(key, str):
            return None

        cleaned_key = key.strip()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT content FROM memories WHERE memory_key = ?", (cleaned_key,))
            row = cursor.fetchone()
            if row:
                return row["content"]
        return None

    def update_memory(self, key: str, content: str) -> bool:
        """
        Update an existing memory's content. Returns True if updated, False if not found.
        """
        if not key or not isinstance(key, str) or not isinstance(content, str):
            raise ValueError("Invalid key or content for update.")

        cleaned_key = key.strip()
        cleaned_content = content.strip()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE memories
                SET content = ?, updated_at = CURRENT_TIMESTAMP
                WHERE memory_key = ?
            """, (cleaned_content, cleaned_key))
            conn.commit()
            return cursor.rowcount > 0

    def delete_memory(self, key: str) -> bool:
        """
        Delete a memory by key. Returns True if deleted, False if not found.
        """
        if not key or not isinstance(key, str):
            return False

        cleaned_key = key.strip()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM memories WHERE memory_key = ?", (cleaned_key,))
            conn.commit()
            return cursor.rowcount > 0

    def list_memories(self) -> Dict[str, str]:
        """
        Return a dictionary mapping all memory keys to their contents.
        """
        results = {}
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT memory_key, content FROM memories ORDER BY updated_at DESC")
            for row in cursor.fetchall():
                results[row["memory_key"]] = row["content"]
        return results

    def clear_all(self, confirm: bool = False) -> None:
        """
        Clear all stored memories. Requires confirm=True as a safety guard
        to prevent accidental usage in normal operation.
        """
        if not confirm:
            raise PermissionError(
                "clear_all() requires confirm=True to prevent accidental data loss."
            )
        with self._get_connection() as conn:
            conn.execute("DELETE FROM memories")
            conn.commit()
