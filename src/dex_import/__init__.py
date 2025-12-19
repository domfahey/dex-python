"""Dex API integration package."""

from .client import DexClient
from .config import Settings
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
    "DexClient",
    "Settings",
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
