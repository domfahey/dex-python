# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Deduplication engine with level 1/2/3 matching, clustering, and merge utilities (`src/dex_import/deduplication.py`).
- Scripts for duplicate analysis, flagging, review, and resolution (`analyze_duplicates.py`, `flag_duplicates.py`, `review_duplicates.py`, `resolve_duplicates.py`).
- Async sync tool with integrity hashing, incremental updates, and progress output (`sync_with_integrity.py`).
- Deduplication plan documentation (`DEDUPLICATION_PLAN.md`).
- Structured deduplication tests and live API integration tests under `tests/deduplication` and `tests/integration`.
- New dependencies for deduplication and CLI UX (`jellyfish`, `networkx`, `rich`) plus `types-networkx`.

### Fixed
- AsyncDexClient `max_retries` default now matches sync client (0)
- Write operations return normalized entity data instead of raw API wrappers
- Paginated methods properly extract total counts from nested API responses

### Changed
- `main.py` now syncs all contacts to SQLite with normalized `contacts`, `emails`, and `phones` tables.
- Test layout and Makefile targets updated to the new suite locations; pytest defaults now exclude integration tests.
- Documentation expanded with retry and error-handling guidance in `README.md` and `docs/api.md`; `.env.example` now includes `DEX_BASE_URL`.
- Updated `.gitignore` to exclude database files (`*.db`, `*.sqlite`) and data exports (`*.csv`, `*.json`).

### Removed
- Legacy test modules replaced by the structured test suite (`tests/test_client.py`, `tests/test_models.py`, `tests/test_retry.py`, `tests/test_exceptions.py`, `tests/test_async_client.py`, `tests/test_integration.py`).

## [0.1.0] - 2025-01-19

### Added

#### Core Client (418288d)
- `DexClient` synchronous client for Dex CRM API
- Full CRUD operations for contacts, reminders, and notes (15 endpoints)
- Context manager support
- `Settings` configuration with pydantic-settings
- Environment variable support (`DEX_API_KEY`, `DEX_BASE_URL`)
- Base Pydantic models: `Contact`, `ContactCreate`, `Reminder`, `ReminderCreate`, `Note`, `NoteCreate`
- Unit tests with pytest-httpx mocking
- Integration tests against live API

#### Update Models (5492bb4)
- `ReminderUpdate` model with `mark_complete()` factory method
- `NoteUpdate` model for timeline item updates
- `PaginatedContacts`, `PaginatedReminders`, `PaginatedNotes` with `has_more` property
- `ContactUpdate` model with field aliasing
- Refactored `update_reminder()` to accept `ReminderUpdate` model
- Refactored `update_note()` to accept `NoteUpdate` model

#### Custom Exceptions (bba359a)
- `DexAPIError` base exception with `status_code` and `response_data`
- `AuthenticationError` for 401 responses
- `ContactNotFoundError`, `ReminderNotFoundError`, `NoteNotFoundError` for 404 responses
- `RateLimitError` for 429 responses with optional `retry_after`
- `ValidationError` for 400 responses
- Client error handling to raise appropriate exceptions

#### Async Client (a792cae)
- `AsyncDexClient` with all async versions of DexClient methods
- Async context manager support (`async with`)
- Shared error handling with sync client

#### Retry Logic (94da346)
- `max_retries` parameter for configurable retry attempts
- `retry_delay` parameter for base delay (exponential backoff)
- Automatic retry on transient errors (429, 500, 502, 503, 504)
- No retry on client errors (400, 401, 404)

### Documentation (2268bd2)
- Updated API reference with all client methods
- Documented Reminders API and Notes API sections
- Added model documentation with field descriptions
- Added factory method examples

### Changed

#### Housekeeping (807203f, 5d3987d)
- Added `.claude/settings.local.json` to `.gitignore`
- Removed local settings from git tracking

[unreleased]: https://github.com/user/dexImport/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/user/dexImport/releases/tag/v0.1.0
