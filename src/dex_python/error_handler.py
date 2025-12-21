"""Shared error handling logic for Dex API clients.

This module provides error handling utilities shared between
the synchronous and asynchronous clients.
"""

from typing import Any

import httpx

from .exceptions import (
    AuthenticationError,
    ContactNotFoundError,
    DexAPIError,
    NoteNotFoundError,
    RateLimitError,
    ReminderNotFoundError,
    ValidationError,
)


def handle_error_response(response: httpx.Response, endpoint: str) -> None:
    """Convert HTTP error response to appropriate exception.

    Args:
        response: The HTTP response with error status.
        endpoint: The API endpoint that was called.

    Raises:
        AuthenticationError: For 401 responses.
        RateLimitError: For 429 responses.
        ValidationError: For 400 responses.
        ContactNotFoundError: For 404 on /contacts endpoints.
        ReminderNotFoundError: For 404 on /reminders endpoints.
        NoteNotFoundError: For 404 on /timeline_items endpoints.
        DexAPIError: For all other error responses.
    """
    status_code = response.status_code
    try:
        data = response.json()
    except Exception:
        data = {}

    if status_code == 401:
        raise AuthenticationError(
            "Invalid API key", status_code=401, response_data=data
        )
    elif status_code == 429:
        retry_after = response.headers.get("Retry-After")
        raise RateLimitError(
            "Rate limit exceeded",
            retry_after=int(retry_after) if retry_after else None,
        )
    elif status_code == 400:
        raise ValidationError(
            data.get("error", "Validation error"),
            status_code=400,
            response_data=data,
        )
    elif status_code == 404:
        _handle_404_error(endpoint, data)
    else:
        raise DexAPIError(
            data.get("error", f"API error: {status_code}"),
            status_code=status_code,
            response_data=data,
        )


def _handle_404_error(endpoint: str, data: dict[str, Any]) -> None:
    """Handle 404 errors with entity-specific exceptions.

    Args:
        endpoint: The API endpoint that was called.
        data: The error response data.

    Raises:
        ContactNotFoundError: For /contacts endpoints.
        ReminderNotFoundError: For /reminders endpoints.
        NoteNotFoundError: For /timeline_items endpoints.
        DexAPIError: For other 404 errors.
    """
    if "/contacts/" in endpoint:
        contact_id = endpoint.split("/contacts/")[-1].split("/")[0]
        raise ContactNotFoundError(contact_id)
    elif "/reminders/" in endpoint:
        reminder_id = endpoint.split("/reminders/")[-1].split("/")[0]
        raise ReminderNotFoundError(reminder_id)
    elif "/timeline_items/" in endpoint:
        note_id = endpoint.split("/timeline_items/")[-1].split("/")[0]
        raise NoteNotFoundError(note_id)
    raise DexAPIError("Not found", status_code=404, response_data=data)
