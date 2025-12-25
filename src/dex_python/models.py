"""Pydantic models for Dex API matching the official schema.

This module defines all data models used for Dex API requests and responses.
Models use strict validation and match the official Dex API schema exactly.

Model Categories:
    - Contact models: ContactEmail, ContactPhone, Contact, ContactCreate, ContactUpdate
    - Reminder models: Reminder, ReminderCreate, ReminderUpdate
    - Note models: Note, NoteCreate, NoteUpdate
    - Pagination: PaginatedContacts, PaginatedReminders, PaginatedNotes

Example:
    >>> from dex_python import Contact, ContactCreate
    >>> new_contact = ContactCreate.with_email("user@example.com", first_name="John")
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_serializer

# =============================================================================
# Contact Models
# =============================================================================


class ContactEmail(BaseModel):
    """Email address for request payloads (creating/updating contacts).

    Attributes:
        email: The email address.
        contact_id: ID of the associated contact (set by API).
    """

    model_config = ConfigDict(strict=True)

    email: str
    contact_id: str | None = None


class ContactEmailResponse(BaseModel):
    """Email address from API response.

    Attributes:
        email: The email address.
        contact_id: ID of the associated contact.
    """

    model_config = ConfigDict(strict=True)

    email: str
    contact_id: str | None = None


class ContactPhone(BaseModel):
    """Phone number for request payloads (creating/updating contacts).

    Attributes:
        phone_number: The phone number string.
        label: Type label (e.g., "Work", "Mobile", "Home").
        contact_id: ID of the associated contact (set by API).
    """

    model_config = ConfigDict(strict=True)

    phone_number: str
    label: str = "Work"
    contact_id: str | None = None


class ContactPhoneResponse(BaseModel):
    """Phone number from API response.

    Attributes:
        phone_number: The phone number string.
        label: Type label (e.g., "Work", "Mobile", "Home").
        contact_id: ID of the associated contact.
    """

    model_config = ConfigDict(strict=True)

    phone_number: str
    label: str | None = None
    contact_id: str | None = None


class Contact(BaseModel):
    """Dex contact entity returned from GET requests.

    Represents a full contact record as returned by the Dex API.
    All fields except `id` are optional since contacts may have
    partial data.

    Attributes:
        id: Unique contact identifier.
        first_name: Contact's first name.
        last_name: Contact's last name.
        job_title: Professional title or role.
        description: Free-form notes about the contact.
        education: Educational background.
        website: Personal or professional website URL.
        image_url: URL to contact's profile image.
        linkedin: LinkedIn profile URL or username.
        facebook: Facebook profile URL or username.
        twitter: Twitter/X handle.
        instagram: Instagram handle.
        telegram: Telegram username.
        birthday_current_year: Birthday formatted for current year.
        last_seen_at: ISO timestamp of last interaction.
        next_reminder_at: ISO timestamp of next scheduled reminder.
        emails: List of email objects with 'email' key.
        phones: List of phone objects with 'phone_number' and 'label' keys.
    """

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

    # Nested arrays from API response (typed models)
    emails: list[ContactEmailResponse] = Field(default_factory=list)
    phones: list[ContactPhoneResponse] = Field(default_factory=list)


class ContactCreate(BaseModel):
    """Request body for creating a new contact (POST /contacts).

    Use factory methods `with_email()` or `with_phone()` for common patterns.

    Example:
        >>> contact = ContactCreate.with_email(
        ...     "john@example.com",
        ...     first_name="John",
        ...     last_name="Doe"
        ... )
    """

    model_config = ConfigDict(strict=True, extra="forbid")

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

    # Timestamps (accept datetime or str, serialize to ISO string)
    birthday_year: int | None = None
    last_seen_at: str | datetime | None = None
    next_reminder_at: str | datetime | None = None

    # Nested format required by API
    contact_emails: dict[str, dict[str, str]] | None = None
    contact_phone_numbers: dict[str, dict[str, str | None]] | None = None

    @field_serializer("last_seen_at", "next_reminder_at")
    def serialize_timestamps(self, v: str | datetime | None) -> str | None:
        """Serialize datetime to ISO string for JSON."""
        if isinstance(v, datetime):
            return v.isoformat()
        return v

    @classmethod
    def with_email(
        cls,
        email: str,
        first_name: str | None = None,
        last_name: str | None = None,
        **kwargs: str | int | None,
    ) -> "ContactCreate":
        """Create a contact with an email address.

        Args:
            email: Email address for the contact.
            first_name: Contact's first name.
            last_name: Contact's last name.
            **kwargs: Additional contact fields.

        Returns:
            ContactCreate instance ready for API submission.
        """
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
        """Create a contact with a phone number.

        Args:
            phone_number: Phone number string.
            label: Phone type label (default: "Work").
            first_name: Contact's first name.
            last_name: Contact's last name.
            **kwargs: Additional contact fields.

        Returns:
            ContactCreate instance ready for API submission.
        """
        return cls(
            first_name=first_name,
            last_name=last_name,
            contact_phone_numbers={
                "data": {"phone_number": phone_number, "label": label}
            },
            **kwargs,  # type: ignore[arg-type]
        )


class ContactUpdate(BaseModel):
    """Request body for updating an existing contact (PUT /contacts/{id}).

    Attributes:
        contact_id: ID of the contact to update.
        changes: Dictionary of field names to new values.
        update_contact_emails: Set True to replace all emails.
        contact_emails: New email list (only used if update_contact_emails=True).
        update_contact_phone_numbers: Set True to replace all phones.
        contact_phone_numbers: New phone list (only used if above is True).
    """

    model_config = ConfigDict(strict=True, populate_by_name=True, extra="forbid")

    contact_id: str = Field(alias="contactId")
    changes: dict[str, Any] = Field(default_factory=dict)

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
    """Contact reference used in reminder responses and requests.

    Attributes:
        contact_id: The contact's unique identifier.
        email: Alternative lookup by email address.
    """

    model_config = ConfigDict(strict=True)

    contact_id: str | None = None
    email: str | None = None


class Reminder(BaseModel):
    """Dex reminder entity returned from GET requests.

    Attributes:
        id: Unique reminder identifier.
        body: Reminder text content.
        is_complete: Whether the reminder has been completed.
        due_at_date: Due date in YYYY-MM-DD format.
        due_at_time: Due time in HH:MM format.
        contact_ids: List of associated contacts (typed).
    """

    model_config = ConfigDict(strict=True)

    id: str
    body: str
    is_complete: bool = False
    due_at_date: str | None = None
    due_at_time: str | None = None
    contact_ids: list[ReminderContact] = Field(default_factory=list)


class ReminderCreate(BaseModel):
    """Request body for creating a reminder (POST /reminders).

    Use `with_contacts()` factory for linking to specific contacts.

    Example:
        >>> reminder = ReminderCreate.with_contacts(
        ...     text="Follow up on proposal",
        ...     contact_ids=["abc123"],
        ...     due_at_date="2025-01-15"
        ... )
    """

    model_config = ConfigDict(strict=True, extra="forbid")

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
        """Create a reminder linked to specific contacts.

        Args:
            text: Reminder text content.
            contact_ids: List of contact IDs to associate.
            due_at_date: Due date in YYYY-MM-DD format.
            title: Optional reminder title.

        Returns:
            ReminderCreate instance ready for API submission.
        """
        return cls(
            title=title,
            text=text,
            due_at_date=due_at_date,
            reminders_contacts={"data": [{"contact_id": cid} for cid in contact_ids]},
        )


class ReminderUpdate(BaseModel):
    """Request body for updating a reminder (PUT /reminders/{id}).

    Use `mark_complete()` factory for the common completion pattern.

    Attributes:
        reminder_id: ID of the reminder to update (excluded from payload, used in URL).
        changes: Dictionary of field names to new values.
        update_contacts: Set True to replace associated contacts.
        reminders_contacts: New contact list (only used if update_contacts=True).
    """

    model_config = ConfigDict(strict=True, extra="forbid")

    reminder_id: str = Field(exclude=True)
    changes: dict[str, Any] = Field(default_factory=dict)
    update_contacts: bool = False
    reminders_contacts: list[dict[str, str]] = Field(default_factory=list)

    @classmethod
    def mark_complete(cls, reminder_id: str) -> "ReminderUpdate":
        """Create an update to mark a reminder as complete.

        Args:
            reminder_id: ID of the reminder to complete.

        Returns:
            ReminderUpdate instance with is_complete=True.
        """
        return cls(
            reminder_id=reminder_id,
            changes={"is_complete": True},
        )


# =============================================================================
# Note (Timeline Item) Models
# =============================================================================


class NoteContact(BaseModel):
    """Contact reference in note responses.

    Attributes:
        contact_id: The contact's unique identifier.
    """

    model_config = ConfigDict(strict=True)

    contact_id: str


class Note(BaseModel):
    """Dex note/timeline item entity returned from GET requests.

    Notes are timeline entries that record interactions or information
    about contacts.

    Attributes:
        id: Unique note identifier.
        note: Note text content.
        event_time: When the event occurred (ISO string from API).
        contacts: List of associated contacts (typed).
    """

    model_config = ConfigDict(strict=True)

    id: str
    note: str
    event_time: str | None = None
    contacts: list[NoteContact] = Field(default_factory=list)


class NoteCreate(BaseModel):
    """Request body for creating a note (POST /timeline_items).

    Use `with_contacts()` factory for linking to specific contacts.

    Example:
        >>> note = NoteCreate.with_contacts(
        ...     note="Met at conference",
        ...     contact_ids=["abc123", "def456"]
        ... )
    """

    model_config = ConfigDict(strict=True, extra="forbid")

    note: str
    event_time: str | datetime | None = None
    meeting_type: str = "note"
    timeline_items_contacts: dict[str, list[dict[str, str]]] | None = None

    @field_serializer("event_time")
    def serialize_event_time(self, v: str | datetime | None) -> str | None:
        """Serialize datetime to ISO string for JSON."""
        if isinstance(v, datetime):
            return v.isoformat()
        return v

    @classmethod
    def with_contacts(
        cls,
        note: str,
        contact_ids: list[str],
        event_time: str | datetime | None = None,
    ) -> "NoteCreate":
        """Create a note linked to specific contacts.

        Args:
            note: Note text content.
            contact_ids: List of contact IDs to associate.
            event_time: ISO timestamp for timeline ordering.

        Returns:
            NoteCreate instance ready for API submission.
        """
        return cls(
            note=note,
            event_time=event_time,
            timeline_items_contacts={
                "data": [{"contact_id": cid} for cid in contact_ids]
            },
        )


class NoteUpdate(BaseModel):
    """Request body for updating a note (PUT /timeline_items/{id}).

    Attributes:
        note_id: ID of the note to update (excluded from payload, used in URL).
        changes: Dictionary of field names to new values.
        update_contacts: Set True to replace associated contacts.
        timeline_items_contacts: New contact list (only used if above is True).
    """

    model_config = ConfigDict(strict=True, extra="forbid")

    note_id: str = Field(exclude=True)
    changes: dict[str, Any] = Field(default_factory=dict)
    update_contacts: bool = False
    timeline_items_contacts: list[dict[str, str]] = Field(default_factory=list)


# =============================================================================
# Pagination Response Models
# =============================================================================


class PaginatedContacts(BaseModel):
    """Paginated response wrapper for contact list queries.

    Attributes:
        contacts: List of contact dictionaries for this page.
        total: Total number of contacts matching the query.
        limit: Maximum results per page.
        offset: Number of results skipped.

    Example:
        >>> result = client.get_contacts(limit=10)
        >>> while result.has_more:
        ...     result = client.get_contacts(limit=10, offset=result.offset + 10)
    """

    model_config = ConfigDict(strict=True)

    contacts: list[dict[str, Any]]
    total: int
    limit: int = 100
    offset: int = 0

    @property
    def has_more(self) -> bool:
        """Check if there are more results available beyond this page."""
        return self.offset + len(self.contacts) < self.total


class PaginatedReminders(BaseModel):
    """Paginated response wrapper for reminder list queries.

    Attributes:
        reminders: List of reminder dictionaries for this page.
        total: Total number of reminders matching the query.
        limit: Maximum results per page.
        offset: Number of results skipped.
    """

    model_config = ConfigDict(strict=True)

    reminders: list[dict[str, Any]]
    total: int
    limit: int = 100
    offset: int = 0

    @property
    def has_more(self) -> bool:
        """Check if there are more results available beyond this page."""
        return self.offset + len(self.reminders) < self.total


class PaginatedNotes(BaseModel):
    """Paginated response wrapper for note list queries.

    Attributes:
        notes: List of note dictionaries for this page.
        total: Total number of notes matching the query.
        limit: Maximum results per page.
        offset: Number of results skipped.
    """

    model_config = ConfigDict(strict=True)

    notes: list[dict[str, Any]]
    total: int
    limit: int = 100
    offset: int = 0

    @property
    def has_more(self) -> bool:
        """Check if there are more results available beyond this page."""
        return self.offset + len(self.notes) < self.total


# =============================================================================
# API Response Extractors
# =============================================================================


def extract_contacts_total(data: dict[str, Any]) -> int:
    """Extract total count from contacts/notes pagination response.

    The Dex API nests the count in: pagination.total.count

    Args:
        data: Raw API response dictionary.

    Returns:
        Total count, or 0 if not found.
    """
    pagination = data.get("pagination", {})
    if isinstance(pagination, dict):
        total = pagination.get("total", {})
        if isinstance(total, dict):
            count = total.get("count", 0)
            if isinstance(count, int):
                return count
    return 0


def extract_reminders_total(data: dict[str, Any]) -> int:
    """Extract total count from reminders pagination response.

    The Dex API nests the count in: total.aggregate.count

    Args:
        data: Raw API response dictionary.

    Returns:
        Total count, or 0 if not found.
    """
    total = data.get("total", {})
    if isinstance(total, dict):
        aggregate = total.get("aggregate", {})
        if isinstance(aggregate, dict):
            count = aggregate.get("count", 0)
            if isinstance(count, int):
                return count
    return 0


def extract_contact_entity(data: dict[str, Any]) -> dict[str, Any]:
    """Extract contact entity from create/update/delete response.

    API responses wrap entities in operation-specific keys.
    This function unwraps them for consistent handling.

    Args:
        data: Raw API response dictionary.

    Returns:
        The unwrapped contact entity, or original data if no wrapper found.
    """
    keys = ["insert_contacts_one", "update_contacts_by_pk", "delete_contacts_by_pk"]
    for key in keys:
        entity = data.get(key)
        if isinstance(entity, dict):
            return entity
    return data


def extract_reminder_entity(data: dict[str, Any]) -> dict[str, Any]:
    """Extract reminder entity from create/update/delete response.

    Args:
        data: Raw API response dictionary.

    Returns:
        The unwrapped reminder entity, or original data if no wrapper found.
    """
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
    """Extract note entity from create/update/delete response.

    Args:
        data: Raw API response dictionary.

    Returns:
        The unwrapped note entity, or original data if no wrapper found.
    """
    for key in [
        "insert_timeline_items_one",
        "update_timeline_items_by_pk",
        "delete_timeline_items_by_pk",
    ]:
        entity = data.get(key)
        if isinstance(entity, dict):
            return entity
    return data
