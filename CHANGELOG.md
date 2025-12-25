# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

#### OpenRefine-Inspired Deduplication
- `fingerprint.py` module with OpenRefine-style keying functions
  - `fingerprint()` - Normalize, sort tokens, remove punctuation, unicode→ASCII
  - `ngram_fingerprint()` - N-gram fingerprints for typo detection
  - `normalize_phone()` - Strip formatting, extract digits only
  - `normalized_levenshtein()` - Edit distance as 0.0-1.0 score
  - `ensemble_similarity()` - Weighted Jaro-Winkler + Levenshtein
- Level 1.5b: Fingerprint name matching
  - Catches reordered names: "Tom Cruise" ↔ "Cruise, Tom"
  - Normalizes unicode: "José García" ↔ "Jose Garcia"
  - Removes punctuation: "O'Brien" ↔ "OBrien"
- Phone normalization in duplicate detection
  - "(555) 123-4567" now matches "555-123-4567"
- 44 new unit tests for fingerprinting (TDD approach)

#### Duplicate Review Enhancements
- 'Open in Dex' option in duplicate review tool for quick web access
- Smart search term generation for Dex duplicate lookup (uses last name for better specificity)

#### Performance Optimizations
- Database indexes for deduplication queries
- Batch operations to eliminate N+1 queries
- Optimized deduplication helper functions

### Changed
- `find_phone_duplicates()` now normalizes phone formats before matching
- `analyze_duplicates.py` includes Level 1.5b fingerprint analysis in reports
- Makefile refactored following best practices
- Improved variable naming in deduplication and sync modules for readability
- Request models now forbid unknown fields and accept datetime inputs for timestamps
- Nested response fields use typed models for emails, phones, and contacts

### Fixed
- Line length compliance with 88 character limit
- Linting issues in test files
- Reminder and note update payloads no longer include path IDs

### Dependencies
- Added `unidecode>=1.3.0` for unicode→ASCII normalization

### Documentation
- Comprehensive docstrings added to all source modules

## [0.2.0] - 2025-12-21

Major release with package rename, deduplication engine, and project reorganization.

### Added

#### Deduplication Engine
- Level 1: Exact email and phone matching
- Level 1.5: Birthday + name matching
- Level 2: Exact name + job title matching
- Level 3: Fuzzy name matching with Jaro-Winkler and Soundex
- Clustering algorithm to group related duplicates
- Merge utilities to consolidate duplicate records

#### Enrichment
- Name parsing with probablepeople integration
- Job title parsing to extract company and role
- Sync-back functionality to push enrichments to Dex API

#### CLI Scripts
- `scripts/sync_with_integrity.py` - Incremental sync with hash-based change detection
- `scripts/analyze_duplicates.py` - Generate duplicate analysis reports
- `scripts/flag_duplicates.py` - Mark duplicate candidates in database
- `scripts/review_duplicates.py` - Interactive duplicate review
- `scripts/resolve_duplicates.py` - Merge confirmed duplicates
- `scripts/sync_enrichment_back.py` - Push enrichments to Dex API

#### Infrastructure
- GitHub issue and PR templates
- `make sync` - Run incremental sync
- `make analyze` - Run duplicate analysis
- `make doctor` - Verify environment and dependencies
- Faker for test data generation

### Changed
- **BREAKING**: Package renamed from `dex_import` to `dex_python`
- **BREAKING**: Import path changed from `from src.dex_import` to `from dex_python`
- Scripts moved to `scripts/` directory
- Documentation reorganized into `docs/` with `docs/planning/` for internal docs

### Fixed
- `AsyncDexClient` `max_retries` default now matches sync client (0)
- Write operations return normalized entity data instead of raw API wrappers
- Paginated methods properly extract total counts from nested API responses
- Database updates preserve deduplication metadata
- Empty/whitespace names filtered in fuzzy matching

### Security
- Security audit completed before public release
- `.gitignore` patterns for sensitive data exports
- Removed PII from git history

## [0.1.0] - 2025-12-19

Initial release of the Dex Python SDK.

### Added

#### Core Client
- `DexClient` - Synchronous client for [Dex CRM API](https://getdex.com/docs/api-reference)
- Full CRUD operations for contacts, reminders, and notes (15 endpoints)
- Context manager support (`with DexClient() as client:`)
- `Settings` configuration via pydantic-settings
- Environment variable support (`DEX_API_KEY`, `DEX_BASE_URL`)

#### Async Client
- `AsyncDexClient` - Async version of all client methods
- Async context manager support (`async with AsyncDexClient() as client:`)

#### Data Models
- `Contact`, `ContactCreate`, `ContactUpdate`
- `Reminder`, `ReminderCreate`, `ReminderUpdate` with `mark_complete()` factory
- `Note`, `NoteCreate`, `NoteUpdate`
- `PaginatedContacts`, `PaginatedReminders`, `PaginatedNotes` with `has_more` property

#### Error Handling
- `DexAPIError` - Base exception with `status_code` and `response_data`
- `AuthenticationError` - 401 responses
- `RateLimitError` - 429 responses with `retry_after`
- `ValidationError` - 400 responses
- `ContactNotFoundError`, `ReminderNotFoundError`, `NoteNotFoundError` - 404 responses

#### Retry Logic
- Configurable `max_retries` and `retry_delay` parameters
- Exponential backoff on transient errors (429, 500, 502, 503, 504)
- No retry on client errors (400, 401, 404)

#### Testing
- Unit tests with pytest-httpx mocking (160+ tests)
- Integration tests against live API
- Strict mypy type checking

#### Documentation
- API reference with usage examples
- Getting started guide
- MIT License
- Contributing guidelines
- Security policy

[unreleased]: https://github.com/domfahey/dex-python/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/domfahey/dex-python/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/domfahey/dex-python/releases/tag/v0.1.0
