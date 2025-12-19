"""Dex API integration package."""

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
