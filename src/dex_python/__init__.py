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
from .deduplication import find_fingerprint_name_duplicates
from .exceptions import (
    AuthenticationError,
    ContactNotFoundError,
    DexAPIError,
    NoteNotFoundError,
    RateLimitError,
    ReminderNotFoundError,
    ValidationError,
)
from .fingerprint import (
    ensemble_similarity,
    fingerprint,
    ngram_fingerprint,
    normalize_phone,
    normalized_levenshtein,
)
from .models import (
    Contact,
    ContactCreate,
    ContactEmail,
    ContactEmailResponse,
    ContactPhone,
    ContactPhoneResponse,
    ContactUpdate,
    Note,
    NoteContact,
    NoteCreate,
    NoteUpdate,
    PaginatedContacts,
    PaginatedNotes,
    PaginatedReminders,
    Reminder,
    ReminderContact,
    ReminderCreate,
    ReminderUpdate,
)

__all__ = [
    # Client
    "AsyncDexClient",
    "DexClient",
    "Settings",
    # Deduplication
    "find_fingerprint_name_duplicates",
    # Exceptions
    "AuthenticationError",
    "ContactNotFoundError",
    "DexAPIError",
    "NoteNotFoundError",
    "RateLimitError",
    "ReminderNotFoundError",
    "ValidationError",
    # Fingerprinting
    "ensemble_similarity",
    "fingerprint",
    "ngram_fingerprint",
    "normalize_phone",
    "normalized_levenshtein",
    # Models
    "Contact",
    "ContactCreate",
    "ContactEmail",
    "ContactEmailResponse",
    "ContactPhone",
    "ContactPhoneResponse",
    "ContactUpdate",
    "Note",
    "NoteContact",
    "NoteCreate",
    "NoteUpdate",
    "PaginatedContacts",
    "PaginatedNotes",
    "PaginatedReminders",
    "Reminder",
    "ReminderContact",
    "ReminderCreate",
    "ReminderUpdate",
]
