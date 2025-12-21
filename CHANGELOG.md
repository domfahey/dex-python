# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.0] - 2025-12-21

### Added
- Birthday-based duplicate detection (Level 1.5)
- Name parsing module with probablepeople integration (`dex_python.name_parsing`)
- Job title enrichment with company/role extraction (`dex_python.enrichment`)
- Sync-back functionality to push enrichments to Dex API (`dex_python.sync_back`)
- GitHub issue and PR templates
- Deduplication engine with level 1/2/3 matching, clustering, and merge utilities
- CLI scripts for duplicate workflow: `analyze`, `flag-duplicates`, `resolve-duplicates`
- Async sync tool with integrity hashing and incremental updates
- `make doctor` command to verify environment
- `make sync` command for incremental sync
- Faker for test data generation

### Changed
- **BREAKING**: Package renamed from `dex_import` to `dex_python`
- **BREAKING**: Import path changed from `from src.dex_import` to `from dex_python`
- Scripts moved to `scripts/` directory
- Documentation reorganized into `docs/` with `docs/planning/` for internal docs
- Project structure follows open source best practices

### Fixed
- `AsyncDexClient` `max_retries` default now matches sync client (0)
- Write operations return normalized entity data instead of raw API wrappers
- Paginated methods properly extract total counts from nested API responses
- Database operations preserve deduplication metadata on updates
- Filter empty/whitespace names in fuzzy matching to prevent false positives

### Security
- Added `.gitignore` patterns for sensitive data exports
- Security audit completed before public release

## [0.1.0] - 2025-12-19

Initial release implementing the [Dex CRM API](https://getdex.com/docs/api-reference/authentication).

### Added
- `DexClient` synchronous client with full CRUD for contacts, reminders, and notes
- `AsyncDexClient` for async API operations
- Context manager support for both clients
- `Settings` configuration with pydantic-settings
- Environment variable support (`DEX_API_KEY`, `DEX_BASE_URL`)
- Pydantic models: `Contact`, `ContactCreate`, `ContactUpdate`, `Reminder`, `ReminderCreate`, `ReminderUpdate`, `Note`, `NoteCreate`, `NoteUpdate`
- Paginated response models with `has_more` property
- Custom exceptions: `DexAPIError`, `AuthenticationError`, `RateLimitError`, `ValidationError`, `ContactNotFoundError`, `ReminderNotFoundError`, `NoteNotFoundError`
- Retry logic with exponential backoff for transient errors (429, 500, 502, 503, 504)
- Unit tests with pytest-httpx mocking
- Integration tests against live API
- MIT License
- Contributing guidelines
- Security policy

[unreleased]: https://github.com/domfahey/dex-python/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/domfahey/dex-python/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/domfahey/dex-python/releases/tag/v0.1.0
