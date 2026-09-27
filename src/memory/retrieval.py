"""Deterministic, local retrieval of relevant permanent memories."""

import re
import sqlite3
from dataclasses import dataclass

from .store import canonicalize_memory_key


MAX_RELEVANT_MEMORIES = 5


@dataclass(frozen=True)
class RetrievedMemory:
    key: str
    content: str


@dataclass(frozen=True)
class MemoryRetrievalResult:
    success: bool
    memories: tuple[RetrievedMemory, ...] = ()


def retrieve_relevant_memories(query: str, memory_store) -> MemoryRetrievalResult:
    """Return bounded memories whose complete canonical keys occur in the query."""
    if not isinstance(query, str) or not query.strip():
        return MemoryRetrievalResult(success=True)

    normalized_query = re.sub(r"[_\s]+", " ", query.casefold()).strip()

    try:
        stored_memories = memory_store.list_memories()
    except (sqlite3.Error, OSError):
        return MemoryRetrievalResult(success=False)

    matches = []
    for key, content in stored_memories.items():
        canonical_key = canonicalize_memory_key(key)
        if not canonical_key:
            continue

        key_pattern = rf"(?<!\w){re.escape(canonical_key)}(?!\w)"
        if re.search(key_pattern, normalized_query):
            matches.append(RetrievedMemory(key=key, content=content))

    matches.sort(
        key=lambda memory: (
            canonicalize_memory_key(memory.key),
            memory.key.casefold(),
            memory.key,
        )
    )
    return MemoryRetrievalResult(
        success=True,
        memories=tuple(matches[:MAX_RELEVANT_MEMORIES]),
    )