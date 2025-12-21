"""Synchronous HTTP client for the Dex CRM API.

This module provides the main DexClient class for interacting with the
Dex API. For async operations, see AsyncDexClient in async_client.py.

Example:
    >>> from dex_python import DexClient
    >>> with DexClient() as client:
    ...     contacts = client.get_contacts(limit=10)
    ...     for contact in contacts:
    ...         print(contact["first_name"])

Environment Variables:
    DEX_API_KEY: Required. Your Dex API key.
    DEX_BASE_URL: Optional. Defaults to https://api.getdex.com/api/rest
"""

import time
from typing import Any, Self

import httpx

from .client_utils import handle_error, should_retry
from .config import Settings
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


class DexClient:
    """Synchronous client for the Dex CRM API.

    Provides full CRUD operations for contacts, reminders, and notes.
    Supports context manager protocol for automatic resource cleanup.

    Attributes:
        settings: Configuration with API key and base URL.
        max_retries: Number of retry attempts for transient errors.
        retry_delay: Base delay (seconds) between retries.

    Example:
        >>> with DexClient() as client:
        ...     contact = client.get_contact("abc123")
        ...     print(contact["first_name"])
    """

    def __init__(
        self,
        settings: Settings | None = None,
        max_retries: int = 0,
        retry_delay: float = 1.0,
    ) -> None:
        """Initialize the Dex API client.

        Args:
            settings: API configuration. If None, loads from environment.
            max_retries: Max retry attempts for transient errors (default: 0).
            retry_delay: Base delay between retries in seconds.
                Uses exponential backoff: delay * 2^attempt.
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



    def _request_with_retry(
        self, method: str, endpoint: str, **kwargs: Any
    ) -> httpx.Response:
        """Execute HTTP request with automatic retry for transient errors.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE).
            endpoint: API endpoint path.
            **kwargs: Additional arguments passed to httpx.request.

        Returns:
            The HTTP response (may be error response if retries exhausted).
        """
        last_response: httpx.Response | None = None

        for attempt in range(self.max_retries + 1):
            response = self._client.request(method, endpoint, **kwargs)
            last_response = response

            if response.status_code < 400:
                return response

            is_last_attempt = attempt == self.max_retries
            if not should_retry(response.status_code) or is_last_attempt:
                return response

            # Exponential backoff
            delay = self.retry_delay * (2**attempt)
            time.sleep(delay)

        # Should never reach here, but satisfy type checker
        assert last_response is not None
        return last_response

    def _request(self, method: str, endpoint: str, **kwargs: Any) -> dict[str, Any]:
        """Execute API request and return parsed JSON response.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE).
            endpoint: API endpoint path.
            **kwargs: Additional arguments passed to httpx.request.

        Returns:
            Parsed JSON response as dictionary.

        Raises:
            DexAPIError: If the request fails.
        """
        response = self._request_with_retry(method, endpoint, **kwargs)
        if response.status_code >= 400:
            handle_error(response, endpoint)
        result: dict[str, Any] = response.json()
        return result

    # =========================================================================
    # Contacts API
    # =========================================================================

    def get_contacts(self, limit: int = 100, offset: int = 0) -> list[dict[str, Any]]:
        """Fetch a paginated list of contacts.

        Args:
            limit: Maximum number of contacts to return (default: 100).
            offset: Number of contacts to skip for pagination.

        Returns:
            List of contact dictionaries.
        """
        endpoint = "/contacts"
        response = self._request_with_retry(
            "GET",
            endpoint,
            params={"limit": limit, "offset": offset},
        )
        if response.status_code >= 400:
            handle_error(response, endpoint)
        data: dict[str, Any] = response.json()
        result: list[dict[str, Any]] = data.get("contacts", [])
        return result

    def get_contacts_paginated(
        self, limit: int = 100, offset: int = 0
    ) -> PaginatedContacts:
        """Fetch contacts with pagination metadata.

        Use this when you need to iterate through all contacts.

        Args:
            limit: Maximum number of contacts to return (default: 100).
            offset: Number of contacts to skip for pagination.

        Returns:
            PaginatedContacts with contacts list and has_more property.
        """
        endpoint = "/contacts"
        response = self._request_with_retry(
            "GET",
            endpoint,
            params={"limit": limit, "offset": offset},
        )
        if response.status_code >= 400:
            handle_error(response, endpoint)
        data: dict[str, Any] = response.json()
        return PaginatedContacts(
            contacts=data.get("contacts", []),
            total=extract_contacts_total(data),
            limit=limit,
            offset=offset,
        )

    def get_contact(self, contact_id: str) -> dict[str, Any]:
        """Fetch a single contact by ID.

        Args:
            contact_id: The unique contact identifier.

        Returns:
            Contact dictionary, or empty dict if not found.
        """
        data = self._request("GET", f"/contacts/{contact_id}")
        contacts = data.get("contacts", [])
        if contacts:
            result: dict[str, Any] = contacts[0]
            return result
        return {}

    def get_contact_by_email(self, email: str) -> dict[str, Any] | None:
        """Look up a contact by email address.

        Args:
            email: Email address to search for.

        Returns:
            Contact dictionary if found, None otherwise.
        """
        data = self._request("GET", "/search/contacts", params={"email": email})
        contacts = data.get("search_contacts_by_exact_email", [])
        if contacts:
            result: dict[str, Any] = contacts[0]
            return result
        return None

    def create_contact(self, contact: ContactCreate) -> dict[str, Any]:
        """Create a new contact.

        Args:
            contact: Contact data. Use ContactCreate.with_email() or
                ContactCreate.with_phone() for convenience.

        Returns:
            The created contact data including server-assigned ID.
        """
        data = self._request(
            "POST",
            "/contacts",
            json={"contact": contact.model_dump(exclude_none=True)},
        )
        return dict(extract_contact_entity(data))

    def update_contact(self, update: ContactUpdate) -> dict[str, Any]:
        """Update an existing contact.

        Args:
            update: Update specification with contact_id and changes.

        Returns:
            The updated contact data.
        """
        data = self._request(
            "PUT",
            f"/contacts/{update.contact_id}",
            json=update.model_dump(exclude_none=True, by_alias=True),
        )
        return dict(extract_contact_entity(data))

    def delete_contact(self, contact_id: str) -> dict[str, Any]:
        """Delete a contact by ID.

        Args:
            contact_id: The unique contact identifier.

        Returns:
            The deleted contact data.
        """
        data = self._request("DELETE", f"/contacts/{contact_id}")
        return dict(extract_contact_entity(data))

    # =========================================================================
    # Reminders API
    # =========================================================================

    def get_reminders(self, limit: int = 100, offset: int = 0) -> list[dict[str, Any]]:
        """Fetch a paginated list of reminders.

        Args:
            limit: Maximum number of reminders to return (default: 100).
            offset: Number of reminders to skip for pagination.

        Returns:
            List of reminder dictionaries.
        """
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
        """Fetch reminders with pagination metadata.

        Args:
            limit: Maximum number of reminders to return (default: 100).
            offset: Number of reminders to skip for pagination.

        Returns:
            PaginatedReminders with reminders list and has_more property.
        """
        endpoint = "/reminders"
        response = self._request_with_retry(
            "GET",
            endpoint,
            params={"limit": limit, "offset": offset},
        )
        if response.status_code >= 400:
            handle_error(response, endpoint)
        data: dict[str, Any] = response.json()
        return PaginatedReminders(
            reminders=data.get("reminders", []),
            total=extract_reminders_total(data),
            limit=limit,
            offset=offset,
        )

    def create_reminder(self, reminder: ReminderCreate) -> dict[str, Any]:
        """Create a new reminder.

        Args:
            reminder: Reminder data. Use ReminderCreate.with_contacts()
                to link to specific contacts.

        Returns:
            The created reminder data including server-assigned ID.
        """
        data = self._request(
            "POST",
            "/reminders",
            json={"reminder": reminder.model_dump(exclude_none=True)},
        )
        return dict(extract_reminder_entity(data))

    def update_reminder(self, update: ReminderUpdate) -> dict[str, Any]:
        """Update an existing reminder.

        Args:
            update: Update specification. Use ReminderUpdate.mark_complete()
                for the common completion pattern.

        Returns:
            The updated reminder data.
        """
        data = self._request(
            "PUT",
            f"/reminders/{update.reminder_id}",
            json=update.model_dump(exclude_none=True),
        )
        return dict(extract_reminder_entity(data))

    def delete_reminder(self, reminder_id: str) -> dict[str, Any]:
        """Delete a reminder by ID.

        Args:
            reminder_id: The unique reminder identifier.

        Returns:
            The deleted reminder data.
        """
        data = self._request("DELETE", f"/reminders/{reminder_id}")
        return dict(extract_reminder_entity(data))

    # =========================================================================
    # Notes (Timeline Items) API
    # =========================================================================

    def get_notes(self, limit: int = 100, offset: int = 0) -> list[dict[str, Any]]:
        """Fetch a paginated list of notes (timeline items).

        Args:
            limit: Maximum number of notes to return (default: 100).
            offset: Number of notes to skip for pagination.

        Returns:
            List of note dictionaries.
        """
        data = self._request(
            "GET",
            "/timeline_items",
            params={"limit": limit, "offset": offset},
        )
        result: list[dict[str, Any]] = data.get("timeline_items", [])
        return result

    def get_notes_paginated(self, limit: int = 100, offset: int = 0) -> PaginatedNotes:
        """Fetch notes with pagination metadata.

        Args:
            limit: Maximum number of notes to return (default: 100).
            offset: Number of notes to skip for pagination.

        Returns:
            PaginatedNotes with notes list and has_more property.
        """
        endpoint = "/timeline_items"
        response = self._request_with_retry(
            "GET",
            endpoint,
            params={"limit": limit, "offset": offset},
        )
        if response.status_code >= 400:
            handle_error(response, endpoint)
        data: dict[str, Any] = response.json()
        return PaginatedNotes(
            notes=data.get("timeline_items", []),
            total=extract_contacts_total(data),  # Notes use same format as contacts
            limit=limit,
            offset=offset,
        )

    def get_notes_by_contact(self, contact_id: str) -> list[dict[str, Any]]:
        """Fetch all notes associated with a specific contact.

        Args:
            contact_id: The unique contact identifier.

        Returns:
            List of note dictionaries for this contact.
        """
        data = self._request("GET", f"/timeline_items/contacts/{contact_id}")
        result: list[dict[str, Any]] = data.get("timeline_items", [])
        return result

    def create_note(self, note: NoteCreate) -> dict[str, Any]:
        """Create a new note (timeline item).

        Args:
            note: Note data. Use NoteCreate.with_contacts()
                to link to specific contacts.

        Returns:
            The created note data including server-assigned ID.
        """
        data = self._request(
            "POST",
            "/timeline_items",
            json={"timeline_event": note.model_dump(exclude_none=True)},
        )
        return dict(extract_note_entity(data))

    def update_note(self, update: NoteUpdate) -> dict[str, Any]:
        """Update an existing note.

        Args:
            update: Update specification with note_id and changes.

        Returns:
            The updated note data.
        """
        data = self._request(
            "PUT",
            f"/timeline_items/{update.note_id}",
            json=update.model_dump(exclude_none=True),
        )
        return dict(extract_note_entity(data))

    def delete_note(self, note_id: str) -> dict[str, Any]:
        """Delete a note by ID.

        Args:
            note_id: The unique note identifier.

        Returns:
            The deleted note data.
        """
        data = self._request("DELETE", f"/timeline_items/{note_id}")
        return dict(extract_note_entity(data))

    # =========================================================================
    # Client Lifecycle
    # =========================================================================

    def close(self) -> None:
        """Close the underlying HTTP client and release resources."""
        self._client.close()

    def __enter__(self) -> Self:
        """Enter context manager (returns self)."""
        return self

    def __exit__(self, *args: object) -> None:
        """Exit context manager (closes client)."""
        self.close()
