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
```

Get your API key from [Dex API Settings](https://getdex.com/settings/api).

## Usage

```python
from src.dex_import import DexClient
from src.dex_import.client import Contact

with DexClient() as client:
    # List contacts
    contacts = client.get_contacts(limit=10)

    # Get single contact
    contact = client.get_contact("contact-id")

    # Create contact
    new_contact = Contact(first_name="John", last_name="Doe")
    result = client.create_contact(new_contact)
```

## Development

```bash
make install          # Set up environment
make test             # Run all tests
make test-unit        # Run unit tests only
make test-integration # Run integration tests (requires API key)
make lint             # Check code style
make format           # Auto-fix formatting
make type             # Run type checking
```

## Documentation

- [API Reference](docs/api.md) - Python client usage
- [Dex API Docs](docs/dex_api_docs/README.md) - Complete Dex REST API reference
