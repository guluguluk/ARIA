# Changelog

Development history for ARIA, organized by version.

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
