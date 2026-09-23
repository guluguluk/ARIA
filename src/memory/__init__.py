"""
Permanent Memory package for ARIA.
Provides local persistent storage using SQLite.
"""

from .store import MemoryStore

__all__ = ["MemoryStore"]
