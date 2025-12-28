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

## Continuity Ledger (compaction-safe)
Maintain a single Continuity Ledger for this workspace in `CONTINUITY.md`. The
ledger is the canonical session briefing designed to survive context
compaction; do not rely on earlier chat text unless it's reflected in the
ledger.

### How it works
- At the start of every assistant turn: read `CONTINUITY.md`, update it
  to reflect the latest goal/constraints/decisions/state, then proceed with the
  work.
- Update `CONTINUITY.md` again whenever any of these change: goal,
  constraints/assumptions, key decisions, progress state (Done/Now/Next), or
  important tool outcomes.
- Keep it short and stable: facts only, no transcripts. Prefer bullets. Mark
  uncertainty as `UNCONFIRMED` (never guess).
- If you notice missing recall or a compaction/summary event: refresh/rebuild
  the ledger from visible context, mark gaps `UNCONFIRMED`, ask up to 1-3
  targeted questions, then continue.

### `functions.update_plan` vs the Ledger
- `functions.update_plan` is for short-term execution scaffolding while you
  work (a small 3-7 step plan with pending/in_progress/completed).
- `CONTINUITY.md` is for long-running continuity across compaction (the
  "what/why/current state"), not a step-by-step task list.
- Keep them consistent: when the plan or state changes, update the ledger at
  the intent/progress level (not every micro-step).

### In replies
- Begin with a brief "Ledger Snapshot" (Goal + Now/Next + Open Questions).
  Print the full ledger only when it materially changes or when the user asks.

### `CONTINUITY.md` format (keep headings)
- Goal (incl. success criteria):
- Constraints/Assumptions:
- Key decisions:
- State:
- Done:
- Now:
- Next:
- Open questions (UNCONFIRMED if needed):
- Working set (files/ids/commands):
