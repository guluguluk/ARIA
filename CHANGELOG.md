# Changelog

Development history for ARIA, organized by version.

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
