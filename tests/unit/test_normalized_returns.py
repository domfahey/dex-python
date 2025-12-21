"""Tests for normalized return values from write operations."""

from pytest_httpx import HTTPXMock

from dex_python import DexClient, Settings
from dex_python.models import ContactCreate, NoteCreate, ReminderCreate


class TestNormalizedContactReturns:
    """Test normalized return values for contact operations."""

    def test_create_contact_returns_entity(
        self, settings: Settings, httpx_mock: HTTPXMock
    ) -> None:
        """Test that create_contact returns the created entity."""
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

        with DexClient(settings) as client:
            result = client.create_contact(ContactCreate(first_name="Alice"))

        assert result["id"] == "new-123"
        assert result["first_name"] == "Alice"

    def test_update_contact_returns_entity(
        self, settings: Settings, httpx_mock: HTTPXMock
    ) -> None:
        """Test that update_contact returns the updated entity."""
        from dex_python.models import ContactUpdate

        httpx_mock.add_response(
            url="https://api.getdex.com/api/rest/contacts/c-123",
            method="PUT",
            json={
                "update_contacts_by_pk": {
                    "id": "c-123",
                    "first_name": "Updated",
                }
            },
        )

        with DexClient(settings) as client:
            result = client.update_contact(
                ContactUpdate(contact_id="c-123", changes={"first_name": "Updated"})
            )

        assert result["id"] == "c-123"
        assert result["first_name"] == "Updated"

    def test_delete_contact_returns_entity(
        self, settings: Settings, httpx_mock: HTTPXMock
    ) -> None:
        """Test that delete_contact returns the deleted entity."""
        httpx_mock.add_response(
            url="https://api.getdex.com/api/rest/contacts/c-123",
            method="DELETE",
            json={"delete_contacts_by_pk": {"id": "c-123"}},
        )

        with DexClient(settings) as client:
            result = client.delete_contact("c-123")

        assert result["id"] == "c-123"


class TestNormalizedReminderReturns:
    """Test normalized return values for reminder operations."""

    def test_create_reminder_returns_entity(
        self, settings: Settings, httpx_mock: HTTPXMock
    ) -> None:
        """Test that create_reminder returns the created entity."""
        httpx_mock.add_response(
            url="https://api.getdex.com/api/rest/reminders",
            method="POST",
            json={
                "insert_reminders_one": {
                    "id": "r-123",
                    "body": "Test reminder",
                }
            },
        )

        with DexClient(settings) as client:
            result = client.create_reminder(ReminderCreate(text="Test reminder"))

        assert result["id"] == "r-123"
        assert result["body"] == "Test reminder"


class TestNormalizedNoteReturns:
    """Test normalized return values for note operations."""

    def test_create_note_returns_entity(
        self, settings: Settings, httpx_mock: HTTPXMock
    ) -> None:
        """Test that create_note returns the created entity."""
        httpx_mock.add_response(
            url="https://api.getdex.com/api/rest/timeline_items",
            method="POST",
            json={
                "insert_timeline_items_one": {
                    "id": "n-123",
                    "note": "Test note",
                }
            },
        )

        with DexClient(settings) as client:
            result = client.create_note(NoteCreate(note="Test note"))

        assert result["id"] == "n-123"
        assert result["note"] == "Test note"
