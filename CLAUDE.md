# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
make install          # Set up venv and install deps
make doctor           # Verify environment and dependencies
make test             # Run all tests
make test-unit        # Run unit tests only
make test-integration # Run integration tests (live API)
make lint             # Check code with ruff
make format           # Auto-fix lint issues and format
make type             # Run mypy strict type checking

# Run single test
uv run pytest tests/unit/test_clients.py::test_get_contacts -v
```

Integration tests are marked `integration` and skipped by default.

## CLI Commands

```bash
# Sync
dex sync incremental    # Recommended: preserves dedup metadata
dex sync full           # Destructive: recreates tables

# Deduplication
dex duplicate analyze   # Generate duplicate report
dex duplicate flag      # Flag duplicate candidates
dex duplicate review    # Interactive review
dex duplicate resolve   # Merge confirmed duplicates

# Enrichment
dex enrichment backfill # Parse job titles for company/role
dex enrichment push     # Push enrichment data to API
```

Common options: `--db-path`, `--data-dir`, `--verbose`, `--dry-run`, `--force`

Artifacts are written to `output/` by default (override with `DEX_DATA_DIR`).

## Architecture

Dex CRM API client using httpx and pydantic.

- `src/dex_python/client.py` - `DexClient` class with context manager support
- `src/dex_python/config.py` - Settings loaded from `.env` (requires `DEX_API_KEY`)
- `src/dex_python/models.py` - Pydantic models with validators and type constraints
- `src/dex_python/deduplication.py` - Duplicate detection and merging utilities
- `src/dex_python/fingerprint.py` - E.164 phone and LinkedIn normalization
- `src/dex_python/cli/` - Unified CLI using Typer
- `src/dex_python/db/` - SQLAlchemy ORM models and Alembic migrations
- `tests/unit/` - Unit tests with pytest-httpx mocking (340+ tests)
- `tests/integration/` - Integration tests against live API

## API

Base URL: `https://api.getdex.com/api/rest`

Required header: `x-hasura-dex-api-key`

See [docs/api.md](docs/api.md) for full API reference.

## Dependencies

Uses **uv** for package management (not pip/poetry).
