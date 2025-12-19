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
    Reminder,
    ReminderCreate,
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
    "Reminder",
    "ReminderCreate",
]
