# API Reference

Python client for the [Dex CRM API](https://getdex.com/docs/api-reference/authentication).

See official docs: [Contacts](https://getdex.com/docs/api-reference/contacts) |
[Reminders](https://getdex.com/docs/api-reference/reminders) |
[Notes](https://getdex.com/docs/api-reference/notes)

Official site: https://getdex.com/

## DexClient

Python client for the Dex CRM API.

### Initialization

```python
from dex_python import DexClient, Settings

# Auto-load from .env
client = DexClient()

# Or with custom settings
settings = Settings(dex_api_key="your-key")
client = DexClient(settings)

# Enable retries for transient errors
client = DexClient(settings, max_retries=3, retry_delay=0.5)
```

### Context Manager

```python
with DexClient() as client:
    contacts = client.get_contacts()
# Client automatically closed
```

### Retries and Rate Limits

Retries are off by default (`max_retries=0`, `retry_delay=1.0`). When
`max_retries` is greater than 0, both `DexClient` and `AsyncDexClient`
retry status codes 429, 500, 502, 503, and 504 using exponential backoff
based on `retry_delay` (seconds). Retries apply to all requests, so keep retry
counts low for non-idempotent writes.

### Error Handling

Common exceptions you may want to handle:

- `AuthenticationError` (401)
- `ValidationError` (400)
- `RateLimitError` (429, includes `retry_after`)
- `ContactNotFoundError`, `ReminderNotFoundError`, `NoteNotFoundError` (404)
- `DexAPIError` (other non-2xx/3xx responses)

```python
import time

from dex_python import DexClient, DexAPIError, RateLimitError

try:
    with DexClient(max_retries=2, retry_delay=0.5) as client:
        client.get_contacts()
except RateLimitError as exc:
    time.sleep(exc.retry_after or 1)
except DexAPIError as exc:
    print(exc)
```

### Pagination Helpers

Use paginated methods to access total counts and `has_more`.

```python
page = client.get_contacts_paginated(limit=100, offset=0)
all_contacts = list(page.contacts)

while page.has_more:
    page = client.get_contacts_paginated(
        limit=page.limit,
        offset=page.offset + len(page.contacts),
    )
    all_contacts.extend(page.contacts)
```

Async versions (`AsyncDexClient`) expose the same `*_paginated` methods.

## AsyncDexClient

Async client with the same API as `DexClient`.

```python
from dex_python import AsyncDexClient, Settings

settings = Settings(dex_api_key="your-key")

async with AsyncDexClient(settings, max_retries=2, retry_delay=0.5) as client:
    contacts = await client.get_contacts(limit=100)
```

---

## Contacts API

### `get_contacts(limit=100, offset=0)`

Fetch paginated list of contacts.

```python
contacts = client.get_contacts(limit=10, offset=0)
```

### `get_contacts_paginated(limit=100, offset=0)`

Fetch contacts with total count metadata.

```python
page = client.get_contacts_paginated(limit=100, offset=0)
print(page.total, page.has_more)
```

### `get_contact(contact_id)`

Fetch a single contact by ID.

```python
contact = client.get_contact("2a05d868-5a20-4c9c-8273-9a24bf589991")
```

### `get_contact_by_email(email)`

Fetch a contact by email address.

```python
contact = client.get_contact_by_email("john@example.com")
```

### `create_contact(contact)`

Create a new contact.

```python
from dex_python import ContactCreate

contact = ContactCreate(first_name="John", last_name="Doe")
result = client.create_contact(contact)

# With email
contact = ContactCreate.with_email(
    email="john@example.com",
    first_name="John",
    last_name="Doe"
)
```

### `update_contact(update)`

Update an existing contact.

```python
from dex_python import ContactUpdate

update = ContactUpdate(
    contact_id="123-456",
    changes={"first_name": "Johnny"}
)
result = client.update_contact(update)
```

### `delete_contact(contact_id)`

Delete a contact by ID.

```python
result = client.delete_contact("123-456")
```

---

## Reminders API

### `get_reminders(limit=100, offset=0)`

Fetch paginated list of reminders.

```python
reminders = client.get_reminders(limit=10)
```

### `get_reminders_paginated(limit=100, offset=0)`

Fetch reminders with total count metadata.

```python
page = client.get_reminders_paginated(limit=100, offset=0)
print(page.total, page.has_more)
```

### `create_reminder(reminder)`

Create a new reminder.

```python
from dex_python import ReminderCreate

reminder = ReminderCreate(text="Follow up with client")
result = client.create_reminder(reminder)

# With contacts
reminder = ReminderCreate.with_contacts(
    text="Follow up",
    contact_ids=["c1", "c2"],
    due_at_date="2025-01-20"
)
```

### `update_reminder(update)`

Update an existing reminder.

```python
from dex_python import ReminderUpdate

update = ReminderUpdate(
    reminder_id="123-456",
    changes={"text": "Updated text", "is_complete": True}
)
result = client.update_reminder(update)

# Mark complete using factory
update = ReminderUpdate.mark_complete("123-456")
result = client.update_reminder(update)
```

### `delete_reminder(reminder_id)`

Delete a reminder by ID.

```python
result = client.delete_reminder("123-456")
```

---

## Notes API

### `get_notes(limit=100, offset=0)`

Fetch paginated list of notes (timeline items).

```python
notes = client.get_notes(limit=10)
```

### `get_notes_paginated(limit=100, offset=0)`

Fetch notes with total count metadata.

```python
page = client.get_notes_paginated(limit=100, offset=0)
print(page.total, page.has_more)
```

### `get_notes_by_contact(contact_id)`

Fetch notes for a specific contact.

```python
notes = client.get_notes_by_contact("contact-123")
```

### `create_note(note)`

Create a new note.

```python
from dex_python import NoteCreate

note = NoteCreate(note="Meeting notes here")
result = client.create_note(note)

# With contacts
note = NoteCreate.with_contacts(
    note="Meeting notes",
    contact_ids=["c1", "c2"],
    event_time="2025-01-15T10:00:00.000Z"
)
```

`event_time` also accepts a `datetime` instance and will be serialized to ISO.

### `update_note(update)`

Update an existing note.

```python
from dex_python import NoteUpdate

update = NoteUpdate(
    note_id="note-123",
    changes={"note": "Updated note text"}
)
result = client.update_note(update)
```

### `delete_note(note_id)`

Delete a note by ID.

```python
result = client.delete_note("note-123")
```

---

## Models

Request models are strict: unknown fields are rejected. Timestamp inputs listed
as `datetime` are serialized to ISO strings on output.

### ContactCreate

| Field | Type | Description |
|-------|------|-------------|
| `first_name` | `str \| None` | First name |
| `last_name` | `str \| None` | Last name |
| `job_title` | `str \| None` | Job title |
| `description` | `str \| None` | Description |
| `education` | `str \| None` | Education |
| `website` | `str \| None` | Website |
| `image_url` | `str \| None` | Profile image URL |
| `linkedin` | `str \| None` | LinkedIn handle |
| `twitter` | `str \| None` | Twitter/X handle |
| `instagram` | `str \| None` | Instagram handle |
| `telegram` | `str \| None` | Telegram handle |
| `birthday_year` | `int \| None` | Birth year (validated: 1900 to current year) |
| `last_seen_at` | `str \| datetime \| None` | Last seen timestamp (ISO 8601) |
| `next_reminder_at` | `str \| datetime \| None` | Next reminder timestamp (ISO 8601) |
| `contact_emails` | `dict` | Nested email payload (`{"data": {"email": ...}}`) |
| `contact_phone_numbers` | `dict` | Nested phone payload (`{"data": {"phone_number": ..., "label": ...}}`) |

### ContactUpdate

| Field | Type | Description |
|-------|------|-------------|
| `contact_id` | `str` | Contact ID (required; serialized as `contactId`) |
| `changes` | `dict[str, Any]` | Fields to update |
| `update_contact_emails` | `bool` | Whether to update email associations |
| `update_contact_phone_numbers` | `bool` | Whether to update phone associations |
| `contact_emails` | `list` | Contact email associations |
| `contact_phone_numbers` | `list` | Contact phone associations |

### ReminderUpdate

| Field | Type | Description |
|-------|------|-------------|
| `reminder_id` | `str` | Reminder ID (required, excluded from payload) |
| `changes` | `dict[str, Any]` | Fields to update |
| `update_contacts` | `bool` | Whether to update contact associations |
| `reminders_contacts` | `list` | Contact associations |

### NoteUpdate

| Field | Type | Description |
|-------|------|-------------|
| `note_id` | `str` | Note ID (required, excluded from payload) |
| `changes` | `dict[str, Any]` | Fields to update |
| `update_contacts` | `bool` | Whether to update contact associations |
| `timeline_items_contacts` | `list` | Contact associations |

### Response model notes

- `Contact.emails`/`Contact.phones` use typed response objects.
- `Reminder.contact_ids` and `Note.contacts` use typed contact references.
- Response timestamps are returned as ISO strings.

### ReminderCreate

| Field | Type | Description |
|-------|------|-------------|
| `title` | `str \| None` | Reminder title |
| `text` | `str` | Reminder text (required) |
| `is_complete` | `bool` | Completion status (default: `False`) |
| `due_at_date` | `str \| None` | Due date (validated: YYYY-MM-DD format) |
| `reminders_contacts` | `dict` | Contact associations |

### NoteCreate

| Field | Type | Description |
|-------|------|-------------|
| `note` | `str` | Note text (required) |
| `event_time` | `str \| datetime \| None` | Event timestamp (ISO 8601) |
| `meeting_type` | `Literal["note"]` | Meeting type (only "note" allowed) |
| `timeline_items_contacts` | `dict` | Contact associations |

### Pagination Models

Pagination models include field constraints:
- `total`: `int` (must be >= 0)
- `limit`: `int` (default: 100, range: 1-1000)
- `offset`: `int` (default: 0, must be >= 0)

| Model | Description |
|-------|-------------|
| `PaginatedContacts` | Paginated contacts with `has_more` property |
| `PaginatedReminders` | Paginated reminders with `has_more` property |
| `PaginatedNotes` | Paginated notes with `has_more` property |

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
| GET | `/timeline_items/contacts/{id}` | Notes by contact |
| POST | `/timeline_items` | Create note |
| PUT | `/timeline_items/{id}` | Update note |
| DELETE | `/timeline_items/{id}` | Delete note |
