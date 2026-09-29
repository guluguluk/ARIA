# Changelog

Development history for ARIA, organized by version.

## v1.1.1 - Oblivion (2026-09-29)

### Memory Reliability and Safety

- Added memory-to-Gemini integration tests for instruction-like and malformed stored content, bounded truncation, empty-store behavior, and separation of conversation history from persistent memory.

## v1.1.0 - Oblivion (2026-09-28)

### Memory and Gemini Integration

- Connected the existing deterministic memory retrieval and bounded context builder to ordinary Gemini requests.
- Added prompt safeguards that mark retrieved memories as reference data and prevent them from overriding system rules, safety behavior, routing, tools, or the user's current request.
- Continued Gemini requests without memory context when no relevant memory exists or retrieval reports a database failure.
- Preserved explicit memory commands, existing Gemini error handling, and the no-automatic-memory-write behavior.

### Testing and Validation

- Added mocked integration tests for relevant and irrelevant memories, retrieval failures, reference-data handling, Gemini 503 handling, explicit memory commands, and normal conversations.

## v1.0.4 - ARIA-Genesis-Prime (2026-09-27)

### Memory Retrieval and Context

- Hardened deterministic memory retrieval with canonical key matching, longest-match handling for overlapping keys, and stable result ordering.
- Added a standalone context builder that consumes structured retrieval results and treats memory contents as reference data, not instructions.
- Bounded generated memory context to five entries and 4,096 characters; kept it separate from Gemini integration.

### Testing and Validation

- Added retrieval and context-builder tests for canonicalization, overlap, limits, ordering, live store changes, failures, formatting, and data handling.

## v1.0.3 - ARIA-Genesis-Prime

### Reliability Improvements

- Added controlled handling for temporary Gemini API failures with HTTP status codes 408, 429, 500, 502, 503, and 504.
- Kept ARIA's command session available after handled Gemini failures without exposing SDK error details to the user.
- Preserved normal Gemini responses and allowed non-temporary API errors to remain visible during development.

### Memory Retrieval

- Added an independent deterministic retrieval API using canonicalized, complete memory-key phrase matching.
- Bounded retrieval to five results and ordered matches deterministically.
- Returned structured results that distinguish an empty match from a retrieval failure without exposing database error details.
- Kept retrieval separate from Gemini; retrieved memories are not added to Gemini requests.

### Testing and Validation

- Added mocked Gemini API tests for successful responses, service unavailability, rate limiting, and non-temporary API errors.
- Added tests verifying safe failure responses and continued command processing after a Gemini failure.
- Added memory retrieval tests for key matching, canonicalization, result limits, deterministic ordering, current store updates and deletions, empty stores, and database failures.

## v1.0.2 - ARIA-Genesis-Prime

### New Features

- Added canonical memory-key normalization for equivalent forms such as `favorite_game`, `favorite game`, and `my favorite game`.
- Improved explicit permanent-memory command handling for retrieval, deletion, and update flows.

### Bug Fixes

- Fixed inconsistent memory-key lookups between storage and retrieval paths.
- Fixed equivalent-key deletion behavior so `forget my favorite game` resolves the same canonical key as `favorite_game`.
- Improved malformed command handling so invalid memory commands return deterministic local responses instead of falling through unexpectedly.

### Architecture Changes

- Centralized memory-key normalization logic to keep storage, retrieval, and deletion behavior consistent.
- Kept memory ownership within ARIA Core and did not broaden the system beyond explicit user-controlled memory actions.

### Important Improvements

- Strengthened memory reliability for repeated keys and equivalent key variants.
- Improved user-facing memory command UX by handling malformed inputs more predictably.

### Testing and Validation

- Added memory-key normalization regression tests.
- Added tests for memory update behavior and malformed memory-command handling.
- Verified the complete project test suite remained passing.

## v1.0.1 - ARIA-Genesis-Prime

### New Features

- Added Gemini API integration using an environment-provided API key.
- Added local Gemma and Qwen model integrations.
- Added command routing for ARIA requests.
- Added a modular tool system with tool registration, validation, and dispatch.
- Added explicit permanent-memory commands for storing, retrieving, listing, and deleting memories.
- Added SQLite-backed persistent memory through `MemoryStore`.

### Architecture Changes

- Refactored ARIA command processing around routing and model selection.
- Separated tool registration from tool execution.
- Separated permanent memory from model-specific conversation handling.
- Added configurable SQLite database path support for permanent memory.

### Important Improvements

- Added environment-based API credential loading.
- Added SQLite database ignore rules.
- Removed the local memory database from Git tracking.

### Testing and Validation

- Added unit tests for routing behavior.
- Added unit tests for tool registration, validation, and dispatch.
- Added unit tests for SQLite memory storage.
- Added integration tests for ARIA permanent-memory commands.
