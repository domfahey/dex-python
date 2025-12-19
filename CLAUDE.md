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
uv run pytest tests/test_client.py::TestDexClient::test_get_contacts -v
```

## Architecture

Dex CRM API client using httpx and pydantic.

- `src/dex_import/config.py` - Settings loaded from `.env` (requires `DEX_API_KEY`)
- `src/dex_import/client.py` - `DexClient` class with context manager support
- `tests/test_client.py` - Unit tests with pytest-httpx mocking
- `tests/test_integration.py` - Integration tests against live API

## API

Base URL: `https://api.getdex.com/api/rest`

Required header: `x-hasura-dex-api-key`

See [docs/api.md](docs/api.md) for full API reference.

## Dependencies

Uses **uv** for package management (not pip/poetry).
