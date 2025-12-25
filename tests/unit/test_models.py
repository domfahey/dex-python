"""Tests for Dex API models."""

from datetime import datetime

import pytest
from pydantic import ValidationError

from dex_python.models import (
    Contact,
    ContactCreate,
    ContactEmailResponse,
    ContactPhoneResponse,
    ContactUpdate,
    Note,
    NoteContact,
    NoteCreate,
    NoteUpdate,
    PaginatedContacts,
    PaginatedNotes,
    PaginatedReminders,
    Reminder,
    ReminderContact,
    ReminderCreate,
    ReminderUpdate,
)

# =============================================================================
# Task 1: Nested Response Fields Tests
# =============================================================================


class TestNestedResponseFields:
    """Test that response models use typed nested models."""

    def test_contact_emails_typed(self) -> None:
        """Contact.emails should be list[ContactEmailResponse]."""
        contact = Contact(
            id="123",
            emails=[{"email": "test@example.com", "contact_id": "123"}],
        )
        assert len(contact.emails) == 1
        assert isinstance(contact.emails[0], ContactEmailResponse)
        assert contact.emails[0].email == "test@example.com"
        assert contact.emails[0].contact_id == "123"

    def test_contact_phones_typed(self) -> None:
        """Contact.phones should be list[ContactPhoneResponse]."""
        contact = Contact(
            id="123",
            phones=[{"phone_number": "555-1234", "label": "Work"}],
        )
        assert len(contact.phones) == 1
        assert isinstance(contact.phones[0], ContactPhoneResponse)
        assert contact.phones[0].phone_number == "555-1234"
        assert contact.phones[0].label == "Work"

    def test_reminder_contacts_typed(self) -> None:
        """Reminder.contact_ids should be list[ReminderContact]."""
        reminder = Reminder(
            id="rem-123",
            body="Test reminder",
            contact_ids=[{"contact_id": "c1"}, {"contact_id": "c2"}],
        )
        assert len(reminder.contact_ids) == 2
        assert isinstance(reminder.contact_ids[0], ReminderContact)
        assert reminder.contact_ids[0].contact_id == "c1"

    def test_note_contacts_typed(self) -> None:
        """Note.contacts should be list[NoteContact]."""
        note = Note(
            id="note-123",
            note="Test note",
            contacts=[{"contact_id": "c1"}],
        )
        assert len(note.contacts) == 1
        assert isinstance(note.contacts[0], NoteContact)
        assert note.contacts[0].contact_id == "c1"

    def test_contact_email_response_model(self) -> None:
        """ContactEmailResponse should have email and optional contact_id."""
        email = ContactEmailResponse(email="test@example.com")
        assert email.email == "test@example.com"
        assert email.contact_id is None

    def test_contact_phone_response_model(self) -> None:
        """ContactPhoneResponse should have phone_number, optional label/contact_id."""
        phone = ContactPhoneResponse(phone_number="555-1234")
        assert phone.phone_number == "555-1234"
        assert phone.label is None
        assert phone.contact_id is None


# =============================================================================
# Task 2: Exclude Path IDs from Update Payloads
# =============================================================================


class TestExcludePathIds:
    """Test that path IDs are excluded from serialization."""

    def test_reminder_update_excludes_reminder_id(self) -> None:
        """ReminderUpdate.reminder_id should NOT be in model_dump output."""
        update = ReminderUpdate(
            reminder_id="rem-123",
            changes={"text": "Updated"},
        )
        data = update.model_dump(exclude_none=True)
        assert "reminder_id" not in data
        # But it should still be accessible as attribute
        assert update.reminder_id == "rem-123"

    def test_note_update_excludes_note_id(self) -> None:
        """NoteUpdate.note_id should NOT be in model_dump output."""
        update = NoteUpdate(
            note_id="note-123",
            changes={"note": "Updated"},
        )
        data = update.model_dump(exclude_none=True)
        assert "note_id" not in data
        # But it should still be accessible as attribute
        assert update.note_id == "note-123"

    def test_contact_update_includes_contact_id(self) -> None:
        """ContactUpdate.contact_id SHOULD be in payload as contactId (per API docs)."""
        update = ContactUpdate(
            contact_id="c-123",
            changes={"first_name": "Updated"},
        )
        data = update.model_dump(exclude_none=True, by_alias=True)
        # contactId IS expected in body per Dex API docs
        assert "contactId" in data
        assert data["contactId"] == "c-123"


# =============================================================================
# Task 3: Accept datetime Inputs with JSON Serialization
# =============================================================================


class TestDatetimeInputs:
    """Test that request models accept datetime and serialize to ISO strings."""

    def test_note_create_accepts_datetime_event_time(self) -> None:
        """NoteCreate.event_time should accept datetime and serialize to ISO."""
        dt = datetime(2025, 1, 15, 10, 30, 0)
        note = NoteCreate(note="Test", event_time=dt)
        data = note.model_dump(mode="json")
        assert data["event_time"] == "2025-01-15T10:30:00"

    def test_note_create_accepts_string_event_time(self) -> None:
        """NoteCreate.event_time should still accept string."""
        note = NoteCreate(note="Test", event_time="2025-01-15T10:30:00.000Z")
        data = note.model_dump(mode="json")
        assert data["event_time"] == "2025-01-15T10:30:00.000Z"

    def test_contact_create_accepts_datetime_last_seen_at(self) -> None:
        """ContactCreate.last_seen_at should accept datetime."""
        dt = datetime(2025, 1, 15, 10, 30, 0)
        contact = ContactCreate(first_name="Test", last_seen_at=dt)
        data = contact.model_dump(mode="json", exclude_none=True)
        assert data["last_seen_at"] == "2025-01-15T10:30:00"

    def test_contact_create_accepts_datetime_next_reminder_at(self) -> None:
        """ContactCreate.next_reminder_at should accept datetime."""
        dt = datetime(2025, 1, 15, 10, 30, 0)
        contact = ContactCreate(first_name="Test", next_reminder_at=dt)
        data = contact.model_dump(mode="json", exclude_none=True)
        assert data["next_reminder_at"] == "2025-01-15T10:30:00"


# =============================================================================
# Task 4: Relax changes Typing
# =============================================================================


class TestRelaxChangesTyping:
    """Test that changes dict accepts Any values."""

    def test_contact_update_changes_accepts_any(self) -> None:
        """ContactUpdate.changes should accept bool, datetime, lists, etc."""
        update = ContactUpdate(
            contact_id="c-123",
            changes={
                "first_name": "Test",
                "birthday_year": 1990,
                "is_active": True,  # bool wasn't allowed before
                "tags": ["vip", "customer"],  # list wasn't allowed
            },
        )
        assert update.changes["is_active"] is True
        assert update.changes["tags"] == ["vip", "customer"]

    def test_reminder_update_changes_accepts_any(self) -> None:
        """ReminderUpdate.changes should accept int, datetime, etc."""
        dt = datetime(2025, 1, 15, 10, 30, 0)
        update = ReminderUpdate(
            reminder_id="rem-123",
            changes={
                "text": "Updated",
                "is_complete": True,
                "priority": 5,  # int wasn't allowed before
                "due_at": dt,  # datetime wasn't allowed
            },
        )
        assert update.changes["priority"] == 5
        assert update.changes["due_at"] == dt

    def test_note_update_changes_accepts_any(self) -> None:
        """NoteUpdate.changes should accept bool, datetime, etc."""
        dt = datetime(2025, 1, 15, 10, 30, 0)
        update = NoteUpdate(
            note_id="note-123",
            changes={
                "note": "Updated",
                "is_pinned": True,  # bool wasn't allowed
                "event_time": dt,  # datetime wasn't allowed
            },
        )
        assert update.changes["is_pinned"] is True
        assert update.changes["event_time"] == dt


# =============================================================================
# Task 5: Avoid Strict Datetime Parsing on Response Models
# =============================================================================


class TestResponseDatetimeAsString:
    """Test that response models accept string timestamps from API."""

    def test_note_event_time_accepts_string(self) -> None:
        """Note.event_time should accept ISO string from API response."""
        note = Note(
            id="note-123",
            note="Test note",
            event_time="2025-01-15T10:30:00.000Z",
        )
        # Should be stored as string, not parsed to datetime
        assert note.event_time == "2025-01-15T10:30:00.000Z"
        assert isinstance(note.event_time, str)

    def test_note_event_time_accepts_none(self) -> None:
        """Note.event_time should accept None."""
        note = Note(
            id="note-123",
            note="Test note",
            event_time=None,
        )
        assert note.event_time is None


# =============================================================================
# Task 6: extra="forbid" on Request Models
# =============================================================================


class TestExtraForbid:
    """Test that request models reject unknown fields."""

    def test_contact_create_rejects_unknown_field(self) -> None:
        """ContactCreate should reject unknown fields (catch typos)."""
        with pytest.raises(ValidationError) as exc_info:
            ContactCreate(
                frist_name="Test",  # typo: frist_name instead of first_name
            )
        assert "frist_name" in str(exc_info.value)

    def test_contact_update_rejects_unknown_field(self) -> None:
        """ContactUpdate should reject unknown fields."""
        with pytest.raises(ValidationError) as exc_info:
            ContactUpdate(
                contact_id="c-123",
                chagnes={"first_name": "Test"},  # typo: chagnes
            )
        assert "chagnes" in str(exc_info.value)

    def test_reminder_create_rejects_unknown_field(self) -> None:
        """ReminderCreate should reject unknown fields."""
        with pytest.raises(ValidationError) as exc_info:
            ReminderCreate(
                text="Test",
                tittle="Important",  # typo: tittle
            )
        assert "tittle" in str(exc_info.value)

    def test_reminder_update_rejects_unknown_field(self) -> None:
        """ReminderUpdate should reject unknown fields."""
        with pytest.raises(ValidationError) as exc_info:
            ReminderUpdate(
                reminder_id="rem-123",
                chagnes={"text": "Updated"},  # typo: chagnes
            )
        assert "chagnes" in str(exc_info.value)

    def test_note_create_rejects_unknown_field(self) -> None:
        """NoteCreate should reject unknown fields."""
        with pytest.raises(ValidationError) as exc_info:
            NoteCreate(
                note="Test",
                evnet_time="2025-01-15T10:30:00Z",  # typo: evnet_time
            )
        assert "evnet_time" in str(exc_info.value)

    def test_note_update_rejects_unknown_field(self) -> None:
        """NoteUpdate should reject unknown fields."""
        with pytest.raises(ValidationError) as exc_info:
            NoteUpdate(
                note_id="note-123",
                chagnes={"note": "Updated"},  # typo: chagnes
            )
        assert "chagnes" in str(exc_info.value)


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
        """Test model dump excludes None values and reminder_id."""
        update = ReminderUpdate(
            reminder_id="123",
            changes={"text": "Updated"},
        )
        data = update.model_dump(exclude_none=True)
        # reminder_id is excluded from payload (used only in URL path)
        assert "reminder_id" not in data
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
        """Test model dump excludes None values and note_id."""
        update = NoteUpdate(
            note_id="123",
            changes={"note": "Updated"},
        )
        data = update.model_dump(exclude_none=True)
        # note_id is excluded from payload (used only in URL path)
        assert "note_id" not in data
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
