"""Asynchronous HTTP client for the Dex CRM API.

This module provides AsyncDexClient for async/await usage patterns.
For synchronous operations, see DexClient in client.py.

Example:
    >>> from dex_python import AsyncDexClient
    >>> async with AsyncDexClient() as client:
    ...     contacts = await client.get_contacts(limit=10)
    ...     for contact in contacts:
    ...         print(contact["first_name"])

Environment Variables:
    DEX_API_KEY: Required. Your Dex API key.
    DEX_BASE_URL: Optional. Defaults to https://api.getdex.com/api/rest
"""

import asyncio
import re
from typing import Any, Self, cast

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

# HTTP status codes that indicate transient failures worth retrying
RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}


class AsyncDexClient:
    """Asynchronous client for the Dex CRM API.

    Provides async versions of all CRUD operations for contacts, reminders,
    and notes. Supports async context manager protocol.

    Attributes:
        settings: Configuration with API key and base URL.
        max_retries: Number of retry attempts for transient errors.
        retry_delay: Base delay (seconds) between retries.

    Example:
        >>> async with AsyncDexClient() as client:
        ...     contact = await client.get_contact("abc123")
        ...     print(contact["first_name"])
    """

    def __init__(
        self,
        settings: Settings | None = None,
        max_retries: int = 0,
        retry_delay: float = 1.0,
    ) -> None:
        """Initialize the async Dex API client.

        Args:
            settings: API configuration. If None, loads from environment.
            max_retries: Max retry attempts for transient errors (default: 0).
            retry_delay: Base delay between retries in seconds.
                Uses exponential backoff: delay * 2^attempt.
        """
        self.settings = settings if settings is not None else Settings()  # type: ignore[call-arg]
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self._client = httpx.AsyncClient(
            base_url=self.settings.dex_base_url,
            headers={
                "Content-Type": "application/json",
                "x-hasura-dex-api-key": self.settings.dex_api_key.get_secret_value(),
            },
            timeout=30.0,
        )

    def _should_retry(self, status_code: int) -> bool:
        """Check if a request should be retried based on HTTP status code."""
        return status_code in RETRYABLE_STATUS_CODES

    def _handle_error(self, response: httpx.Response, endpoint: str) -> None:
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
            if re.fullmatch(r"/contacts/[^/]+/?", endpoint):
                contact_id = endpoint.split("/contacts/")[-1].split("/")[0]
                raise ContactNotFoundError(contact_id)
            if re.fullmatch(r"/reminders/[^/]+/?", endpoint):
                reminder_id = endpoint.split("/reminders/")[-1].split("/")[0]
                raise ReminderNotFoundError(reminder_id)
            if re.fullmatch(r"/timeline/[^/]+/?", endpoint) or re.fullmatch(
                r"/timeline_items/[^/]+/?", endpoint
            ):
                note_id = endpoint.rstrip("/").split("/")[-1]
                raise NoteNotFoundError(note_id)
            raise DexAPIError("Not found", status_code=404, response_data=data)
        else:
            raise DexAPIError(
                data.get("error", f"API error: {status_code}"),
                status_code=status_code,
                response_data=data,
            )

    async def _request_with_retry(
        self, method: str, endpoint: str, **kwargs: Any
    ) -> httpx.Response:
        """Execute async HTTP request with retry for transient errors.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE).
            endpoint: API endpoint path.
            **kwargs: Additional arguments passed to httpx.request.

        Returns:
            The HTTP response (may be error response if retries exhausted).
        """
        last_response: httpx.Response | None = None

        for attempt in range(self.max_retries + 1):
            response = await self._client.request(method, endpoint, **kwargs)
            last_response = response

            if response.status_code < 400:
                return response

            is_last_attempt = attempt == self.max_retries
            if not self._should_retry(response.status_code) or is_last_attempt:
                return response

            # Exponential backoff
            delay = self.retry_delay * (2**attempt)
            await asyncio.sleep(delay)

        # Should never reach here, but satisfy type checker
        assert last_response is not None
        return last_response

    async def _request(
        self, method: str, endpoint: str, **kwargs: Any
    ) -> dict[str, Any]:
        """Execute async API request and return parsed JSON response.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE).
            endpoint: API endpoint path.
            **kwargs: Additional arguments passed to httpx.request.

        Returns:
            Parsed JSON response as dictionary.

        Raises:
            DexAPIError: If the request fails.
        """
        response = await self._request_with_retry(method, endpoint, **kwargs)
        if response.status_code >= 400:
            self._handle_error(response, endpoint)
        result: dict[str, Any] = response.json()
        return result

    async def _request_with_fallback(
        self, method: str, endpoints: list[str], **kwargs: Any
    ) -> dict[str, Any]:
        """Execute API request with fallback endpoints.

        Tries each endpoint in order and falls back to the next endpoint when the
        previous returns a 404. For other errors, the error from the first
        failing endpoint is raised immediately.
        """

        if not endpoints:
            raise DexAPIError("No fallback endpoints provided", status_code=500)

        for index, endpoint in enumerate(endpoints):
            response = await self._request_with_retry(method, endpoint, **kwargs)
            if response.status_code < 400:
                return cast(dict[str, Any], response.json())

            is_last_attempt = index >= len(endpoints) - 1
            if response.status_code == 404 and not is_last_attempt:
                continue

            self._handle_error(response, endpoint)

        raise DexAPIError("Request failed", status_code=500)

    # =========================================================================
    # Contacts API
    # =========================================================================

    async def get_contacts(
        self, limit: int = 100, offset: int = 0
    ) -> list[dict[str, Any]]:
        """Fetch a paginated list of contacts.

        Args:
            limit: Maximum number of contacts to return (default: 100).
            offset: Number of contacts to skip for pagination.

        Returns:
            List of contact dictionaries.
        """
        endpoint = "/contacts"
        response = await self._request_with_retry(
            "GET",
            endpoint,
            params={"limit": limit, "offset": offset},
        )
        if response.status_code >= 400:
            self._handle_error(response, endpoint)
        data: dict[str, Any] = response.json()
        result: list[dict[str, Any]] = data.get("contacts", [])
        return result

    async def get_contacts_paginated(
        self, limit: int = 100, offset: int = 0
    ) -> PaginatedContacts:
        """Fetch contacts with pagination metadata.

        Args:
            limit: Maximum number of contacts to return (default: 100).
            offset: Number of contacts to skip for pagination.

        Returns:
            PaginatedContacts with contacts list and has_more property.
        """
        endpoint = "/contacts"
        response = await self._request_with_retry(
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

    async def update_contacts_bulk(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Update multiple contacts in a single request."""
        data = await self._request("PUT", "/contacts", json=payload)
        return dict(data)

    async def delete_contacts_bulk(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Delete multiple contacts in a single request."""
        data = await self._request("DELETE", "/contacts", json=payload)
        return dict(data)

    async def count_contacts(self) -> int:
        """Get total number of contacts."""
        data = await self._request("GET", "/contacts/count")
        if isinstance(data, int):
            return data
        if isinstance(data, dict):
            for key in ("count", "total", "contacts_count"):
                count = data.get(key)
                if isinstance(count, int):
                    return count
            aggregate = data.get("aggregate")
            if isinstance(aggregate, dict):
                count = aggregate.get("count")
                if isinstance(count, int):
                    return count
            total = data.get("total")
            if isinstance(total, dict):
                aggregate = total.get("aggregate")
                if isinstance(aggregate, dict):
                    count = aggregate.get("count")
                    if isinstance(count, int):
                        return count
                count = total.get("count")
                if isinstance(count, int):
                    return count
            pagination = data.get("pagination")
            if isinstance(pagination, dict):
                total = pagination.get("total")
                if isinstance(total, dict):
                    count = total.get("count")
                    if isinstance(count, int):
                        return count
                    aggregate = total.get("aggregate")
                    if isinstance(aggregate, dict):
                        count = aggregate.get("count")
                        if isinstance(count, int):
                            return count
        return 0

    async def search_contacts(
        self, params: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        """Search contacts."""
        data = await self._request("GET", "/contacts/search", params=params or {})
        candidates = data.get("contacts")
        if isinstance(candidates, list):
            return candidates
        return []

    async def filter_contacts(self, payload: dict[str, Any]) -> list[dict[str, Any]]:
        """Filter contacts."""
        data = await self._request("POST", "/contacts/filter", json=payload)
        candidates = data.get("contacts")
        if isinstance(candidates, list):
            return candidates
        return []

    async def find_contacts_by_emails(
        self, payload: dict[str, Any] | list[str]
    ) -> list[dict[str, Any]]:
        """Find contacts by email addresses."""
        body = payload if isinstance(payload, dict) else {"emails": payload}
        data = await self._request("POST", "/contacts/by-emails", json=body)
        candidates = data.get("contacts")
        if isinstance(candidates, list):
            return candidates
        return []

    async def merge_contacts(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Merge multiple contacts."""
        data = await self._request("POST", "/contacts/merge", json=payload)
        return dict(data)

    async def get_contact(self, contact_id: str) -> dict[str, Any]:
        """Fetch a single contact by ID.

        Args:
            contact_id: The unique contact identifier.

        Returns:
            Contact dictionary, or empty dict if not found.
        """
        data = await self._request("GET", f"/contacts/{contact_id}")
        contacts = data.get("contacts", [])
        if contacts:
            result: dict[str, Any] = contacts[0]
            return result
        return {}

    async def get_contact_by_email(self, email: str) -> dict[str, Any] | None:
        """Look up a contact by email address.

        Args:
            email: Email address to search for.

        Returns:
            Contact dictionary if found, None otherwise.
        """
        data = await self._request("GET", "/search/contacts", params={"email": email})
        contacts = data.get("search_contacts_by_exact_email", [])
        if contacts:
            result: dict[str, Any] = contacts[0]
            return result
        return None

    async def create_contact(self, contact: ContactCreate) -> dict[str, Any]:
        """Create a new contact.

        Args:
            contact: Contact data. Use ContactCreate.with_email() or
                ContactCreate.with_phone() for convenience.

        Returns:
            The created contact data including server-assigned ID.
        """
        data = await self._request(
            "POST",
            "/contacts",
            json={"contact": contact.model_dump(exclude_none=True, mode="json")},
        )
        return dict(extract_contact_entity(data))

    async def update_contact(self, update: ContactUpdate) -> dict[str, Any]:
        """Update an existing contact.

        Args:
            update: Update specification with contact_id and changes.

        Returns:
            The updated contact data.
        """
        data = await self._request(
            "PUT",
            f"/contacts/{update.contact_id}",
            json=update.model_dump(exclude_none=True, by_alias=True, mode="json"),
        )
        return dict(extract_contact_entity(data))

    async def delete_contact(self, contact_id: str) -> dict[str, Any]:
        """Delete a contact by ID.

        Args:
            contact_id: The unique contact identifier.

        Returns:
            The deleted contact data.
        """
        data = await self._request("DELETE", f"/contacts/{contact_id}")
        return dict(extract_contact_entity(data))

    # =========================================================================
    # Reminders API
    # =========================================================================

    async def get_reminders(
        self, limit: int = 100, offset: int = 0
    ) -> list[dict[str, Any]]:
        """Fetch a paginated list of reminders.

        Args:
            limit: Maximum number of reminders to return (default: 100).
            offset: Number of reminders to skip for pagination.

        Returns:
            List of reminder dictionaries.
        """
        data = await self._request(
            "GET",
            "/reminders",
            params={"limit": limit, "offset": offset},
        )
        result: list[dict[str, Any]] = data.get("reminders", [])
        return result

    async def get_reminder(self, reminder_id: str) -> dict[str, Any]:
        """Fetch a single reminder by ID."""
        data = await self._request("GET", f"/reminders/{reminder_id}")
        reminders = data.get("reminders")
        if isinstance(reminders, list) and reminders:
            result: dict[str, Any] = reminders[0]
            return result
        reminder = data.get("reminder")
        if isinstance(reminder, dict):
            return reminder
        return dict(data)

    async def get_recurring_reminders(self) -> list[dict[str, Any]]:
        """Fetch recurring reminders."""
        data = await self._request("GET", "/reminders/recurring")
        reminders = data.get("reminders")
        if isinstance(reminders, list):
            return reminders
        return []

    async def get_reminders_paginated(
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
        response = await self._request_with_retry(
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

    async def create_reminder(self, reminder: ReminderCreate) -> dict[str, Any]:
        """Create a new reminder.

        Args:
            reminder: Reminder data. Use ReminderCreate.with_contacts()
                to link to specific contacts.

        Returns:
            The created reminder data including server-assigned ID.
        """
        data = await self._request(
            "POST",
            "/reminders",
            json={"reminder": reminder.model_dump(exclude_none=True, mode="json")},
        )
        return dict(extract_reminder_entity(data))

    async def update_reminder(self, update: ReminderUpdate) -> dict[str, Any]:
        """Update an existing reminder.

        Args:
            update: Update specification. Use ReminderUpdate.mark_complete()
                for the common completion pattern.

        Returns:
            The updated reminder data.
        """
        data = await self._request(
            "PUT",
            f"/reminders/{update.reminder_id}",
            json=update.model_dump(exclude_none=True, mode="json"),
        )
        return dict(extract_reminder_entity(data))

    async def delete_reminder(self, reminder_id: str) -> dict[str, Any]:
        """Delete a reminder by ID.

        Args:
            reminder_id: The unique reminder identifier.

        Returns:
            The deleted reminder data.
        """
        data = await self._request("DELETE", f"/reminders/{reminder_id}")
        return dict(extract_reminder_entity(data))

    # =========================================================================
    # Notes (Timeline Items) API
    # =========================================================================

    async def get_notes(
        self, limit: int = 100, offset: int = 0
    ) -> list[dict[str, Any]]:
        """Fetch a paginated list of notes (timeline items).

        Args:
            limit: Maximum number of notes to return (default: 100).
            offset: Number of notes to skip for pagination.

        Returns:
            List of note dictionaries.
        """
        data = await self._request(
            "GET",
            "/timeline_items",
            params={"limit": limit, "offset": offset},
        )
        result: list[dict[str, Any]] = data.get("timeline_items", [])
        return result

    async def get_notes_paginated(
        self, limit: int = 100, offset: int = 0
    ) -> PaginatedNotes:
        """Fetch notes with pagination metadata.

        Args:
            limit: Maximum number of notes to return (default: 100).
            offset: Number of notes to skip for pagination.

        Returns:
            PaginatedNotes with notes list and has_more property.
        """
        endpoint = "/timeline_items"
        response = await self._request_with_retry(
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

    async def get_timeline(
        self, limit: int = 100, offset: int = 0
    ) -> list[dict[str, Any]]:
        """Fetch a paginated list of timeline items from docs endpoint."""
        data = await self._request(
            "GET",
            "/timeline",
            params={"limit": limit, "offset": offset},
        )
        candidates = data.get("timeline")
        if isinstance(candidates, list):
            return candidates
        candidates = data.get("timeline_items")
        if isinstance(candidates, list):
            return candidates
        return []

    async def get_timeline_note(self, note_id: str) -> dict[str, Any]:
        """Fetch a single timeline item."""
        data = await self._request("GET", f"/timeline/{note_id}")
        if not isinstance(data, dict):
            return {}
        note = data.get("timeline_item")
        if isinstance(note, dict):
            return note
        timeline = data.get("timeline")
        if isinstance(timeline, dict):
            return timeline
        return {}

    async def count_timeline(self) -> int:
        """Get total number of timeline items."""
        data = await self._request("GET", "/timeline/count")
        if isinstance(data, int):
            return data
        if isinstance(data, dict):
            count = data.get("count")
            if isinstance(count, int):
                return count
            total = data.get("total")
            if isinstance(total, dict):
                aggregate = total.get("aggregate")
                if isinstance(aggregate, dict):
                    count = aggregate.get("count")
                    if isinstance(count, int):
                        return count
                count = total.get("count")
                if isinstance(count, int):
                    return count
            pagination = data.get("pagination")
            if isinstance(pagination, dict):
                total = pagination.get("total")
                if isinstance(total, dict):
                    count = total.get("count")
                    if isinstance(count, int):
                        return count
                    aggregate = total.get("aggregate")
                    if isinstance(aggregate, dict):
                        count = aggregate.get("count")
                        if isinstance(count, int):
                            return count
        return 0

    async def get_timeline_note_types(self) -> list[str]:
        """Fetch supported timeline note types."""
        data = await self._request("GET", "/timeline/note-types")
        for key in ("note_types", "timeline_note_types", "types"):
            candidates = data.get(key)
            if isinstance(candidates, list):
                return candidates
        return []

    async def get_notes_by_contact(self, contact_id: str) -> list[dict[str, Any]]:
        """Fetch all notes associated with a specific contact.

        Args:
            contact_id: The unique contact identifier.

        Returns:
            List of note dictionaries for this contact.
        """
        data = await self._request("GET", f"/timeline_items/contacts/{contact_id}")
        result: list[dict[str, Any]] = data.get("timeline_items", [])
        return result

    async def get_groups(self) -> list[dict[str, Any]]:
        """Fetch all groups."""
        data = await self._request("GET", "/groups")
        groups = data.get("groups")
        if isinstance(groups, list):
            return groups
        return []

    async def get_group(self, group_id: str) -> dict[str, Any]:
        """Fetch a single group."""
        data = await self._request("GET", f"/groups/{group_id}")
        return dict(data)

    async def create_group(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Create a new group."""
        data = await self._request("POST", "/groups", json=payload)
        return dict(data)

    async def update_group(
        self, group_id: str, payload: dict[str, Any]
    ) -> dict[str, Any]:
        """Update an existing group."""
        data = await self._request("PUT", f"/groups/{group_id}", json=payload)
        return dict(data)

    async def delete_group(self, group_id: str) -> dict[str, Any]:
        """Delete a group."""
        data = await self._request("DELETE", f"/groups/{group_id}")
        return dict(data)

    async def count_groups(self) -> int:
        """Get total number of groups."""
        data = await self._request("GET", "/groups/count")
        if isinstance(data, int):
            return data
        if isinstance(data, dict):
            count = data.get("count")
            if isinstance(count, int):
                return count
        return 0

    async def get_group_contacts(self, group_id: str) -> list[dict[str, Any]]:
        """Fetch contacts in a group."""
        data = await self._request("GET", f"/groups/{group_id}/contacts")
        candidates = data.get("contacts")
        if isinstance(candidates, list):
            return candidates
        return []

    async def add_group_contacts(
        self, group_id: str, payload: dict[str, Any]
    ) -> dict[str, Any]:
        """Add contacts to a group."""
        data = await self._request("PUT", f"/groups/{group_id}/contacts", json=payload)
        return dict(data)

    async def remove_group_contacts(
        self, group_id: str, payload: dict[str, Any]
    ) -> dict[str, Any]:
        """Remove contacts from a group."""
        data = await self._request("POST", f"/groups/{group_id}/contacts", json=payload)
        return dict(data)

    async def get_group_contact_counts(self) -> list[dict[str, Any]]:
        """Fetch per-group contact counts."""
        data = await self._request("GET", "/groups/contact-counts")
        counts = data.get("counts")
        if isinstance(counts, list):
            return counts
        return []

    # =========================================================================
    # Custom Fields API
    # =========================================================================

    async def get_custom_fields(self) -> list[dict[str, Any]]:
        """Fetch custom field definitions for the authenticated user."""
        data = await self._request_with_fallback(
            "GET",
            [
                "/custom-fields",
                "/v1/custom-fields",
            ],
        )
        if not isinstance(data, dict):
            return []
        payload = data.get("data")
        if isinstance(payload, dict):
            custom_fields = payload.get("custom_fields", [])
        else:
            custom_fields = data.get("custom_fields", [])
        if not isinstance(custom_fields, list):
            return []
        return custom_fields

    async def create_custom_field(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Create a custom field."""
        data = await self._request_with_fallback(
            "POST",
            [
                "/custom-fields",
                "/v1/custom-fields",
            ],
            json=payload,
        )
        return dict(data)

    async def update_custom_field(
        self, custom_field_id: str, payload: dict[str, Any]
    ) -> dict[str, Any]:
        """Update a custom field."""
        data = await self._request_with_fallback(
            "PUT",
            [
                f"/custom-fields/{custom_field_id}",
                f"/v1/custom-fields/{custom_field_id}",
            ],
            json=payload,
        )
        return dict(data)

    async def delete_custom_field(self, custom_field_id: str) -> dict[str, Any]:
        """Delete a custom field."""
        data = await self._request_with_fallback(
            "DELETE",
            [
                f"/custom-fields/{custom_field_id}",
                f"/v1/custom-fields/{custom_field_id}",
            ],
        )
        return dict(data)

    async def reorder_custom_fields(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Reorder custom fields."""
        data = await self._request_with_fallback(
            "PUT",
            [
                "/custom-fields/reorder",
                "/v1/custom-fields/reorder",
            ],
            json=payload,
        )
        return dict(data)

    async def batch_update_custom_fields_contacts(
        self, payload: dict[str, Any]
    ) -> dict[str, Any]:
        """Batch update custom field values for contacts."""
        data = await self._request_with_fallback(
            "POST",
            [
                "/custom-fields/batch-update-contacts",
                "/v1/custom-fields/batch-update-contacts",
            ],
            json=payload,
        )
        return dict(data)

    async def create_note(self, note: NoteCreate) -> dict[str, Any]:
        """Create a new note (timeline item).

        Args:
            note: Note data. Use NoteCreate.with_contacts()
                to link to specific contacts.

        Returns:
            The created note data including server-assigned ID.
        """
        data = await self._request_with_fallback(
            "POST",
            [
                "/timeline",
                "/timeline_items",
            ],
            json={"timeline_event": note.model_dump(exclude_none=True, mode="json")},
        )
        return dict(extract_note_entity(data))

    async def search_groups(
        self, params: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        """Search groups."""
        data = await self._request("GET", "/search/groups", params=params or {})
        candidates = data.get("groups")
        if isinstance(candidates, list):
            return candidates
        return []

    async def search_timeline(
        self, params: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        """Search timeline notes."""
        data = await self._request("GET", "/search/timeline", params=params or {})
        candidates = data.get("timeline")
        if isinstance(candidates, list):
            return candidates
        candidates = data.get("timeline_items")
        if isinstance(candidates, list):
            return candidates
        return []

    async def search_reminders(
        self, params: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        """Search reminders."""
        data = await self._request("GET", "/search/reminders", params=params or {})
        candidates = data.get("reminders")
        if isinstance(candidates, list):
            return candidates
        return []

    async def search_tags(
        self, params: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        """Search tags."""
        data = await self._request("GET", "/search/tags", params=params or {})
        candidates = data.get("tags")
        if isinstance(candidates, list):
            return candidates
        return []

    async def search_views(
        self, params: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        """Search views."""
        data = await self._request("GET", "/search/views", params=params or {})
        candidates = data.get("views")
        if isinstance(candidates, list):
            return candidates
        return []

    async def get_tags(self) -> list[dict[str, Any]]:
        """Fetch tags."""
        data = await self._request("GET", "/tags")
        tags = data.get("tags")
        if isinstance(tags, list):
            return tags
        return []

    async def get_tag(self, tag_id: str) -> dict[str, Any]:
        """Fetch a single tag."""
        data = await self._request("GET", f"/tags/{tag_id}")
        return dict(data)

    async def create_tag(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Create a tag."""
        data = await self._request("POST", "/tags", json=payload)
        return dict(data)

    async def update_tag(self, tag_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Update a tag."""
        data = await self._request("PUT", f"/tags/{tag_id}", json=payload)
        return dict(data)

    async def delete_tag(self, tag_id: str) -> dict[str, Any]:
        """Delete a tag."""
        data = await self._request("DELETE", f"/tags/{tag_id}")
        return dict(data)

    async def count_tags(self) -> int:
        """Get total number of tags."""
        data = await self._request("GET", "/tags/count")
        if isinstance(data, int):
            return data
        if isinstance(data, dict):
            count = data.get("count")
            if isinstance(count, int):
                return count
        return 0

    async def get_tag_contact_counts(self) -> list[dict[str, Any]]:
        """Fetch per-tag contact counts."""
        data = await self._request("GET", "/tags/contact-counts")
        counts = data.get("counts")
        if isinstance(counts, list):
            return counts
        return []

    async def update_note(self, update: NoteUpdate) -> dict[str, Any]:
        """Update an existing note.

        Args:
            update: Update specification with note_id and changes.

        Returns:
            The updated note data.
        """
        data = await self._request_with_fallback(
            "PUT",
            [
                f"/timeline/{update.note_id}",
                f"/timeline_items/{update.note_id}",
            ],
            json=update.model_dump(exclude_none=True, mode="json"),
        )
        return dict(extract_note_entity(data))

    async def delete_note(self, note_id: str) -> dict[str, Any]:
        """Delete a note by ID.

        Args:
            note_id: The unique note identifier.

        Returns:
            The deleted note data.
        """
        data = await self._request_with_fallback(
            "DELETE",
            [
                f"/timeline/{note_id}",
                f"/timeline_items/{note_id}",
            ],
        )
        return dict(extract_note_entity(data))

    async def get_current_user(self) -> dict[str, Any]:
        """Fetch current user."""
        data = await self._request("GET", "/users/me")
        return dict(data)

    # =========================================================================
    # Client Lifecycle
    # =========================================================================

    async def close(self) -> None:
        """Close the underlying async HTTP client and release resources."""
        await self._client.aclose()

    async def __aenter__(self) -> Self:
        """Enter async context manager (returns self)."""
        return self

    async def __aexit__(self, *args: object) -> None:
        """Exit async context manager (closes client)."""
        await self.close()
