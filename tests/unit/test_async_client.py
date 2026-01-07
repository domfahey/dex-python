"""Comprehensive tests for AsyncDexClient CRUD operations.

This module mirrors the sync client tests to ensure feature parity
between DexClient and AsyncDexClient.
"""

from __future__ import annotations

import json

import pytest
from pytest_httpx import HTTPXMock

from dex_python import (
    ContactCreate,
    ContactUpdate,
    NoteCreate,
    NoteUpdate,
    ReminderCreate,
    ReminderUpdate,
    Settings,
)
from dex_python.async_client import AsyncDexClient
from dex_python.exceptions import (
    AuthenticationError,
    ContactNotFoundError,
    DexAPIError,
    NoteNotFoundError,
    RateLimitError,
    ReminderNotFoundError,
    ValidationError,
)

pytestmark = pytest.mark.asyncio


class TestAsyncClientContacts:
    """Test AsyncDexClient contact operations."""

    async def test_get_contacts(
        self, settings: Settings, httpx_mock: HTTPXMock
    ) -> None:
        """Test fetching contacts list."""
        mock_response = {
            "contacts": [
                {"id": "1", "first_name": "John", "last_name": "Doe"},
                {"id": "2", "first_name": "Jane", "last_name": "Smith"},
            ],
            "pagination": {"total": {"count": 2}},
        }
        httpx_mock.add_response(
            url="https://api.getdex.com/api/rest/contacts?limit=100&offset=0",
            json=mock_response,
        )

        async with AsyncDexClient(settings) as client:
            contacts = await client.get_contacts()

        assert len(contacts) == 2
        assert contacts[0]["first_name"] == "John"

    async def test_get_contacts_with_pagination(
        self, settings: Settings, httpx_mock: HTTPXMock
    ) -> None:
        """Test fetching contacts with custom pagination."""
        httpx_mock.add_response(
            url="https://api.getdex.com/api/rest/contacts?limit=50&offset=100",
            json={"contacts": [{"id": "101"}], "pagination": {"total": {"count": 150}}},
        )

        async with AsyncDexClient(settings) as client:
            contacts = await client.get_contacts(limit=50, offset=100)

        assert len(contacts) == 1
        assert contacts[0]["id"] == "101"

    async def test_get_contacts_paginated(
        self, settings: Settings, httpx_mock: HTTPXMock
    ) -> None:
        """Test get_contacts_paginated returns PaginatedContacts."""
        httpx_mock.add_response(
            url="https://api.getdex.com/api/rest/contacts?limit=10&offset=0",
            json={
                "contacts": [{"id": "1"}],
                "pagination": {"total": {"count": 100}},
            },
        )

        async with AsyncDexClient(settings) as client:
            result = await client.get_contacts_paginated(limit=10, offset=0)

        assert result.total == 100
        assert result.has_more is True
        assert len(result.contacts) == 1

    async def test_get_contact_by_id(
        self, settings: Settings, httpx_mock: HTTPXMock
    ) -> None:
        """Test fetching single contact by ID."""
        httpx_mock.add_response(
            url="https://api.getdex.com/api/rest/contacts/abc123",
            json={
                "contacts": [
                    {
                        "id": "abc123",
                        "first_name": "John",
                        "emails": [{"email": "john@example.com"}],
                    }
                ]
            },
        )

        async with AsyncDexClient(settings) as client:
            contact = await client.get_contact("abc123")

        assert contact["id"] == "abc123"
        assert contact["first_name"] == "John"

    async def test_get_contact_empty_response(
        self, settings: Settings, httpx_mock: HTTPXMock
    ) -> None:
        """Test get_contact returns empty dict when no contacts found."""
        httpx_mock.add_response(
            url="https://api.getdex.com/api/rest/contacts/nonexistent",
            json={"contacts": []},
        )

        async with AsyncDexClient(settings) as client:
            contact = await client.get_contact("nonexistent")

        assert contact == {}

    async def test_get_contact_by_email(
        self, settings: Settings, httpx_mock: HTTPXMock
    ) -> None:
        """Test looking up contact by email."""
        httpx_mock.add_response(
            url="https://api.getdex.com/api/rest/search/contacts?email=jane%40example.com",
            json={
                "search_contacts_by_exact_email": [
                    {"id": "456", "first_name": "Jane"}
                ]
            },
        )

        async with AsyncDexClient(settings) as client:
            contact = await client.get_contact_by_email("jane@example.com")

        assert contact is not None
        assert contact["id"] == "456"

    async def test_get_contact_by_email_not_found(
        self, settings: Settings, httpx_mock: HTTPXMock
    ) -> None:
        """Test get_contact_by_email returns None when not found."""
        httpx_mock.add_response(
            url="https://api.getdex.com/api/rest/search/contacts?email=nobody%40example.com",
            json={"search_contacts_by_exact_email": []},
        )

        async with AsyncDexClient(settings) as client:
            contact = await client.get_contact_by_email("nobody@example.com")

        assert contact is None

    async def test_create_contact(
        self, settings: Settings, httpx_mock: HTTPXMock
    ) -> None:
        """Test creating a new contact."""
        httpx_mock.add_response(
            url="https://api.getdex.com/api/rest/contacts",
            method="POST",
            json={
                "insert_contacts_one": {
                    "id": "new-123",
                    "first_name": "Alice",
                    "last_name": "Wonder",
                }
            },
        )

        async with AsyncDexClient(settings) as client:
            result = await client.create_contact(
                ContactCreate(first_name="Alice", last_name="Wonder")
            )

        assert result["id"] == "new-123"
        assert result["first_name"] == "Alice"

    async def test_create_contact_with_email(
        self, settings: Settings, httpx_mock: HTTPXMock
    ) -> None:
        """Test creating contact with email using factory method."""
        httpx_mock.add_response(
            url="https://api.getdex.com/api/rest/contacts",
            method="POST",
            json={"insert_contacts_one": {"id": "789", "first_name": "Bob"}},
        )

        async with AsyncDexClient(settings) as client:
            contact = ContactCreate.with_email(
                "bob@example.com", first_name="Bob", last_name="Builder"
            )
            result = await client.create_contact(contact)

        request = httpx_mock.get_requests()[0]
        body = json.loads(request.content)
        assert body["contact"]["contact_emails"] == {"data": {"email": "bob@example.com"}}

    async def test_update_contact(
        self, settings: Settings, httpx_mock: HTTPXMock
    ) -> None:
        """Test updating an existing contact."""
        httpx_mock.add_response(
            url="https://api.getdex.com/api/rest/contacts/contact-123",
            method="PUT",
            json={"update_contacts_by_pk": {"id": "contact-123", "first_name": "Updated"}},
        )

        async with AsyncDexClient(settings) as client:
            update = ContactUpdate(
                contact_id="contact-123", changes={"first_name": "Updated"}
            )
            result = await client.update_contact(update)

        assert result["id"] == "contact-123"
        request = httpx_mock.get_requests()[0]
        assert request.method == "PUT"

    async def test_delete_contact(
        self, settings: Settings, httpx_mock: HTTPXMock
    ) -> None:
        """Test deleting a contact."""
        httpx_mock.add_response(
            url="https://api.getdex.com/api/rest/contacts/del-123",
            method="DELETE",
            json={"delete_contacts_by_pk": {"id": "del-123"}},
        )

        async with AsyncDexClient(settings) as client:
            result = await client.delete_contact("del-123")

        assert result["id"] == "del-123"
        request = httpx_mock.get_requests()[0]
        assert request.method == "DELETE"


class TestAsyncClientReminders:
    """Test AsyncDexClient reminder operations."""

    async def test_get_reminders(
        self, settings: Settings, httpx_mock: HTTPXMock
    ) -> None:
        """Test fetching reminders list."""
        httpx_mock.add_response(
            url="https://api.getdex.com/api/rest/reminders?limit=100&offset=0",
            json={
                "reminders": [
                    {"id": "rem-1", "body": "Call John"},
                    {"id": "rem-2", "body": "Email Jane"},
                ]
            },
        )

        async with AsyncDexClient(settings) as client:
            reminders = await client.get_reminders()

        assert len(reminders) == 2
        assert reminders[0]["body"] == "Call John"

    async def test_get_reminders_paginated(
        self, settings: Settings, httpx_mock: HTTPXMock
    ) -> None:
        """Test get_reminders_paginated returns PaginatedReminders."""
        httpx_mock.add_response(
            url="https://api.getdex.com/api/rest/reminders?limit=10&offset=0",
            json={
                "reminders": [{"id": "rem-1"}],
                "total": {"aggregate": {"count": 50}},
            },
        )

        async with AsyncDexClient(settings) as client:
            result = await client.get_reminders_paginated(limit=10, offset=0)

        assert result.total == 50
        assert result.has_more is True

    async def test_create_reminder(
        self, settings: Settings, httpx_mock: HTTPXMock
    ) -> None:
        """Test creating a new reminder."""
        httpx_mock.add_response(
            url="https://api.getdex.com/api/rest/reminders",
            method="POST",
            json={"insert_reminders_one": {"id": "new-rem", "body": "Follow up"}},
        )

        async with AsyncDexClient(settings) as client:
            reminder = ReminderCreate(text="Follow up")
            result = await client.create_reminder(reminder)

        assert result["id"] == "new-rem"

    async def test_create_reminder_with_contacts(
        self, settings: Settings, httpx_mock: HTTPXMock
    ) -> None:
        """Test creating reminder linked to contacts."""
        httpx_mock.add_response(
            url="https://api.getdex.com/api/rest/reminders",
            method="POST",
            json={"insert_reminders_one": {"id": "rem-linked"}},
        )

        async with AsyncDexClient(settings) as client:
            reminder = ReminderCreate.with_contacts(
                text="Team meeting",
                contact_ids=["c1", "c2"],
                due_at_date="2025-01-20",
            )
            result = await client.create_reminder(reminder)

        request = httpx_mock.get_requests()[0]
        body = json.loads(request.content)
        assert len(body["reminder"]["reminders_contacts"]["data"]) == 2

    async def test_update_reminder(
        self, settings: Settings, httpx_mock: HTTPXMock
    ) -> None:
        """Test updating an existing reminder."""
        httpx_mock.add_response(
            url="https://api.getdex.com/api/rest/reminders/rem-123",
            method="PUT",
            json={"update_reminders_by_pk": {"id": "rem-123"}},
        )

        async with AsyncDexClient(settings) as client:
            update = ReminderUpdate(reminder_id="rem-123", changes={"text": "Updated"})
            result = await client.update_reminder(update)

        assert result["id"] == "rem-123"

    async def test_update_reminder_mark_complete(
        self, settings: Settings, httpx_mock: HTTPXMock
    ) -> None:
        """Test marking reminder as complete using factory method."""
        httpx_mock.add_response(
            url="https://api.getdex.com/api/rest/reminders/rem-456",
            method="PUT",
            json={"update_reminders_by_pk": {"id": "rem-456", "is_complete": True}},
        )

        async with AsyncDexClient(settings) as client:
            update = ReminderUpdate.mark_complete("rem-456")
            result = await client.update_reminder(update)

        request = httpx_mock.get_requests()[0]
        body = json.loads(request.content)
        assert body["changes"]["is_complete"] is True

    async def test_delete_reminder(
        self, settings: Settings, httpx_mock: HTTPXMock
    ) -> None:
        """Test deleting a reminder."""
        httpx_mock.add_response(
            url="https://api.getdex.com/api/rest/reminders/rem-del",
            method="DELETE",
            json={"delete_reminders_by_pk": {"id": "rem-del"}},
        )

        async with AsyncDexClient(settings) as client:
            result = await client.delete_reminder("rem-del")

        assert result["id"] == "rem-del"


class TestAsyncClientNotes:
    """Test AsyncDexClient note operations."""

    async def test_get_notes(
        self, settings: Settings, httpx_mock: HTTPXMock
    ) -> None:
        """Test fetching notes list."""
        httpx_mock.add_response(
            url="https://api.getdex.com/api/rest/timeline_items?limit=100&offset=0",
            json={
                "timeline_items": [
                    {"id": "note-1", "note": "Meeting notes"},
                    {"id": "note-2", "note": "Follow up"},
                ]
            },
        )

        async with AsyncDexClient(settings) as client:
            notes = await client.get_notes()

        assert len(notes) == 2
        assert notes[0]["note"] == "Meeting notes"

    async def test_get_notes_paginated(
        self, settings: Settings, httpx_mock: HTTPXMock
    ) -> None:
        """Test get_notes_paginated returns PaginatedNotes."""
        httpx_mock.add_response(
            url="https://api.getdex.com/api/rest/timeline_items?limit=10&offset=0",
            json={
                "timeline_items": [{"id": "note-1"}],
                "pagination": {"total": {"count": 25}},
            },
        )

        async with AsyncDexClient(settings) as client:
            result = await client.get_notes_paginated(limit=10, offset=0)

        assert result.total == 25
        assert result.has_more is True

    async def test_get_notes_by_contact(
        self, settings: Settings, httpx_mock: HTTPXMock
    ) -> None:
        """Test fetching notes for a specific contact."""
        httpx_mock.add_response(
            url="https://api.getdex.com/api/rest/timeline_items/contacts/contact-abc",
            json={
                "timeline_items": [
                    {"id": "note-1", "note": "First meeting"},
                    {"id": "note-2", "note": "Second meeting"},
                ]
            },
        )

        async with AsyncDexClient(settings) as client:
            notes = await client.get_notes_by_contact("contact-abc")

        assert len(notes) == 2

    async def test_create_note(
        self, settings: Settings, httpx_mock: HTTPXMock
    ) -> None:
        """Test creating a new note."""
        httpx_mock.add_response(
            url="https://api.getdex.com/api/rest/timeline_items",
            method="POST",
            json={"insert_timeline_items_one": {"id": "new-note", "note": "Test note"}},
        )

        async with AsyncDexClient(settings) as client:
            note = NoteCreate(note="Test note")
            result = await client.create_note(note)

        assert result["id"] == "new-note"

    async def test_create_note_with_contacts(
        self, settings: Settings, httpx_mock: HTTPXMock
    ) -> None:
        """Test creating note linked to contacts."""
        httpx_mock.add_response(
            url="https://api.getdex.com/api/rest/timeline_items",
            method="POST",
            json={"insert_timeline_items_one": {"id": "note-linked"}},
        )

        async with AsyncDexClient(settings) as client:
            note = NoteCreate.with_contacts(
                note="Conference discussion",
                contact_ids=["c1", "c2", "c3"],
            )
            result = await client.create_note(note)

        request = httpx_mock.get_requests()[0]
        body = json.loads(request.content)
        assert len(body["timeline_event"]["timeline_items_contacts"]["data"]) == 3

    async def test_update_note(
        self, settings: Settings, httpx_mock: HTTPXMock
    ) -> None:
        """Test updating an existing note."""
        httpx_mock.add_response(
            url="https://api.getdex.com/api/rest/timeline_items/note-123",
            method="PUT",
            json={"update_timeline_items_by_pk": {"id": "note-123"}},
        )

        async with AsyncDexClient(settings) as client:
            update = NoteUpdate(note_id="note-123", changes={"note": "Updated note"})
            result = await client.update_note(update)

        assert result["id"] == "note-123"

    async def test_delete_note(
        self, settings: Settings, httpx_mock: HTTPXMock
    ) -> None:
        """Test deleting a note."""
        httpx_mock.add_response(
            url="https://api.getdex.com/api/rest/timeline_items/note-del",
            method="DELETE",
            json={"delete_timeline_items_by_pk": {"id": "note-del"}},
        )

        async with AsyncDexClient(settings) as client:
            result = await client.delete_note("note-del")

        assert result["id"] == "note-del"


class TestAsyncClientErrors:
    """Test AsyncDexClient error handling."""

    async def test_401_raises_authentication_error(
        self, settings: Settings, httpx_mock: HTTPXMock
    ) -> None:
        """Test 401 response raises AuthenticationError."""
        httpx_mock.add_response(
            url="https://api.getdex.com/api/rest/contacts?limit=100&offset=0",
            status_code=401,
            json={"error": "Invalid API key"},
        )

        async with AsyncDexClient(settings) as client:
            with pytest.raises(AuthenticationError) as exc_info:
                await client.get_contacts()

        assert exc_info.value.status_code == 401

    async def test_400_raises_validation_error(
        self, settings: Settings, httpx_mock: HTTPXMock
    ) -> None:
        """Test 400 response raises ValidationError."""
        httpx_mock.add_response(
            url="https://api.getdex.com/api/rest/contacts",
            method="POST",
            status_code=400,
            json={"error": "Invalid request body"},
        )

        async with AsyncDexClient(settings) as client:
            with pytest.raises(ValidationError) as exc_info:
                await client.create_contact(ContactCreate(first_name="Test"))

        assert exc_info.value.status_code == 400

    async def test_429_raises_rate_limit_error(
        self, settings: Settings, httpx_mock: HTTPXMock
    ) -> None:
        """Test 429 response raises RateLimitError."""
        httpx_mock.add_response(
            url="https://api.getdex.com/api/rest/contacts?limit=100&offset=0",
            status_code=429,
            headers={"Retry-After": "60"},
            json={"error": "Rate limit exceeded"},
        )

        async with AsyncDexClient(settings) as client:
            with pytest.raises(RateLimitError) as exc_info:
                await client.get_contacts()

        assert exc_info.value.retry_after == 60

    async def test_404_contact_raises_contact_not_found(
        self, settings: Settings, httpx_mock: HTTPXMock
    ) -> None:
        """Test 404 on contact endpoint raises ContactNotFoundError."""
        httpx_mock.add_response(
            url="https://api.getdex.com/api/rest/contacts/invalid-id",
            status_code=404,
            json={"error": "Not found"},
        )

        async with AsyncDexClient(settings) as client:
            with pytest.raises(ContactNotFoundError) as exc_info:
                await client.get_contact("invalid-id")

        assert exc_info.value.contact_id == "invalid-id"

    async def test_404_reminder_raises_reminder_not_found(
        self, settings: Settings, httpx_mock: HTTPXMock
    ) -> None:
        """Test 404 on reminder endpoint raises ReminderNotFoundError."""
        httpx_mock.add_response(
            url="https://api.getdex.com/api/rest/reminders/bad-rem",
            method="DELETE",
            status_code=404,
            json={"error": "Not found"},
        )

        async with AsyncDexClient(settings) as client:
            with pytest.raises(ReminderNotFoundError) as exc_info:
                await client.delete_reminder("bad-rem")

        assert exc_info.value.reminder_id == "bad-rem"

    async def test_404_note_raises_note_not_found(
        self, settings: Settings, httpx_mock: HTTPXMock
    ) -> None:
        """Test 404 on timeline_items endpoint raises NoteNotFoundError."""
        httpx_mock.add_response(
            url="https://api.getdex.com/api/rest/timeline_items/bad-note",
            method="DELETE",
            status_code=404,
            json={"error": "Not found"},
        )

        async with AsyncDexClient(settings) as client:
            with pytest.raises(NoteNotFoundError) as exc_info:
                await client.delete_note("bad-note")

        assert exc_info.value.note_id == "bad-note"

    async def test_500_raises_dex_api_error(
        self, settings: Settings, httpx_mock: HTTPXMock
    ) -> None:
        """Test 500 response raises DexAPIError."""
        httpx_mock.add_response(
            url="https://api.getdex.com/api/rest/contacts?limit=100&offset=0",
            status_code=500,
            json={"error": "Internal server error"},
        )

        async with AsyncDexClient(settings) as client:
            with pytest.raises(DexAPIError) as exc_info:
                await client.get_contacts()

        assert exc_info.value.status_code == 500

    async def test_error_with_malformed_json(
        self, settings: Settings, httpx_mock: HTTPXMock
    ) -> None:
        """Test error handling when response has invalid JSON."""
        httpx_mock.add_response(
            url="https://api.getdex.com/api/rest/contacts?limit=100&offset=0",
            status_code=500,
            content=b"Internal Server Error",
        )

        async with AsyncDexClient(settings) as client:
            with pytest.raises(DexAPIError):
                await client.get_contacts()


class TestAsyncClientLifecycle:
    """Test AsyncDexClient lifecycle and context manager."""

    async def test_context_manager_closes_client(self, settings: Settings) -> None:
        """Test that context manager properly closes the client."""
        async with AsyncDexClient(settings) as client:
            client_ref = client
        assert client_ref._client.is_closed

    async def test_manual_close(self, settings: Settings) -> None:
        """Test manual close method."""
        client = AsyncDexClient(settings)
        assert not client._client.is_closed
        await client.close()
        assert client._client.is_closed

    async def test_client_headers(self, settings: Settings) -> None:
        """Test client has correct headers."""
        async with AsyncDexClient(settings) as client:
            headers = client._client.headers
            assert headers["content-type"] == "application/json"
            assert headers["x-hasura-dex-api-key"] == "test-api-key"


class TestAsyncClientRetry:
    """Test AsyncDexClient retry behavior."""

    async def test_retry_on_503(
        self, settings: Settings, httpx_mock: HTTPXMock, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test retry on 503 Service Unavailable."""
        delays: list[float] = []

        async def fake_sleep(delay: float) -> None:
            delays.append(delay)

        monkeypatch.setattr("dex_python.async_client.asyncio.sleep", fake_sleep)

        httpx_mock.add_response(
            url="https://api.getdex.com/api/rest/contacts?limit=100&offset=0",
            status_code=503,
        )
        httpx_mock.add_response(
            url="https://api.getdex.com/api/rest/contacts?limit=100&offset=0",
            json={"contacts": [{"id": "1"}]},
        )

        async with AsyncDexClient(settings, max_retries=2, retry_delay=0.01) as client:
            contacts = await client.get_contacts()

        assert len(contacts) == 1
        assert delays == [0.01]
        assert len(httpx_mock.get_requests()) == 2

    async def test_exponential_backoff(
        self, settings: Settings, httpx_mock: HTTPXMock, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test exponential backoff doubles delay each retry."""
        delays: list[float] = []

        async def fake_sleep(delay: float) -> None:
            delays.append(delay)

        monkeypatch.setattr("dex_python.async_client.asyncio.sleep", fake_sleep)

        # Add 3 failures then success
        for _ in range(3):
            httpx_mock.add_response(
                url="https://api.getdex.com/api/rest/contacts?limit=100&offset=0",
                status_code=503,
            )
        httpx_mock.add_response(
            url="https://api.getdex.com/api/rest/contacts?limit=100&offset=0",
            json={"contacts": []},
        )

        async with AsyncDexClient(settings, max_retries=3, retry_delay=1.0) as client:
            await client.get_contacts()

        # Delays should be: 1.0, 2.0, 4.0 (exponential backoff)
        assert delays == [1.0, 2.0, 4.0]

    async def test_max_retries_exceeded(
        self, settings: Settings, httpx_mock: HTTPXMock, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test error is raised after max retries exceeded."""
        delays: list[float] = []

        async def fake_sleep(delay: float) -> None:
            delays.append(delay)

        monkeypatch.setattr("dex_python.async_client.asyncio.sleep", fake_sleep)

        for _ in range(3):
            httpx_mock.add_response(
                url="https://api.getdex.com/api/rest/contacts?limit=100&offset=0",
                status_code=503,
            )

        async with AsyncDexClient(settings, max_retries=2, retry_delay=0.01) as client:
            with pytest.raises(DexAPIError):
                await client.get_contacts()

        assert len(delays) == 2
        assert len(httpx_mock.get_requests()) == 3

    async def test_no_retry_on_400(
        self, settings: Settings, httpx_mock: HTTPXMock, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test 400 errors are not retried."""
        delays: list[float] = []

        async def fake_sleep(delay: float) -> None:
            delays.append(delay)

        monkeypatch.setattr("dex_python.async_client.asyncio.sleep", fake_sleep)

        httpx_mock.add_response(
            url="https://api.getdex.com/api/rest/contacts",
            method="POST",
            status_code=400,
            json={"error": "Bad request"},
        )

        async with AsyncDexClient(settings, max_retries=3, retry_delay=0.01) as client:
            with pytest.raises(ValidationError):
                await client.create_contact(ContactCreate(first_name="Test"))

        assert delays == []
        assert len(httpx_mock.get_requests()) == 1

    async def test_no_retry_on_401(
        self, settings: Settings, httpx_mock: HTTPXMock, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test 401 errors are not retried."""
        delays: list[float] = []

        async def fake_sleep(delay: float) -> None:
            delays.append(delay)

        monkeypatch.setattr("dex_python.async_client.asyncio.sleep", fake_sleep)

        httpx_mock.add_response(
            url="https://api.getdex.com/api/rest/contacts?limit=100&offset=0",
            status_code=401,
            json={"error": "Unauthorized"},
        )

        async with AsyncDexClient(settings, max_retries=3, retry_delay=0.01) as client:
            with pytest.raises(AuthenticationError):
                await client.get_contacts()

        assert delays == []
        assert len(httpx_mock.get_requests()) == 1

    async def test_retry_on_all_retryable_codes(
        self, settings: Settings, httpx_mock: HTTPXMock, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test retry on all retryable status codes (429, 500, 502, 503, 504)."""
        retryable_codes = [429, 500, 502, 503, 504]

        for code in retryable_codes:
            delays: list[float] = []

            async def fake_sleep(delay: float) -> None:
                delays.append(delay)

            monkeypatch.setattr("dex_python.async_client.asyncio.sleep", fake_sleep)

            httpx_mock.reset()
            httpx_mock.add_response(
                url="https://api.getdex.com/api/rest/contacts?limit=100&offset=0",
                status_code=code,
            )
            httpx_mock.add_response(
                url="https://api.getdex.com/api/rest/contacts?limit=100&offset=0",
                json={"contacts": []},
            )

            async with AsyncDexClient(settings, max_retries=1, retry_delay=0.01) as client:
                await client.get_contacts()

            assert len(delays) == 1, f"Expected retry for status code {code}"

    async def test_default_no_retries(
        self, settings: Settings, httpx_mock: HTTPXMock, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test default client has no retries (max_retries=0)."""
        delays: list[float] = []

        async def fake_sleep(delay: float) -> None:
            delays.append(delay)

        monkeypatch.setattr("dex_python.async_client.asyncio.sleep", fake_sleep)

        httpx_mock.add_response(
            url="https://api.getdex.com/api/rest/contacts?limit=100&offset=0",
            status_code=503,
        )

        async with AsyncDexClient(settings) as client:
            with pytest.raises(DexAPIError):
                await client.get_contacts()

        assert delays == []
        assert len(httpx_mock.get_requests()) == 1
