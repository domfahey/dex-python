"""Async Dex API client."""

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
    ReminderCreate,
    ReminderUpdate,
)


class AsyncDexClient:
    """Async client for the Dex CRM API."""

    def __init__(self, settings: Settings | None = None) -> None:
        """Initialize the async client with settings."""
        self.settings = settings if settings is not None else Settings()  # type: ignore[call-arg]
        self._client = httpx.AsyncClient(
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

    async def _request(
        self, method: str, endpoint: str, **kwargs: Any
    ) -> dict[str, Any]:
        """Make an async API request."""
        response = await self._client.request(method, endpoint, **kwargs)
        if response.status_code >= 400:
            self._handle_error(response, endpoint)
        result: dict[str, Any] = response.json()
        return result

    # =========================================================================
    # Contacts API
    # =========================================================================

    async def get_contacts(
        self, limit: int = 100, offset: int = 0
    ) -> list[dict[str, Any]]:
        """Fetch paginated list of contacts."""
        endpoint = "/contacts"
        response = await self._client.request(
            "GET",
            endpoint,
            params={"limit": limit, "offset": offset},
        )
        if response.status_code >= 400:
            self._handle_error(response, endpoint)
        data: dict[str, Any] = response.json()
        result: list[dict[str, Any]] = data.get("contacts", [])
        return result

    async def get_contact(self, contact_id: str) -> dict[str, Any]:
        """Fetch a single contact by ID."""
        data = await self._request("GET", f"/contacts/{contact_id}")
        contacts = data.get("contacts", [])
        if contacts:
            result: dict[str, Any] = contacts[0]
            return result
        return {}

    async def get_contact_by_email(self, email: str) -> dict[str, Any] | None:
        """Fetch a contact by email address."""
        data = await self._request("GET", "/search/contacts", params={"email": email})
        contacts = data.get("search_contacts_by_exact_email", [])
        if contacts:
            result: dict[str, Any] = contacts[0]
            return result
        return None

    async def create_contact(self, contact: ContactCreate) -> dict[str, Any]:
        """Create a new contact."""
        return await self._request(
            "POST",
            "/contacts",
            json={"contact": contact.model_dump(exclude_none=True)},
        )

    async def update_contact(self, update: ContactUpdate) -> dict[str, Any]:
        """Update an existing contact."""
        return await self._request(
            "PUT",
            f"/contacts/{update.contact_id}",
            json=update.model_dump(exclude_none=True, by_alias=True),
        )

    async def delete_contact(self, contact_id: str) -> dict[str, Any]:
        """Delete a contact by ID."""
        return await self._request("DELETE", f"/contacts/{contact_id}")

    # =========================================================================
    # Reminders API
    # =========================================================================

    async def get_reminders(
        self, limit: int = 100, offset: int = 0
    ) -> list[dict[str, Any]]:
        """Fetch paginated list of reminders."""
        data = await self._request(
            "GET",
            "/reminders",
            params={"limit": limit, "offset": offset},
        )
        result: list[dict[str, Any]] = data.get("reminders", [])
        return result

    async def create_reminder(self, reminder: ReminderCreate) -> dict[str, Any]:
        """Create a new reminder."""
        return await self._request(
            "POST",
            "/reminders",
            json={"reminder": reminder.model_dump(exclude_none=True)},
        )

    async def update_reminder(self, update: ReminderUpdate) -> dict[str, Any]:
        """Update an existing reminder."""
        return await self._request(
            "PUT",
            f"/reminders/{update.reminder_id}",
            json=update.model_dump(exclude_none=True),
        )

    async def delete_reminder(self, reminder_id: str) -> dict[str, Any]:
        """Delete a reminder by ID."""
        return await self._request("DELETE", f"/reminders/{reminder_id}")

    # =========================================================================
    # Notes (Timeline Items) API
    # =========================================================================

    async def get_notes(
        self, limit: int = 100, offset: int = 0
    ) -> list[dict[str, Any]]:
        """Fetch paginated list of notes."""
        data = await self._request(
            "GET",
            "/timeline_items",
            params={"limit": limit, "offset": offset},
        )
        result: list[dict[str, Any]] = data.get("timeline_items", [])
        return result

    async def get_notes_by_contact(self, contact_id: str) -> list[dict[str, Any]]:
        """Fetch notes for a specific contact."""
        data = await self._request("GET", f"/timeline_items/contacts/{contact_id}")
        result: list[dict[str, Any]] = data.get("timeline_items", [])
        return result

    async def create_note(self, note: NoteCreate) -> dict[str, Any]:
        """Create a new note."""
        return await self._request(
            "POST",
            "/timeline_items",
            json={"timeline_event": note.model_dump(exclude_none=True)},
        )

    async def update_note(self, update: NoteUpdate) -> dict[str, Any]:
        """Update an existing note."""
        return await self._request(
            "PUT",
            f"/timeline_items/{update.note_id}",
            json=update.model_dump(exclude_none=True),
        )

    async def delete_note(self, note_id: str) -> dict[str, Any]:
        """Delete a note by ID."""
        return await self._request("DELETE", f"/timeline_items/{note_id}")

    # =========================================================================
    # Client Management
    # =========================================================================

    async def close(self) -> None:
        """Close the HTTP client."""
        await self._client.aclose()

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, *args: object) -> None:
        await self.close()
