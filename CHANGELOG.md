# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

#### Unified CLI
- New `dex` command-line interface using Typer
  - `dex sync incremental` - Incremental sync preserving dedup metadata
  - `dex sync full` - Full sync (destructive)
  - `dex duplicate analyze` - Generate duplicate analysis report
  - `dex duplicate flag` - Flag duplicate candidates
  - `dex duplicate review` - Interactive duplicate review
  - `dex duplicate resolve` - Merge confirmed duplicates
  - `dex enrichment backfill` - Parse job titles for company/role
  - `dex enrichment push` - Push enrichment data to API
- Standardized CLI options: `--db-path`, `--data-dir`, `--verbose`, `--dry-run`, `--force`
- Entry point: `dex = "dex_python.cli:app"`

#### SQLAlchemy + Alembic Migrations
- SQLAlchemy ORM models matching existing schema (`dex_python.db.models`)
  - `Contact`, `Email`, `Phone`, `Reminder`, `Note` models
  - `ReminderContact`, `NoteContact` many-to-many link tables
  - All indexes defined in model `__table_args__`
- Alembic migration infrastructure
  - `render_as_batch=True` for SQLite compatibility
  - Autogenerate support for schema changes
  - Initial migration codifying current schema
- Session management utilities (`dex_python.db.session`)

#### International Phone Normalization (E.164)
- `normalize_phone_e164()` - Full international phone parsing via `phonenumbers` library
  - Supports all countries with proper E.164 formatting
  - `default_region` parameter for numbers without country code
  - `strict` mode for validation (returns empty for invalid numbers)
- `format_phone()` - Format phones as E.164, national, or international
  - National: `(555) 123-4567`
  - International: `+1 555-123-4567`
  - E.164: `+15551234567`

#### LinkedIn URL Normalization
- `normalize_linkedin()` - Canonicalize LinkedIn profile URLs
  - Handles full URLs, short URLs, and usernames
  - Strips query parameters, fragments, trailing slashes
  - Case-insensitive matching
  - Supports locale subdomains (uk.linkedin.com, m.linkedin.com)
- `find_linkedin_duplicates()` - Find contacts sharing LinkedIn profiles
- New deduplication level for social URL matching

#### Performance Indexes
- `idx_contacts_duplicate_group` - Critical for dedup queries
- `idx_contacts_linkedin` - LinkedIn URL lookups
- `idx_contacts_website` - Website URL lookups

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

#### Pydantic Best Practices Audit
- 50 new test cases for model validation coverage
  - Strict mode validation (type coercion rejection)
  - Required field validation
  - Nested object validation
  - Alias handling (`populate_by_name`)
  - Pagination edge cases
  - Union type edge cases (`str | datetime | None`)
- Field validators for input validation
  - `birthday_year`: Validates range 1900 to current year
  - `due_at_date`: Validates YYYY-MM-DD format
- Type hardening with `Literal` and `Field` constraints
  - `meeting_type: Literal["note"]` for NoteCreate
  - `total: int = Field(ge=0)` on pagination models
  - `limit: int = Field(default=100, ge=1, le=1000)` on pagination
  - `offset: int = Field(default=0, ge=0)` on pagination
- `__all__` export list for all public models and extractors
- Field descriptions for timestamp and date fields

### Changed
- `find_phone_duplicates()` now normalizes phone formats before matching
- `analyze_duplicates.py` includes Level 1.5b fingerprint analysis in reports
- Makefile refactored following best practices
- Improved variable naming in deduplication and sync modules for readability
- Performance test thresholds loosened to reduce timing variance across environments
- Request models now forbid unknown fields and accept datetime inputs for timestamps
- Nested response fields use typed models for emails, phones, and contacts

### Fixed
- Line length compliance with 88 character limit
- Linting issues in test files
- Reminder and note update payloads no longer include path IDs
- Note event timestamps in responses are treated as ISO strings

### Dependencies
- Added `typer>=0.12.0` for unified CLI
- Added `sqlalchemy>=2.0.0` for ORM models
- Added `alembic>=1.14.0` for database migrations
- Added `phonenumbers>=8.13.0` for international phone parsing
- Added `unidecode>=1.3.0` for unicode→ASCII normalization

### Documentation
- Comprehensive docstrings added to all source modules
- Added `AGENTS.md` and `CONTINUITY.md` for repository guidance and continuity
- Updated README and API/performance docs for model validation and perf thresholds
- Clarified performance/indexing rationale in code comments

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
