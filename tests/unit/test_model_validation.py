"""Additional model validation tests for boundary conditions and edge cases.

Supplements tests in test_models.py with additional edge cases.
"""

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from dex_python.models import (
    Contact,
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


class TestBirthdayYearValidation:
    """Test birthday_year field validation boundaries."""

    def test_birthday_year_at_1900_boundary(self) -> None:
        """Birthday year 1900 should be accepted (boundary)."""
        contact = ContactCreate(first_name="Test", birthday_year=1900)
        assert contact.birthday_year == 1900

    def test_birthday_year_below_1900_rejected(self) -> None:
        """Birthday year below 1900 should be rejected."""
        with pytest.raises(ValidationError) as exc_info:
            ContactCreate(first_name="Test", birthday_year=1899)
        assert "birthday_year" in str(exc_info.value)

    def test_birthday_year_at_current_year(self) -> None:
        """Birthday year at current year should be accepted."""
        current_year = datetime.now().year
        contact = ContactCreate(first_name="Test", birthday_year=current_year)
        assert contact.birthday_year == current_year

    def test_birthday_year_above_current_year_rejected(self) -> None:
        """Birthday year above current year should be rejected."""
        future_year = datetime.now().year + 1
        with pytest.raises(ValidationError) as exc_info:
            ContactCreate(first_name="Test", birthday_year=future_year)
        assert "birthday_year" in str(exc_info.value)

    def test_birthday_year_way_in_future_rejected(self) -> None:
        """Birthday year way in future should be rejected."""
        with pytest.raises(ValidationError):
            ContactCreate(first_name="Test", birthday_year=2100)

    def test_birthday_year_negative_rejected(self) -> None:
        """Negative birthday year should be rejected."""
        with pytest.raises(ValidationError):
            ContactCreate(first_name="Test", birthday_year=-1)

    def test_birthday_year_zero_rejected(self) -> None:
        """Birthday year 0 should be rejected."""
        with pytest.raises(ValidationError):
            ContactCreate(first_name="Test", birthday_year=0)


class TestDueDateValidation:
    """Test due_at_date field validation."""

    def test_valid_date_format(self) -> None:
        """Valid YYYY-MM-DD format should be accepted."""
        reminder = ReminderCreate(text="Test", due_at_date="2025-01-15")
        assert reminder.due_at_date == "2025-01-15"

    def test_invalid_date_format_mm_dd_yyyy(self) -> None:
        """MM/DD/YYYY format should be rejected."""
        with pytest.raises(ValidationError):
            ReminderCreate(text="Test", due_at_date="01/15/2025")

    def test_invalid_date_format_dd_mm_yyyy(self) -> None:
        """DD-MM-YYYY format should be rejected."""
        with pytest.raises(ValidationError):
            ReminderCreate(text="Test", due_at_date="15-01-2025")

    def test_invalid_date_format_iso_with_time(self) -> None:
        """ISO format with time should be rejected."""
        with pytest.raises(ValidationError):
            ReminderCreate(text="Test", due_at_date="2025-01-15T10:30:00")

    def test_invalid_date_format_text(self) -> None:
        """Text date format should be rejected."""
        with pytest.raises(ValidationError):
            ReminderCreate(text="Test", due_at_date="January 15, 2025")

    def test_invalid_date_impossible_day(self) -> None:
        """Impossible day (Feb 30) still passes regex but is allowed."""
        # The validator only checks format, not validity
        reminder = ReminderCreate(text="Test", due_at_date="2025-02-30")
        assert reminder.due_at_date == "2025-02-30"

    def test_none_due_date_valid(self) -> None:
        """None due_at_date should be valid."""
        reminder = ReminderCreate(text="Test", due_at_date=None)
        assert reminder.due_at_date is None


class TestPaginationBoundaries:
    """Test pagination model boundaries."""

    def test_total_zero(self) -> None:
        """Total of 0 should be valid."""
        page = PaginatedContacts(contacts=[], total=0)
        assert page.total == 0
        assert page.has_more is False

    def test_total_negative_rejected(self) -> None:
        """Negative total should be rejected (ge=0 constraint)."""
        with pytest.raises(ValidationError):
            PaginatedContacts(contacts=[], total=-1)

    def test_limit_minimum(self) -> None:
        """Limit of 1 should be valid (ge=1)."""
        page = PaginatedContacts(contacts=[], total=0, limit=1)
        assert page.limit == 1

    def test_limit_zero_rejected(self) -> None:
        """Limit of 0 should be rejected."""
        with pytest.raises(ValidationError):
            PaginatedContacts(contacts=[], total=0, limit=0)

    def test_limit_maximum(self) -> None:
        """Limit of 1000 should be valid (le=1000)."""
        page = PaginatedContacts(contacts=[], total=0, limit=1000)
        assert page.limit == 1000

    def test_limit_above_maximum_rejected(self) -> None:
        """Limit above 1000 should be rejected."""
        with pytest.raises(ValidationError):
            PaginatedContacts(contacts=[], total=0, limit=1001)

    def test_offset_zero(self) -> None:
        """Offset of 0 should be valid."""
        page = PaginatedContacts(contacts=[], total=0, offset=0)
        assert page.offset == 0

    def test_offset_negative_rejected(self) -> None:
        """Negative offset should be rejected."""
        with pytest.raises(ValidationError):
            PaginatedContacts(contacts=[], total=0, offset=-1)

    def test_offset_large_value(self) -> None:
        """Large offset should be valid."""
        page = PaginatedContacts(contacts=[], total=1000000, offset=999999)
        assert page.offset == 999999

    def test_has_more_exact_boundary(self) -> None:
        """has_more at exact boundary (offset + len == total)."""
        page = PaginatedContacts(
            contacts=[{"id": "1"}, {"id": "2"}],
            total=10,
            limit=2,
            offset=8,
        )
        # offset(8) + len(2) = 10 = total, so no more
        assert page.has_more is False

    def test_has_more_one_before_boundary(self) -> None:
        """has_more one before boundary."""
        page = PaginatedContacts(
            contacts=[{"id": "1"}, {"id": "2"}],
            total=11,
            limit=2,
            offset=8,
        )
        # offset(8) + len(2) = 10 < 11 total, so has more
        assert page.has_more is True

    def test_reminders_pagination_has_more(self) -> None:
        """PaginatedReminders has_more should work correctly."""
        page = PaginatedReminders(
            reminders=[{"id": "1"}],
            total=100,
            limit=10,
            offset=90,
        )
        # offset(90) + len(1) = 91 < 100, has more
        assert page.has_more is True

    def test_notes_pagination_has_more(self) -> None:
        """PaginatedNotes has_more should work correctly."""
        page = PaginatedNotes(
            notes=[{"id": "1"}],
            total=1,
            limit=10,
            offset=0,
        )
        # offset(0) + len(1) = 1 = total, no more
        assert page.has_more is False


class TestTimestampFields:
    """Test timestamp field handling."""

    def test_last_seen_at_datetime(self) -> None:
        """last_seen_at should accept datetime."""
        dt = datetime(2025, 1, 15, 10, 30, 0)
        contact = ContactCreate(first_name="Test", last_seen_at=dt)
        data = contact.model_dump(mode="json", exclude_none=True)
        assert data["last_seen_at"] == "2025-01-15T10:30:00"

    def test_last_seen_at_string(self) -> None:
        """last_seen_at should accept string."""
        contact = ContactCreate(first_name="Test", last_seen_at="2025-01-15T10:30:00Z")
        assert contact.last_seen_at == "2025-01-15T10:30:00Z"

    def test_last_seen_at_with_timezone(self) -> None:
        """last_seen_at should handle timezone-aware datetime."""
        dt = datetime(2025, 1, 15, 10, 30, 0, tzinfo=timezone.utc)
        contact = ContactCreate(first_name="Test", last_seen_at=dt)
        data = contact.model_dump(mode="json", exclude_none=True)
        assert "+00:00" in data["last_seen_at"] or "Z" in data["last_seen_at"]

    def test_next_reminder_at_datetime(self) -> None:
        """next_reminder_at should accept datetime."""
        dt = datetime(2025, 1, 20, 9, 0, 0)
        contact = ContactCreate(first_name="Test", next_reminder_at=dt)
        data = contact.model_dump(mode="json", exclude_none=True)
        assert "2025-01-20" in data["next_reminder_at"]

    def test_event_time_datetime(self) -> None:
        """NoteCreate.event_time should accept datetime."""
        dt = datetime(2025, 1, 15, 14, 30, 0)
        note = NoteCreate(note="Test", event_time=dt)
        data = note.model_dump(mode="json")
        assert data["event_time"] == "2025-01-15T14:30:00"

    def test_event_time_with_microseconds(self) -> None:
        """event_time should preserve microseconds."""
        dt = datetime(2025, 1, 15, 14, 30, 0, 123456)
        note = NoteCreate(note="Test", event_time=dt)
        data = note.model_dump(mode="json")
        assert "123456" in data["event_time"]


class TestExtractorFunctions:
    """Test API response extractor functions."""

    def test_extract_contacts_total_standard(self) -> None:
        """extract_contacts_total should work with standard format."""
        data = {"pagination": {"total": {"count": 42}}}
        assert extract_contacts_total(data) == 42

    def test_extract_contacts_total_missing_pagination(self) -> None:
        """extract_contacts_total should return 0 when pagination missing."""
        data = {}
        assert extract_contacts_total(data) == 0

    def test_extract_contacts_total_missing_total(self) -> None:
        """extract_contacts_total should return 0 when total missing."""
        data = {"pagination": {}}
        assert extract_contacts_total(data) == 0

    def test_extract_contacts_total_missing_count(self) -> None:
        """extract_contacts_total should return 0 when count missing."""
        data = {"pagination": {"total": {}}}
        assert extract_contacts_total(data) == 0

    def test_extract_contacts_total_non_int_count(self) -> None:
        """extract_contacts_total should return 0 for non-int count."""
        data = {"pagination": {"total": {"count": "42"}}}
        assert extract_contacts_total(data) == 0

    def test_extract_reminders_total_standard(self) -> None:
        """extract_reminders_total should work with standard format."""
        data = {"total": {"aggregate": {"count": 15}}}
        assert extract_reminders_total(data) == 15

    def test_extract_reminders_total_missing(self) -> None:
        """extract_reminders_total should return 0 when data missing."""
        assert extract_reminders_total({}) == 0
        assert extract_reminders_total({"total": {}}) == 0
        assert extract_reminders_total({"total": {"aggregate": {}}}) == 0

    def test_extract_contact_entity_insert(self) -> None:
        """extract_contact_entity should extract from insert response."""
        data = {"insert_contacts_one": {"id": "123", "first_name": "John"}}
        result = extract_contact_entity(data)
        assert result["id"] == "123"

    def test_extract_contact_entity_update(self) -> None:
        """extract_contact_entity should extract from update response."""
        data = {"update_contacts_by_pk": {"id": "456"}}
        result = extract_contact_entity(data)
        assert result["id"] == "456"

    def test_extract_contact_entity_delete(self) -> None:
        """extract_contact_entity should extract from delete response."""
        data = {"delete_contacts_by_pk": {"id": "789"}}
        result = extract_contact_entity(data)
        assert result["id"] == "789"

    def test_extract_contact_entity_unknown_format(self) -> None:
        """extract_contact_entity should return original for unknown format."""
        data = {"unknown_key": {"id": "999"}}
        result = extract_contact_entity(data)
        assert result == data

    def test_extract_reminder_entity(self) -> None:
        """extract_reminder_entity should work for all operations."""
        assert extract_reminder_entity(
            {"insert_reminders_one": {"id": "1"}}
        ) == {"id": "1"}
        assert extract_reminder_entity(
            {"update_reminders_by_pk": {"id": "2"}}
        ) == {"id": "2"}
        assert extract_reminder_entity(
            {"delete_reminders_by_pk": {"id": "3"}}
        ) == {"id": "3"}

    def test_extract_note_entity(self) -> None:
        """extract_note_entity should work for all operations."""
        assert extract_note_entity(
            {"insert_timeline_items_one": {"id": "1"}}
        ) == {"id": "1"}
        assert extract_note_entity(
            {"update_timeline_items_by_pk": {"id": "2"}}
        ) == {"id": "2"}
        assert extract_note_entity(
            {"delete_timeline_items_by_pk": {"id": "3"}}
        ) == {"id": "3"}


class TestUpdateModelsChangesDict:
    """Test that update models handle changes dict correctly."""

    def test_contact_update_changes_any_type(self) -> None:
        """ContactUpdate.changes should accept any value types."""
        update = ContactUpdate(
            contact_id="c1",
            changes={
                "first_name": "John",
                "birthday_year": 1990,
                "is_active": True,
                "tags": ["vip", "customer"],
                "metadata": {"key": "value"},
            },
        )
        assert update.changes["is_active"] is True
        assert update.changes["tags"] == ["vip", "customer"]
        assert update.changes["metadata"] == {"key": "value"}

    def test_reminder_update_changes_with_datetime(self) -> None:
        """ReminderUpdate.changes should accept datetime values."""
        dt = datetime(2025, 1, 15, 10, 0, 0)
        update = ReminderUpdate(
            reminder_id="rem1",
            changes={"due_at": dt, "is_complete": True},
        )
        assert update.changes["due_at"] == dt

    def test_note_update_changes_empty(self) -> None:
        """NoteUpdate with empty changes should be valid."""
        update = NoteUpdate(note_id="note1", changes={})
        assert update.changes == {}


class TestFactoryMethods:
    """Test model factory methods."""

    def test_contact_create_with_email(self) -> None:
        """ContactCreate.with_email should create correct structure."""
        contact = ContactCreate.with_email(
            "test@example.com",
            first_name="John",
            last_name="Doe",
        )
        assert contact.first_name == "John"
        assert contact.last_name == "Doe"
        assert contact.contact_emails == {"data": {"email": "test@example.com"}}

    def test_contact_create_with_phone(self) -> None:
        """ContactCreate.with_phone should create correct structure."""
        contact = ContactCreate.with_phone(
            "555-1234",
            label="Mobile",
            first_name="John",
        )
        assert contact.contact_phone_numbers == {
            "data": {"phone_number": "555-1234", "label": "Mobile"}
        }

    def test_reminder_create_with_contacts(self) -> None:
        """ReminderCreate.with_contacts should create correct structure."""
        reminder = ReminderCreate.with_contacts(
            text="Follow up",
            contact_ids=["c1", "c2", "c3"],
            due_at_date="2025-01-20",
            title="Important",
        )
        assert reminder.text == "Follow up"
        assert reminder.title == "Important"
        assert reminder.due_at_date == "2025-01-20"
        assert len(reminder.reminders_contacts["data"]) == 3

    def test_note_create_with_contacts(self) -> None:
        """NoteCreate.with_contacts should create correct structure."""
        note = NoteCreate.with_contacts(
            note="Meeting notes",
            contact_ids=["c1", "c2"],
            event_time="2025-01-15T10:00:00Z",
        )
        assert note.note == "Meeting notes"
        assert note.event_time == "2025-01-15T10:00:00Z"
        assert len(note.timeline_items_contacts["data"]) == 2

    def test_reminder_update_mark_complete(self) -> None:
        """ReminderUpdate.mark_complete should set is_complete."""
        update = ReminderUpdate.mark_complete("rem123")
        assert update.reminder_id == "rem123"
        assert update.changes == {"is_complete": True}


class TestModelDumpBehavior:
    """Test model_dump behavior for serialization."""

    def test_reminder_update_excludes_reminder_id(self) -> None:
        """ReminderUpdate should exclude reminder_id from dump."""
        update = ReminderUpdate(reminder_id="rem1", changes={"text": "Updated"})
        data = update.model_dump(exclude_none=True)
        assert "reminder_id" not in data
        # But attribute should still be accessible
        assert update.reminder_id == "rem1"

    def test_note_update_excludes_note_id(self) -> None:
        """NoteUpdate should exclude note_id from dump."""
        update = NoteUpdate(note_id="note1", changes={"note": "Updated"})
        data = update.model_dump(exclude_none=True)
        assert "note_id" not in data

    def test_contact_update_includes_contact_id_by_alias(self) -> None:
        """ContactUpdate should include contactId when by_alias=True."""
        update = ContactUpdate(contact_id="c1", changes={"first_name": "John"})
        data = update.model_dump(by_alias=True, exclude_none=True)
        assert "contactId" in data
        assert data["contactId"] == "c1"
