# Dex Python

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)
[![Type checked: mypy](https://img.shields.io/badge/type%20checked-mypy-blue.svg)](https://mypy-lang.org/)

Python SDK for the [Dex](https://getdex.com) CRM API with sync/async clients, automatic retries, and local SQLite caching.

## Features

- Sync and async clients for the Dex REST API
- Automatic retry with exponential backoff for rate limits
- Strict request/response validation with Pydantic models
- Unified `dex` CLI for sync, deduplication, and enrichment workflows
- Local SQLite database with Alembic migrations
- Contact deduplication with fuzzy matching and LinkedIn/phone normalization
- E.164 international phone number parsing
- Job title parsing for company/role extraction
- Comprehensive test suite with 340+ tests

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
# Optional: local output directory for DB and reports
DEX_DATA_DIR=output
```

Get your API key from [Dex API Settings](https://getdex.com/settings/api).

## Usage

```python
from dex_python import ContactCreate, DexClient

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

from dex_python import DexClient, RateLimitError

try:
    with DexClient(max_retries=2, retry_delay=0.5) as client:
        contacts = client.get_contacts(limit=10)
except RateLimitError as exc:
    time.sleep(exc.retry_after or 1)
```

## CLI

The unified `dex` CLI provides commands for sync, deduplication, and enrichment:

```bash
dex sync incremental    # Incremental sync preserving dedup metadata
dex sync full           # Full sync (destructive)
dex duplicate analyze   # Generate duplicate analysis report
dex duplicate flag      # Flag duplicate candidates
dex duplicate review    # Interactive duplicate review
dex duplicate resolve   # Merge confirmed duplicates
dex enrichment backfill # Parse job titles for company/role
dex enrichment push     # Push enrichment data to API
```

Common options: `--db-path`, `--data-dir`, `--verbose`, `--dry-run`, `--force`

## SQLite sync

Scripts write contact data to a local SQLite database with Alembic migrations:

```bash
dex sync incremental                         # Recommended: CLI command
make sync                                    # Or via Makefile
uv run python scripts/sync_with_integrity.py # Direct script execution
```

Database location defaults to `output/dex_contacts.db` (override with `DEX_DATA_DIR`).

## Deduplication workflow

1. Sync contacts: `dex sync incremental`
2. Generate report: `dex duplicate analyze`
3. Flag candidates: `dex duplicate flag`
4. Review interactively: `dex duplicate review`
5. Merge confirmed: `dex duplicate resolve` (destructive)

Back up the database before merging. The deduplication engine supports:
- Exact matching (email, phone, LinkedIn URL)
- Composite matching (name + job title)
- Fuzzy matching (Jaro-Winkler with phonetic blocking)
- E.164 phone normalization for international numbers

## Development

```bash
make install          # Set up environment
make doctor           # Verify environment and dependencies
make test             # Run unit tests (integration excluded by default)
make test-unit        # Run unit tests only
make test-integration # Run integration tests (requires API key)
make lint             # Check code style
make format           # Auto-fix formatting
make type             # Run type checking
```

Integration tests are marked with `integration` and require `DEX_API_KEY`.

## Documentation

- [Getting Started](docs/getting-started.md) - Install, configure, and make a first request
- [API Reference](docs/api.md) - Python client usage
- [Architecture](docs/architecture.md) - System design and component overview
- [Name Parsing](docs/name-parsing.md) - Parsing behavior and stored fields
- [Dex API Docs](docs/dex_api_docs/README.md) - Local REST API reference
- [Deduplication Plan](docs/planning/deduplication.md) - Deduplication workflow and thresholds
- [Roadmap](docs/planning/roadmap.md) - Planned work and priorities

### Official Dex API

- [Authentication](https://getdex.com/docs/api-reference/authentication) - API key setup
- [Contacts](https://getdex.com/docs/api-reference/contacts) - Contact endpoints
- [Reminders](https://getdex.com/docs/api-reference/reminders) - Reminder endpoints
- [Notes](https://getdex.com/docs/api-reference/notes) - Note endpoints

## Testing

```bash
make test             # Run all tests (excludes integration by default)
make test-unit        # Run unit tests only
make test-integration # Run integration tests (requires DEX_API_KEY)
make check            # Run format, lint, type check, and tests
```

### Test Structure

```
tests/
├── unit/                    # Fast, isolated unit tests
│   ├── test_clients.py      # Client API tests with mocked HTTP
│   ├── test_models.py       # Pydantic model tests
│   └── deduplication/       # Deduplication algorithm tests
├── integration/             # Live API tests (requires credentials)
└── conftest.py              # Shared fixtures
```

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Run checks (`make check`)
4. Commit your changes
5. Push to your branch
6. Open a Pull Request

### Code Standards

- **Style:** [Ruff](https://github.com/astral-sh/ruff) for linting and formatting
- **Types:** [mypy](https://mypy-lang.org/) with strict mode
- **Tests:** [pytest](https://pytest.org/) with 340+ tests

## Security

- See [SECURITY.md](SECURITY.md) for vulnerability reporting
- Never commit API keys or contact data
- Use `.env` files for local secrets (gitignored)

## Code of Conduct

This project follows the [Contributor Covenant Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [Dex](https://getdex.com) for the CRM platform and API
- [httpx](https://www.python-httpx.org/) for the HTTP client
- [Pydantic](https://docs.pydantic.dev/) for data validation
- [Faker](https://faker.readthedocs.io/) for test data generation
