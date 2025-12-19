# API Reference

## DexClient

Python client for the Dex CRM API.

### Initialization

```python
from src.dex_import import DexClient, Settings

# Auto-load from .env
client = DexClient()

# Or with custom settings
settings = Settings(dex_api_key="your-key")
client = DexClient(settings)
```

### Context Manager

```python
with DexClient() as client:
    contacts = client.get_contacts()
# Client automatically closed
```

### Methods

#### `get_contacts(limit=100, offset=0)`

Fetch paginated list of contacts.

```python
contacts = client.get_contacts(limit=10, offset=0)
```

#### `get_contact(contact_id)`

Fetch a single contact by ID.

```python
contact = client.get_contact("2a05d868-5a20-4c9c-8273-9a24bf589991")
```

#### `create_contact(contact)`

Create a new contact.

```python
from src.dex_import.client import Contact

contact = Contact(first_name="John", last_name="Doe")
result = client.create_contact(contact)
```

---

## Contact Model

| Field | Type | Description |
|-------|------|-------------|
| `id` | `str \| None` | Contact UUID (set by API) |
| `first_name` | `str \| None` | First name |
| `last_name` | `str \| None` | Last name |
| `email` | `str \| None` | Email address |
| `phone` | `str \| None` | Phone number |
| `company` | `str \| None` | Company name |
| `notes` | `str \| None` | Notes about contact |

---

## Settings

| Variable | Required | Default |
|----------|----------|---------|
| `DEX_API_KEY` | Yes | - |
| `DEX_BASE_URL` | No | `https://api.getdex.com/api/rest` |

---

## Dex API Reference

For complete Dex API documentation, see [dex_api_docs/](dex_api_docs/README.md).

### Endpoints Summary

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/contacts` | List contacts |
| GET | `/contacts/{id}` | Get contact by ID |
| GET | `/search/contacts?email=` | Get contact by email |
| POST | `/contacts` | Create contact |
| PUT | `/contacts/{id}` | Update contact |
| DELETE | `/contacts/{id}` | Delete contact |
| GET | `/reminders` | List reminders |
| POST | `/reminders` | Create reminder |
| PUT | `/reminders/{id}` | Update reminder |
| DELETE | `/reminders/{id}` | Delete reminder |
| GET | `/timeline_items` | List notes |
| POST | `/timeline_items` | Create note |
| PUT | `/timeline_items/{id}` | Update note |
| DELETE | `/timeline_items/{id}` | Delete note |
