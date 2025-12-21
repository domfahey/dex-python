"""Dex Python SDK - Python client for the Dex CRM API.

This package provides sync and async clients for interacting with the Dex CRM API,
including full CRUD operations for contacts, reminders, and notes.

Quick Start:
    >>> from dex_python import DexClient
    >>> with DexClient() as client:
    ...     contacts = client.get_contacts(limit=10)

For async usage:
    >>> from dex_python import AsyncDexClient
    >>> async with AsyncDexClient() as client:
    ...     contacts = await client.get_contacts(limit=10)

Environment Variables:
    DEX_API_KEY: Your Dex API key (required)
    DEX_BASE_URL: API base URL (optional, defaults to https://api.getdex.com/api/rest)

See Also:
    - https://github.com/domfahey/dex-python
    - https://getdex.com/docs/api-reference
"""

from .async_client import AsyncDexClient
from .client import DexClient
from .config import Settings
from .exceptions import (
    AuthenticationError,
    ContactNotFoundError,
    DexAPIError,
    NoteNotFoundError,
    RateLimitError,
    ReminderNotFoundError,
    ValidationError,
)
from .models import (
    Contact,
    ContactCreate,
    ContactEmail,
    ContactPhone,
    ContactUpdate,
    Note,
    NoteCreate,
    NoteUpdate,
    PaginatedContacts,
    PaginatedNotes,
    PaginatedReminders,
    Reminder,
    ReminderCreate,
    ReminderUpdate,
)

__all__ = [
    # Client
    "AsyncDexClient",
    "DexClient",
    "Settings",
    # Exceptions
    "AuthenticationError",
    "ContactNotFoundError",
    "DexAPIError",
    "NoteNotFoundError",
    "RateLimitError",
    "ReminderNotFoundError",
    "ValidationError",
    # Models
    "Contact",
    "ContactCreate",
    "ContactEmail",
    "ContactPhone",
    "ContactUpdate",
    "Note",
    "NoteCreate",
    "NoteUpdate",
    "PaginatedContacts",
    "PaginatedNotes",
    "PaginatedReminders",
    "Reminder",
    "ReminderCreate",
    "ReminderUpdate",
]
