"""Dex API client."""

from typing import Any, Self

import httpx

from .config import Settings
from .models import (
    ContactCreate,
    ContactUpdate,
    NoteCreate,
    NoteUpdate,
    ReminderCreate,
    ReminderUpdate,
)


class DexClient:
    """Client for the Dex CRM API."""

    def __init__(self, settings: Settings | None = None) -> None:
        """Initialize the client with settings."""
        self.settings = settings if settings is not None else Settings()  # type: ignore[call-arg]
        self._client = httpx.Client(
            base_url=self.settings.dex_base_url,
            headers={
                "Content-Type": "application/json",
                "x-hasura-dex-api-key": self.settings.dex_api_key,
            },
            timeout=30.0,
        )

    def _request(self, method: str, endpoint: str, **kwargs: Any) -> dict[str, Any]:
        """Make an API request."""
        response = self._client.request(method, endpoint, **kwargs)
        response.raise_for_status()
        result: dict[str, Any] = response.json()
        return result

    # =========================================================================
    # Contacts API
    # =========================================================================

    def get_contacts(self, limit: int = 100, offset: int = 0) -> list[dict[str, Any]]:
        """Fetch paginated list of contacts."""
        response = self._client.request(
            "GET",
            "/contacts",
            params={"limit": limit, "offset": offset},
        )
        response.raise_for_status()
        data: dict[str, Any] = response.json()
        result: list[dict[str, Any]] = data.get("contacts", [])
        return result

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
        return self._request(
            "POST",
            "/contacts",
            json={"contact": contact.model_dump(exclude_none=True)},
        )

    def update_contact(self, update: ContactUpdate) -> dict[str, Any]:
        """Update an existing contact."""
        return self._request(
            "PUT",
            f"/contacts/{update.contact_id}",
            json=update.model_dump(exclude_none=True, by_alias=True),
        )

    def delete_contact(self, contact_id: str) -> dict[str, Any]:
        """Delete a contact by ID."""
        return self._request("DELETE", f"/contacts/{contact_id}")

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

    def create_reminder(self, reminder: ReminderCreate) -> dict[str, Any]:
        """Create a new reminder."""
        return self._request(
            "POST",
            "/reminders",
            json={"reminder": reminder.model_dump(exclude_none=True)},
        )

    def update_reminder(self, update: ReminderUpdate) -> dict[str, Any]:
        """Update an existing reminder."""
        return self._request(
            "PUT",
            f"/reminders/{update.reminder_id}",
            json=update.model_dump(exclude_none=True),
        )

    def delete_reminder(self, reminder_id: str) -> dict[str, Any]:
        """Delete a reminder by ID."""
        return self._request("DELETE", f"/reminders/{reminder_id}")

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

    def get_notes_by_contact(self, contact_id: str) -> list[dict[str, Any]]:
        """Fetch notes for a specific contact."""
        data = self._request("GET", f"/timeline_items/contacts/{contact_id}")
        result: list[dict[str, Any]] = data.get("timeline_items", [])
        return result

    def create_note(self, note: NoteCreate) -> dict[str, Any]:
        """Create a new note."""
        return self._request(
            "POST",
            "/timeline_items",
            json={"timeline_event": note.model_dump(exclude_none=True)},
        )

    def update_note(self, update: NoteUpdate) -> dict[str, Any]:
        """Update an existing note."""
        return self._request(
            "PUT",
            f"/timeline_items/{update.note_id}",
            json=update.model_dump(exclude_none=True),
        )

    def delete_note(self, note_id: str) -> dict[str, Any]:
        """Delete a note by ID."""
        return self._request("DELETE", f"/timeline_items/{note_id}")

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
