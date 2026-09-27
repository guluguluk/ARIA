"""
Permanent Memory package for ARIA.
Provides local persistent storage using SQLite.
"""

from .retrieval import (
	MAX_RELEVANT_MEMORIES,
	MemoryRetrievalResult,
	RetrievedMemory,
	retrieve_relevant_memories,
)
from .store import MemoryStore, canonicalize_memory_key

__all__ = [
	"MAX_RELEVANT_MEMORIES",
	"MemoryRetrievalResult",
	"MemoryStore",
	"RetrievedMemory",
	"canonicalize_memory_key",
	"retrieve_relevant_memories",
]
