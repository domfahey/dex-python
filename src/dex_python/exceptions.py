"""Custom exceptions for Dex API client.

This module defines the exception hierarchy for the Dex Python SDK.
All exceptions inherit from DexAPIError, which provides status_code
and response_data attributes for error handling.

Exception Hierarchy:
    DexAPIError (base)
    ├── AuthenticationError (401)
    ├── ValidationError (400)
    ├── RateLimitError (429)
    ├── ContactNotFoundError (404)
    ├── ReminderNotFoundError (404)
    └── NoteNotFoundError (404)

Example:
    >>> from dex_python import DexClient, RateLimitError
    >>> try:
    ...     client.get_contacts()
    ... except RateLimitError as e:
    ...     print(f"Rate limited, retry after {e.retry_after}s")
"""

from typing import Any


class DexAPIError(Exception):
    """Base exception for all Dex API errors.

    All API errors include the HTTP status code and optional response data
    for debugging and error handling.

    Attributes:
        status_code: HTTP status code from the API response.
        response_data: Parsed JSON response body, if available.

    Example:
        >>> try:
        ...     client.get_contact("invalid-id")
        ... except DexAPIError as e:
        ...     print(f"Error {e.status_code}: {e}")
    """

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        response_data: dict[str, Any] | None = None,
    ) -> None:
        """Initialize a DexAPIError.

        Args:
            message: Human-readable error message.
            status_code: HTTP status code from the response.
            response_data: Parsed JSON response body.
        """
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data


class AuthenticationError(DexAPIError):
    """Raised when API authentication fails (HTTP 401).

    This typically indicates an invalid or expired API key.
    Check your DEX_API_KEY environment variable.
    """

    pass


class ContactNotFoundError(DexAPIError):
    """Raised when a contact is not found (HTTP 404).

    Attributes:
        contact_id: The ID of the contact that was not found.
    """

    def __init__(self, contact_id: str) -> None:
        """Initialize with the missing contact ID.

        Args:
            contact_id: The ID of the contact that was not found.
        """
        super().__init__(f"Contact not found: {contact_id}", status_code=404)
        self.contact_id = contact_id


class ReminderNotFoundError(DexAPIError):
    """Raised when a reminder is not found (HTTP 404).

    Attributes:
        reminder_id: The ID of the reminder that was not found.
    """

    def __init__(self, reminder_id: str) -> None:
        """Initialize with the missing reminder ID.

        Args:
            reminder_id: The ID of the reminder that was not found.
        """
        super().__init__(f"Reminder not found: {reminder_id}", status_code=404)
        self.reminder_id = reminder_id


class NoteNotFoundError(DexAPIError):
    """Raised when a note is not found (HTTP 404).

    Attributes:
        note_id: The ID of the note that was not found.
    """

    def __init__(self, note_id: str) -> None:
        """Initialize with the missing note ID.

        Args:
            note_id: The ID of the note that was not found.
        """
        super().__init__(f"Note not found: {note_id}", status_code=404)
        self.note_id = note_id


class RateLimitError(DexAPIError):
    """Raised when the API rate limit is exceeded (HTTP 429).

    The retry_after attribute indicates how long to wait before retrying.

    Attributes:
        retry_after: Seconds to wait before retrying, if provided by the API.

    Example:
        >>> import time
        >>> try:
        ...     client.get_contacts()
        ... except RateLimitError as e:
        ...     time.sleep(e.retry_after or 60)
    """

    def __init__(self, message: str, retry_after: int | None = None) -> None:
        """Initialize with rate limit details.

        Args:
            message: Error message from the API.
            retry_after: Seconds to wait before retrying.
        """
        super().__init__(message, status_code=429)
        self.retry_after = retry_after


class ValidationError(DexAPIError):
    """Raised when request validation fails (HTTP 400).

    This indicates invalid request data, such as missing required fields
    or invalid field values.
    """

    pass
