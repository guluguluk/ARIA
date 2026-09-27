"""Deterministic, local retrieval of relevant permanent memories."""

import re
import sqlite3
from dataclasses import dataclass

from .store import MemoryStore, canonicalize_memory_key


MAX_RELEVANT_MEMORIES = 5


@dataclass(frozen=True)
class RetrievedMemory:
    key: str
    content: str


@dataclass(frozen=True)
class MemoryRetrievalResult:
    success: bool
    memories: tuple[RetrievedMemory, ...] = ()


def retrieve_relevant_memories(
    query: str, memory_store: MemoryStore
) -> MemoryRetrievalResult:
    """Return bounded memories whose complete canonical keys occur in the query."""
    if not isinstance(query, str) or not query.strip():
        return MemoryRetrievalResult(success=True)

    normalized_query = re.sub(r"[_\s]+", " ", query.casefold()).strip()

    try:
        stored_memories = memory_store.list_memories()
    except (sqlite3.Error, OSError):
        return MemoryRetrievalResult(success=False)

    canonical_memories = {}
    for key in sorted(stored_memories, key=lambda value: (value.casefold(), value)):
        canonical_key = canonicalize_memory_key(key)
        if canonical_key and canonical_key not in canonical_memories:
            canonical_memories[canonical_key] = RetrievedMemory(
                key=key,
                content=stored_memories[key],
            )

    occurrences = []
    for canonical_key, memory in canonical_memories.items():
        key_pattern = rf"(?<!\w){re.escape(canonical_key)}(?!\w)"
        occurrences.extend(
            (match.start(), match.end(), canonical_key, memory)
            for match in re.finditer(key_pattern, normalized_query)
        )

    occurrences.sort(
        key=lambda occurrence: (
            occurrence[0],
            -(occurrence[1] - occurrence[0]),
            occurrence[2],
            occurrence[3].key.casefold(),
            occurrence[3].key,
        )
    )

    selected = []
    occupied_spans = []
    selected_keys = set()
    for start, end, canonical_key, memory in occurrences:
        overlaps_existing = any(
            start < existing_end and existing_start < end
            for existing_start, existing_end in occupied_spans
        )
        if overlaps_existing or canonical_key in selected_keys:
            continue
        selected.append(memory)
        occupied_spans.append((start, end))
        selected_keys.add(canonical_key)

    selected.sort(
        key=lambda memory: (
            canonicalize_memory_key(memory.key),
            memory.key.casefold(),
            memory.key,
        )
    )
    return MemoryRetrievalResult(
        success=True,
        memories=tuple(selected[:MAX_RELEVANT_MEMORIES]),
    )