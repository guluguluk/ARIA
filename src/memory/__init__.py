"""
Permanent Memory package for ARIA.
Provides local persistent storage using SQLite.
"""

from .context_builder import (
	MAX_CONTEXT_CHARACTERS,
	MAX_CONTEXT_ENTRIES,
	build_memory_context,
)
from .retrieval import (
	MAX_RELEVANT_MEMORIES,
	MemoryRetrievalResult,
	RetrievedMemory,
	retrieve_relevant_memories,
)
from .store import MemoryStore, canonicalize_memory_key

__all__ = [
	"MAX_CONTEXT_CHARACTERS",
	"MAX_CONTEXT_ENTRIES",
	"MAX_RELEVANT_MEMORIES",
	"MemoryRetrievalResult",
	"MemoryStore",
	"RetrievedMemory",
	"build_memory_context",
	"canonicalize_memory_key",
	"retrieve_relevant_memories",
]
