"""Tests for Dex API models."""

from src.dex_import.models import (
    ContactCreate,
    NoteCreate,
    NoteUpdate,
    PaginatedContacts,
    PaginatedNotes,
    PaginatedReminders,
    ReminderCreate,
    ReminderUpdate,
)


class TestReminderUpdate:
    """Test suite for ReminderUpdate model."""

    def test_basic_update(self) -> None:
        """Test creating basic reminder update."""
        update = ReminderUpdate(
            reminder_id="123-456",
            changes={"text": "Updated reminder", "is_complete": True},
        )
        assert update.reminder_id == "123-456"
        assert update.changes["text"] == "Updated reminder"
        assert update.changes["is_complete"] is True

    def test_update_with_contacts(self) -> None:
        """Test reminder update with contact associations."""
        update = ReminderUpdate(
            reminder_id="123",
            changes={"text": "New text"},
            update_contacts=True,
            reminders_contacts=[
                {"reminder_id": "123", "contact_id": "contact-1"},
                {"reminder_id": "123", "contact_id": "contact-2"},
            ],
        )
        assert update.update_contacts is True
        assert len(update.reminders_contacts) == 2

    def test_model_dump_excludes_none(self) -> None:
        """Test model dump excludes None values."""
        update = ReminderUpdate(
            reminder_id="123",
            changes={"text": "Updated"},
        )
        data = update.model_dump(exclude_none=True)
        assert "reminder_id" in data
        assert "changes" in data
        assert data["update_contacts"] is False  # Default value included

    def test_factory_method(self) -> None:
        """Test factory method for common update pattern."""
        update = ReminderUpdate.mark_complete("reminder-123")
        assert update.reminder_id == "reminder-123"
        assert update.changes["is_complete"] is True


class TestNoteUpdate:
    """Test suite for NoteUpdate model."""

    def test_basic_update(self) -> None:
        """Test creating basic note update."""
        update = NoteUpdate(
            note_id="note-123",
            changes={"note": "Updated note text"},
        )
        assert update.note_id == "note-123"
        assert update.changes["note"] == "Updated note text"

    def test_update_with_contacts(self) -> None:
        """Test note update with contact associations."""
        update = NoteUpdate(
            note_id="note-123",
            changes={"note": "New text"},
            update_contacts=True,
            timeline_items_contacts=[
                {"timeline_item_id": "note-123", "contact_id": "contact-1"},
            ],
        )
        assert update.update_contacts is True
        assert len(update.timeline_items_contacts) == 1

    def test_update_with_event_time(self) -> None:
        """Test note update with event time change."""
        update = NoteUpdate(
            note_id="note-123",
            changes={
                "note": "Meeting notes",
                "event_time": "2025-01-15T10:00:00.000Z",
            },
        )
        assert "event_time" in update.changes

    def test_model_dump_excludes_none(self) -> None:
        """Test model dump excludes None values."""
        update = NoteUpdate(
            note_id="123",
            changes={"note": "Updated"},
        )
        data = update.model_dump(exclude_none=True)
        assert "note_id" in data
        assert "changes" in data


class TestPaginatedContacts:
    """Test suite for PaginatedContacts model."""

    def test_paginated_response(self) -> None:
        """Test paginated contacts response."""
        response = PaginatedContacts(
            contacts=[
                {"id": "1", "first_name": "John"},
                {"id": "2", "first_name": "Jane"},
            ],
            total=100,
        )
        assert len(response.contacts) == 2
        assert response.total == 100

    def test_empty_response(self) -> None:
        """Test empty paginated response."""
        response = PaginatedContacts(contacts=[], total=0)
        assert len(response.contacts) == 0
        assert response.total == 0

    def test_has_more_property(self) -> None:
        """Test has_more property for pagination."""
        response = PaginatedContacts(
            contacts=[{"id": "1"}],
            total=100,
            limit=10,
            offset=0,
        )
        assert response.has_more is True

        response2 = PaginatedContacts(
            contacts=[{"id": "1"}],
            total=1,
            limit=10,
            offset=0,
        )
        assert response2.has_more is False


class TestPaginatedReminders:
    """Test suite for PaginatedReminders model."""

    def test_paginated_response(self) -> None:
        """Test paginated reminders response."""
        response = PaginatedReminders(
            reminders=[
                {"id": "1", "body": "Reminder 1"},
                {"id": "2", "body": "Reminder 2"},
            ],
            total=50,
        )
        assert len(response.reminders) == 2
        assert response.total == 50


class TestPaginatedNotes:
    """Test suite for PaginatedNotes model."""

    def test_paginated_response(self) -> None:
        """Test paginated notes response."""
        response = PaginatedNotes(
            notes=[
                {"id": "1", "note": "Note 1"},
                {"id": "2", "note": "Note 2"},
            ],
            total=25,
        )
        assert len(response.notes) == 2
        assert response.total == 25


class TestContactCreateFactories:
    """Additional tests for ContactCreate factory methods."""

    def test_with_email_and_phone(self) -> None:
        """Test creating contact with both email and phone."""
        contact = ContactCreate(
            first_name="Test",
            last_name="User",
            contact_emails={"data": {"email": "test@example.com"}},
            contact_phone_numbers={"data": {"phone_number": "123", "label": "Work"}},
        )
        assert contact.contact_emails is not None
        assert contact.contact_phone_numbers is not None


class TestReminderCreateFactories:
    """Additional tests for ReminderCreate factory methods."""

    def test_with_contacts_factory(self) -> None:
        """Test with_contacts factory method."""
        reminder = ReminderCreate.with_contacts(
            text="Follow up",
            contact_ids=["c1", "c2", "c3"],
            due_at_date="2025-01-20",
            title="Important",
        )
        assert reminder.text == "Follow up"
        assert reminder.title == "Important"
        assert reminder.due_at_date == "2025-01-20"
        assert reminder.reminders_contacts is not None
        assert len(reminder.reminders_contacts["data"]) == 3


class TestNoteCreateFactories:
    """Additional tests for NoteCreate factory methods."""

    def test_with_contacts_factory(self) -> None:
        """Test with_contacts factory method."""
        note = NoteCreate.with_contacts(
            note="Meeting notes",
            contact_ids=["c1", "c2"],
            event_time="2025-01-15T10:00:00.000Z",
        )
        assert note.note == "Meeting notes"
        assert note.event_time == "2025-01-15T10:00:00.000Z"
        assert note.timeline_items_contacts is not None
        assert len(note.timeline_items_contacts["data"]) == 2
