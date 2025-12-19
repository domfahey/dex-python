"""Custom exceptions for Dex API client."""

from typing import Any


class DexAPIError(Exception):
    """Base exception for Dex API errors."""

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        response_data: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data


class AuthenticationError(DexAPIError):
    """Raised when API authentication fails (401)."""

    pass


class ContactNotFoundError(DexAPIError):
    """Raised when a contact is not found (404)."""

    def __init__(self, contact_id: str) -> None:
        super().__init__(f"Contact not found: {contact_id}", status_code=404)
        self.contact_id = contact_id


class ReminderNotFoundError(DexAPIError):
    """Raised when a reminder is not found (404)."""

    def __init__(self, reminder_id: str) -> None:
        super().__init__(f"Reminder not found: {reminder_id}", status_code=404)
        self.reminder_id = reminder_id


class NoteNotFoundError(DexAPIError):
    """Raised when a note is not found (404)."""

    def __init__(self, note_id: str) -> None:
        super().__init__(f"Note not found: {note_id}", status_code=404)
        self.note_id = note_id


class RateLimitError(DexAPIError):
    """Raised when rate limit is exceeded (429)."""

    def __init__(self, message: str, retry_after: int | None = None) -> None:
        super().__init__(message, status_code=429)
        self.retry_after = retry_after


class ValidationError(DexAPIError):
    """Raised when request validation fails (400)."""

    pass
