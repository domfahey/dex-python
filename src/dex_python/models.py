"""Pydantic models for Dex API matching the official schema."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

# =============================================================================
# Contact Models
# =============================================================================


class ContactEmail(BaseModel):
    """Email associated with a contact."""

    model_config = ConfigDict(strict=True)

    email: str
    contact_id: str | None = None


class ContactPhone(BaseModel):
    """Phone number associated with a contact."""

    model_config = ConfigDict(strict=True)

    phone_number: str
    label: str = "Work"
    contact_id: str | None = None


class Contact(BaseModel):
    """Dex contact (GET response schema)."""

    model_config = ConfigDict(strict=True)

    id: str
    first_name: str | None = None
    last_name: str | None = None
    job_title: str | None = None
    description: str | None = None
    education: str | None = None
    website: str | None = None
    image_url: str | None = None

    # Social media handles
    linkedin: str | None = None
    facebook: str | None = None
    twitter: str | None = None
    instagram: str | None = None
    telegram: str | None = None

    # Timestamps
    birthday_current_year: str | None = None
    last_seen_at: str | None = None
    next_reminder_at: str | None = None

    # Nested arrays from API response
    emails: list[dict[str, str]] = Field(default_factory=list)
    phones: list[dict[str, str]] = Field(default_factory=list)


class ContactCreate(BaseModel):
    """Contact creation request body (POST /contacts)."""

    model_config = ConfigDict(strict=True)

    first_name: str | None = None
    last_name: str | None = None
    job_title: str | None = None
    description: str | None = None
    education: str | None = None
    website: str | None = None
    image_url: str | None = None

    # Social media handles
    linkedin: str | None = None
    twitter: str | None = None
    instagram: str | None = None
    telegram: str | None = None

    # Timestamps
    birthday_year: int | None = None
    last_seen_at: str | None = None
    next_reminder_at: str | None = None

    # Nested format required by API
    contact_emails: dict[str, dict[str, str]] | None = None
    contact_phone_numbers: dict[str, dict[str, str | None]] | None = None

    @classmethod
    def with_email(
        cls,
        email: str,
        first_name: str | None = None,
        last_name: str | None = None,
        **kwargs: str | int | None,
    ) -> "ContactCreate":
        """Create contact with email."""
        return cls(
            first_name=first_name,
            last_name=last_name,
            contact_emails={"data": {"email": email}},
            **kwargs,  # type: ignore[arg-type]
        )

    @classmethod
    def with_phone(
        cls,
        phone_number: str,
        label: str = "Work",
        first_name: str | None = None,
        last_name: str | None = None,
        **kwargs: str | int | None,
    ) -> "ContactCreate":
        """Create contact with phone number."""
        return cls(
            first_name=first_name,
            last_name=last_name,
            contact_phone_numbers={
                "data": {"phone_number": phone_number, "label": label}
            },
            **kwargs,  # type: ignore[arg-type]
        )


class ContactUpdate(BaseModel):
    """Contact update request body (PUT /contacts/{id})."""

    model_config = ConfigDict(strict=True, populate_by_name=True)

    contact_id: str = Field(alias="contactId")
    changes: dict[str, str | int | None] = Field(default_factory=dict)

    # Email updates
    update_contact_emails: bool = False
    contact_emails: list[ContactEmail] = Field(default_factory=list)

    # Phone updates
    update_contact_phone_numbers: bool = False
    contact_phone_numbers: list[ContactPhone] = Field(default_factory=list)


# =============================================================================
# Reminder Models
# =============================================================================


class ReminderContact(BaseModel):
    """Contact reference for a reminder."""

    model_config = ConfigDict(strict=True)

    contact_id: str | None = None
    email: str | None = None


class Reminder(BaseModel):
    """Dex reminder (GET response schema)."""

    model_config = ConfigDict(strict=True)

    id: str
    body: str
    is_complete: bool = False
    due_at_date: str | None = None
    due_at_time: str | None = None
    contact_ids: list[dict[str, str]] = Field(default_factory=list)


class ReminderCreate(BaseModel):
    """Reminder creation request body (POST /reminders)."""

    model_config = ConfigDict(strict=True)

    title: str | None = None
    text: str
    is_complete: bool = False
    due_at_date: str | None = None
    reminders_contacts: dict[str, list[dict[str, str]]] | None = None

    @classmethod
    def with_contacts(
        cls,
        text: str,
        contact_ids: list[str],
        due_at_date: str | None = None,
        title: str | None = None,
    ) -> "ReminderCreate":
        """Create reminder with associated contacts."""
        return cls(
            title=title,
            text=text,
            due_at_date=due_at_date,
            reminders_contacts={"data": [{"contact_id": cid} for cid in contact_ids]},
        )


class ReminderUpdate(BaseModel):
    """Reminder update request body (PUT /reminders/{id})."""

    model_config = ConfigDict(strict=True)

    reminder_id: str
    changes: dict[str, str | bool | None] = Field(default_factory=dict)
    update_contacts: bool = False
    reminders_contacts: list[dict[str, str]] = Field(default_factory=list)

    @classmethod
    def mark_complete(cls, reminder_id: str) -> "ReminderUpdate":
        """Create update to mark reminder as complete."""
        return cls(
            reminder_id=reminder_id,
            changes={"is_complete": True},
        )


# =============================================================================
# Note (Timeline Item) Models
# =============================================================================


class Note(BaseModel):
    """Dex note/timeline item (GET response schema)."""

    model_config = ConfigDict(strict=True)

    id: str
    note: str
    event_time: datetime | None = None
    contacts: list[dict[str, str]] = Field(default_factory=list)


class NoteCreate(BaseModel):
    """Note creation request body (POST /timeline_items)."""

    model_config = ConfigDict(strict=True)

    note: str
    event_time: str | None = None
    meeting_type: str = "note"
    timeline_items_contacts: dict[str, list[dict[str, str]]] | None = None

    @classmethod
    def with_contacts(
        cls,
        note: str,
        contact_ids: list[str],
        event_time: str | None = None,
    ) -> "NoteCreate":
        """Create note with associated contacts."""
        return cls(
            note=note,
            event_time=event_time,
            timeline_items_contacts={
                "data": [{"contact_id": cid} for cid in contact_ids]
            },
        )


class NoteUpdate(BaseModel):
    """Note update request body (PUT /timeline_items/{id})."""

    model_config = ConfigDict(strict=True)

    note_id: str
    changes: dict[str, str | None] = Field(default_factory=dict)
    update_contacts: bool = False
    timeline_items_contacts: list[dict[str, str]] = Field(default_factory=list)


# =============================================================================
# Pagination Response Models
# =============================================================================


class PaginatedContacts(BaseModel):
    """Paginated contacts response."""

    model_config = ConfigDict(strict=True)

    contacts: list[dict[str, Any]]
    total: int
    limit: int = 100
    offset: int = 0

    @property
    def has_more(self) -> bool:
        """Check if there are more results available."""
        return self.offset + len(self.contacts) < self.total


class PaginatedReminders(BaseModel):
    """Paginated reminders response."""

    model_config = ConfigDict(strict=True)

    reminders: list[dict[str, Any]]
    total: int
    limit: int = 100
    offset: int = 0

    @property
    def has_more(self) -> bool:
        """Check if there are more results available."""
        return self.offset + len(self.reminders) < self.total


class PaginatedNotes(BaseModel):
    """Paginated notes response."""

    model_config = ConfigDict(strict=True)

    notes: list[dict[str, Any]]
    total: int
    limit: int = 100
    offset: int = 0

    @property
    def has_more(self) -> bool:
        """Check if there are more results available."""
        return self.offset + len(self.notes) < self.total


def extract_contacts_total(data: dict[str, Any]) -> int:
    """Extract total count from contacts/notes pagination response."""
    pagination = data.get("pagination", {})
    if isinstance(pagination, dict):
        total = pagination.get("total", {})
        if isinstance(total, dict):
            count = total.get("count", 0)
            if isinstance(count, int):
                return count
    return 0


def extract_reminders_total(data: dict[str, Any]) -> int:
    """Extract total count from reminders response."""
    total = data.get("total", {})
    if isinstance(total, dict):
        aggregate = total.get("aggregate", {})
        if isinstance(aggregate, dict):
            count = aggregate.get("count", 0)
            if isinstance(count, int):
                return count
    return 0


# =============================================================================
# Response Entity Extractors
# =============================================================================


def extract_contact_entity(data: dict[str, Any]) -> dict[str, Any]:
    """Extract contact entity from create/update/delete response."""
    # Try different response wrapper keys
    keys = ["insert_contacts_one", "update_contacts_by_pk", "delete_contacts_by_pk"]
    for key in keys:
        entity = data.get(key)
        if isinstance(entity, dict):
            return entity
    return data  # Return as-is if no wrapper found


def extract_reminder_entity(data: dict[str, Any]) -> dict[str, Any]:
    """Extract reminder entity from create/update/delete response."""
    for key in [
        "insert_reminders_one",
        "update_reminders_by_pk",
        "delete_reminders_by_pk",
    ]:
        entity = data.get(key)
        if isinstance(entity, dict):
            return entity
    return data


def extract_note_entity(data: dict[str, Any]) -> dict[str, Any]:
    """Extract note entity from create/update/delete response."""
    for key in [
        "insert_timeline_items_one",
        "update_timeline_items_by_pk",
        "delete_timeline_items_by_pk",
    ]:
        entity = data.get(key)
        if isinstance(entity, dict):
            return entity
    return data
