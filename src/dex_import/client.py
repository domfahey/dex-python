"""Dex API client."""

import time
from typing import Any, Self

import httpx

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
    ContactCreate,
    ContactUpdate,
    NoteCreate,
    NoteUpdate,
    PaginatedContacts,
    PaginatedNotes,
    PaginatedReminders,
    ReminderCreate,
    ReminderUpdate,
    extract_contact_entity,
    extract_contacts_total,
    extract_note_entity,
    extract_reminder_entity,
    extract_reminders_total,
)

# Status codes that should be retried
RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}


class DexClient:
    """Client for the Dex CRM API."""

    def __init__(
        self,
        settings: Settings | None = None,
        max_retries: int = 0,
        retry_delay: float = 1.0,
    ) -> None:
        """Initialize the client with settings.

        Args:
            settings: API settings (loads from env if not provided)
            max_retries: Max retry attempts for transient errors (0 = no retries)
            retry_delay: Base delay between retries in seconds (exponential backoff)
        """
        self.settings = settings if settings is not None else Settings()  # type: ignore[call-arg]
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self._client = httpx.Client(
            base_url=self.settings.dex_base_url,
            headers={
                "Content-Type": "application/json",
                "x-hasura-dex-api-key": self.settings.dex_api_key,
            },
            timeout=30.0,
        )

    def _handle_error(self, response: httpx.Response, endpoint: str) -> None:
        """Handle HTTP error responses and raise appropriate exceptions."""
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

    def _should_retry(self, status_code: int) -> bool:
        """Check if request should be retried based on status code."""
        return status_code in RETRYABLE_STATUS_CODES

    def _request_with_retry(
        self, method: str, endpoint: str, **kwargs: Any
    ) -> httpx.Response:
        """Make a request with retry logic for transient errors."""
        last_response: httpx.Response | None = None

        for attempt in range(self.max_retries + 1):
            response = self._client.request(method, endpoint, **kwargs)
            last_response = response

            if response.status_code < 400:
                return response

            is_last_attempt = attempt == self.max_retries
            if not self._should_retry(response.status_code) or is_last_attempt:
                return response

            # Exponential backoff
            delay = self.retry_delay * (2**attempt)
            time.sleep(delay)

        # Should never reach here, but satisfy type checker
        assert last_response is not None
        return last_response

    def _request(self, method: str, endpoint: str, **kwargs: Any) -> dict[str, Any]:
        """Make an API request."""
        response = self._request_with_retry(method, endpoint, **kwargs)
        if response.status_code >= 400:
            self._handle_error(response, endpoint)
        result: dict[str, Any] = response.json()
        return result

    # =========================================================================
    # Contacts API
    # =========================================================================

    def get_contacts(self, limit: int = 100, offset: int = 0) -> list[dict[str, Any]]:
        """Fetch paginated list of contacts."""
        endpoint = "/contacts"
        response = self._request_with_retry(
            "GET",
            endpoint,
            params={"limit": limit, "offset": offset},
        )
        if response.status_code >= 400:
            self._handle_error(response, endpoint)
        data: dict[str, Any] = response.json()
        result: list[dict[str, Any]] = data.get("contacts", [])
        return result

    def get_contacts_paginated(
        self, limit: int = 100, offset: int = 0
    ) -> PaginatedContacts:
        """Fetch paginated contacts with metadata."""
        endpoint = "/contacts"
        response = self._request_with_retry(
            "GET",
            endpoint,
            params={"limit": limit, "offset": offset},
        )
        if response.status_code >= 400:
            self._handle_error(response, endpoint)
        data: dict[str, Any] = response.json()
        return PaginatedContacts(
            contacts=data.get("contacts", []),
            total=extract_contacts_total(data),
            limit=limit,
            offset=offset,
        )

    def get_contact(self, contact_id: str) -> dict[str, Any]:
        """Fetch a single contact by ID."""
        data = self._request("GET", f"/contacts/{contact_id}")
        contacts = data.get("contacts", [])
        if contacts:
            result: dict[str, Any] = contacts[0]
            return result
        return {}

    def get_contact_by_email(self, email: str) -> dict[str, Any] | None:
        """Fetch a contact by email address."""
        data = self._request("GET", "/search/contacts", params={"email": email})
        contacts = data.get("search_contacts_by_exact_email", [])
        if contacts:
            result: dict[str, Any] = contacts[0]
            return result
        return None

    def create_contact(self, contact: ContactCreate) -> dict[str, Any]:
        """Create a new contact."""
        data = self._request(
            "POST",
            "/contacts",
            json={"contact": contact.model_dump(exclude_none=True)},
        )
        return dict(extract_contact_entity(data))

    def update_contact(self, update: ContactUpdate) -> dict[str, Any]:
        """Update an existing contact."""
        data = self._request(
            "PUT",
            f"/contacts/{update.contact_id}",
            json=update.model_dump(exclude_none=True, by_alias=True),
        )
        return dict(extract_contact_entity(data))

    def delete_contact(self, contact_id: str) -> dict[str, Any]:
        """Delete a contact by ID."""
        data = self._request("DELETE", f"/contacts/{contact_id}")
        return dict(extract_contact_entity(data))

    # =========================================================================
    # Reminders API
    # =========================================================================

    def get_reminders(self, limit: int = 100, offset: int = 0) -> list[dict[str, Any]]:
        """Fetch paginated list of reminders."""
        data = self._request(
            "GET",
            "/reminders",
            params={"limit": limit, "offset": offset},
        )
        result: list[dict[str, Any]] = data.get("reminders", [])
        return result

    def get_reminders_paginated(
        self, limit: int = 100, offset: int = 0
    ) -> PaginatedReminders:
        """Fetch paginated reminders with metadata."""
        endpoint = "/reminders"
        response = self._request_with_retry(
            "GET",
            endpoint,
            params={"limit": limit, "offset": offset},
        )
        if response.status_code >= 400:
            self._handle_error(response, endpoint)
        data: dict[str, Any] = response.json()
        return PaginatedReminders(
            reminders=data.get("reminders", []),
            total=extract_reminders_total(data),
            limit=limit,
            offset=offset,
        )

    def create_reminder(self, reminder: ReminderCreate) -> dict[str, Any]:
        """Create a new reminder."""
        data = self._request(
            "POST",
            "/reminders",
            json={"reminder": reminder.model_dump(exclude_none=True)},
        )
        return dict(extract_reminder_entity(data))

    def update_reminder(self, update: ReminderUpdate) -> dict[str, Any]:
        """Update an existing reminder."""
        data = self._request(
            "PUT",
            f"/reminders/{update.reminder_id}",
            json=update.model_dump(exclude_none=True),
        )
        return dict(extract_reminder_entity(data))

    def delete_reminder(self, reminder_id: str) -> dict[str, Any]:
        """Delete a reminder by ID."""
        data = self._request("DELETE", f"/reminders/{reminder_id}")
        return dict(extract_reminder_entity(data))

    # =========================================================================
    # Notes (Timeline Items) API
    # =========================================================================

    def get_notes(self, limit: int = 100, offset: int = 0) -> list[dict[str, Any]]:
        """Fetch paginated list of notes."""
        data = self._request(
            "GET",
            "/timeline_items",
            params={"limit": limit, "offset": offset},
        )
        result: list[dict[str, Any]] = data.get("timeline_items", [])
        return result

    def get_notes_paginated(
        self, limit: int = 100, offset: int = 0
    ) -> PaginatedNotes:
        """Fetch paginated notes with metadata."""
        endpoint = "/timeline_items"
        response = self._request_with_retry(
            "GET",
            endpoint,
            params={"limit": limit, "offset": offset},
        )
        if response.status_code >= 400:
            self._handle_error(response, endpoint)
        data: dict[str, Any] = response.json()
        return PaginatedNotes(
            notes=data.get("timeline_items", []),
            total=extract_contacts_total(data),  # Notes use same format as contacts
            limit=limit,
            offset=offset,
        )

    def get_notes_by_contact(self, contact_id: str) -> list[dict[str, Any]]:
        """Fetch notes for a specific contact."""
        data = self._request("GET", f"/timeline_items/contacts/{contact_id}")
        result: list[dict[str, Any]] = data.get("timeline_items", [])
        return result

    def create_note(self, note: NoteCreate) -> dict[str, Any]:
        """Create a new note."""
        data = self._request(
            "POST",
            "/timeline_items",
            json={"timeline_event": note.model_dump(exclude_none=True)},
        )
        return dict(extract_note_entity(data))

    def update_note(self, update: NoteUpdate) -> dict[str, Any]:
        """Update an existing note."""
        data = self._request(
            "PUT",
            f"/timeline_items/{update.note_id}",
            json=update.model_dump(exclude_none=True),
        )
        return dict(extract_note_entity(data))

    def delete_note(self, note_id: str) -> dict[str, Any]:
        """Delete a note by ID."""
        data = self._request("DELETE", f"/timeline_items/{note_id}")
        return dict(extract_note_entity(data))

    # =========================================================================
    # Client Management
    # =========================================================================

    def close(self) -> None:
        """Close the HTTP client."""
        self._client.close()

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()
