"""Shared utilities for DexClient and AsyncDexClient.

This module contains common functionality used by both synchronous and
asynchronous API clients to reduce code duplication.
"""

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

# HTTP status codes that indicate transient failures worth retrying
RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}


def should_retry(status_code: int) -> bool:
    """Check if a request should be retried based on HTTP status code.

    Args:
        status_code: The HTTP status code from the response.

    Returns:
        True if the request should be retried, False otherwise.
    """
    return status_code in RETRYABLE_STATUS_CODES


def handle_error(response: httpx.Response, endpoint: str) -> None:
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
    else:
        raise DexAPIError(
            data.get("error", f"API error: {status_code}"),
            status_code=status_code,
            response_data=data,
        )
