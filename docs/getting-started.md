# Getting Started

This guide walks you through installing Dex Python, configuring API access,
and making a first request.

## Prerequisites

- Python 3.11+
- `uv` installed (recommended)
- A Dex API key from https://getdex.com/settings/api
- Dex website: https://getdex.com/

## Install

From the repository root:

```bash
uv venv
uv sync --all-extras --dev
```

## Configure

Create a `.env` file in the repository root:

```bash
DEX_API_KEY=your-api-key-here
# Optional: override base URL (useful for testing)
DEX_BASE_URL=https://api.getdex.com/api/rest
# Optional: local output directory for DB and reports
DEX_DATA_DIR=output
```

Keep `.env` out of version control so API keys are not committed.

## Verify your setup

Run a read-only request to confirm credentials:

```bash
uv run python - <<'PY'
from dex_python import DexClient

with DexClient() as client:
    contacts = client.get_contacts(limit=1)
    print(f"fetched {len(contacts)} contact(s)")
PY
```

## Quick start: API client

```python
from dex_python import DexClient

with DexClient(max_retries=2, retry_delay=0.5) as client:
    contacts = client.get_contacts(limit=5)
    for contact in contacts:
        print(contact.id, contact.first_name, contact.last_name)
```

## Quick start: SQLite sync (optional)

Scripts write contact data to `output/dex_contacts.db` by default (override with
`DEX_DATA_DIR`):

```bash
uv run python scripts/main.py                # Full refresh (recreates tables)
uv run python scripts/sync_with_integrity.py # Incremental sync with hashes
```

Note: `scripts/sync_with_integrity.py` writes `dex_contacts.db` in the repo root
by default. If you want other scripts to target that database, set
`DEX_DATA_DIR=.` when running them.

## Best practices

- Keep `DEX_API_KEY` in `.env` or environment variables and never commit it.
- Use low retry counts for non-idempotent writes; enable retries for reads.
- Back up the database before running destructive dedup steps.

## Next steps

- Read `docs/api.md` for client API details.
- Browse `docs/dex_api_docs/README.md` for the Dex REST reference.
- Review `docs/planning/deduplication.md` before running the merge workflow.
