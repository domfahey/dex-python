# Repository Guidelines

## Project Structure & Module Organization
Layout: `src/dex_python/` (SDK), `scripts/` (sync/dedup), `tests/unit/` +
`tests/integration/`, `docs/` + `docs/dex_api_docs/`, `output/` (set
`DEX_DATA_DIR`).

## Build, Test, and Development Commands
Use `make`: `make install`, `make doctor`, `make format`/`make lint`/
`make type`, `make test`/`make test-unit`/`make test-integration`, `make check`,
and data `make sync`/`make analyze`/`make flag-duplicates`/
`make resolve-duplicates` (destructive).

## Coding Style & Naming Conventions
Python 3.11+, 4-space indentation, line length 88. Ruff formats/lints; mypy.
Use snake_case; tests are `tests/**/test_*.py` with `test_*` functions.

## Testing Guidelines
Use `pytest` with `pytest-asyncio`. Integration tests are marked `integration`
and skipped; run `make test-integration` with `.env` +
`DEX_API_KEY`.

## Commit & Pull Request Guidelines
Use prefixes `feat:`/`fix:`/`docs:`/`refactor:`/`build:`. PRs target `main`,
include description + linked issues, and should pass `make check`.

## Security & Configuration Tips
Store secrets in `.env` (see `.env.example`) and never commit API keys or
contact data. `DEX_BASE_URL` targets test instances; `DEX_DATA_DIR` controls
SQLite outputs.
