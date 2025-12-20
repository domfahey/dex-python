# Dex Import

Python client for the [Dex](https://getdex.com) CRM API.

## Installation

```bash
uv venv && uv sync --all-extras --dev
```

## Configuration

Create a `.env` file with your API key:

```bash
DEX_API_KEY=your-api-key-here
# Optional: override base URL (useful for testing)
DEX_BASE_URL=https://api.getdex.com/api/rest
```

Get your API key from [Dex API Settings](https://getdex.com/settings/api).

## Usage

```python
from src.dex_import import ContactCreate, DexClient

with DexClient(max_retries=3, retry_delay=0.5) as client:
    # List contacts
    contacts = client.get_contacts(limit=10)

    # Get single contact
    contact = client.get_contact("contact-id")

    # Create contact
    new_contact = ContactCreate(first_name="John", last_name="Doe")
    result = client.create_contact(new_contact)
```

## Retries and rate limits

- Retries are off by default (`max_retries=0`, `retry_delay=1.0`); set `max_retries` to retry transient errors (429, 500, 502, 503, 504).
- Backoff uses `retry_delay` as the base (seconds) with exponential growth per attempt.
- Retries apply to all requests; keep `max_retries` low for non-idempotent writes.
- `RateLimitError.retry_after` exposes the `Retry-After` header when provided.
- Both `DexClient` and `AsyncDexClient` support retry logic.

```python
import time

from src.dex_import import DexClient, RateLimitError

try:
    with DexClient(max_retries=2, retry_delay=0.5) as client:
        contacts = client.get_contacts(limit=10)
except RateLimitError as exc:
    time.sleep(exc.retry_after or 1)
```

## SQLite sync

Two scripts write contact data to `dex_contacts.db`:

- `main.py` performs a full refresh and recreates tables on each run.
- `sync_with_integrity.py` performs incremental syncs with hashes and preserves
  deduplication metadata.

```bash
uv run python main.py
uv run python sync_with_integrity.py
```

## Deduplication workflow

1. Sync contacts to SQLite (`main.py` or `sync_with_integrity.py`).
2. Generate a report: `uv run python analyze_duplicates.py`
3. Flag candidate groups: `uv run python flag_duplicates.py`
4. Review interactively: `uv run python review_duplicates.py`
5. Merge confirmed groups: `uv run python resolve_duplicates.py` (destructive)

Back up `dex_contacts.db` before merging.

## Development

```bash
make install          # Set up environment
make test             # Run unit tests (integration excluded by default)
make test-unit        # Run unit tests only
make test-integration # Run integration tests (requires API key)
make lint             # Check code style
make format           # Auto-fix formatting
make type             # Run type checking
```

Integration tests are marked with `integration` and require `DEX_API_KEY`.

## Documentation

- [API Reference](docs/api.md) - Python client usage
- [Dex API Docs](docs/dex_api_docs/README.md) - Complete Dex REST API reference
- [Deduplication Plan](DEDUPLICATION_PLAN.md) - Local database deduplication flow
