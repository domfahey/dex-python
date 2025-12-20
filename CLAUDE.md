# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
make install          # Set up venv and install deps
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

## Data Workflow

```bash
uv run python main.py
uv run python sync_with_integrity.py
uv run python analyze_duplicates.py
uv run python flag_duplicates.py
uv run python review_duplicates.py
uv run python resolve_duplicates.py
```

## Architecture

Dex CRM API client using httpx and pydantic.

- `src/dex_import/config.py` - Settings loaded from `.env` (requires `DEX_API_KEY`)
- `src/dex_import/client.py` - `DexClient` class with context manager support
- `src/dex_import/deduplication.py` - Duplicate detection and merging utilities
- `tests/unit/test_clients.py` - Unit tests with pytest-httpx mocking
- `tests/integration/test_live_api.py` - Integration tests against live API

## API

Base URL: `https://api.getdex.com/api/rest`

Required header: `x-hasura-dex-api-key`

See [docs/api.md](docs/api.md) for full API reference.

## Dependencies

Uses **uv** for package management (not pip/poetry).
