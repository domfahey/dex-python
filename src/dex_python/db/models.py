"""SQLAlchemy ORM models matching current database schema.

These models mirror the schema defined in scripts/sync_with_integrity.py
and are designed for use with Alembic migrations.
"""

from datetime import datetime
from typing import Any, Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""

    pass


class Contact(Base):
    """Contact entity matching existing schema."""

    __tablename__ = "contacts"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    first_name: Mapped[Optional[str]] = mapped_column(Text)
    last_name: Mapped[Optional[str]] = mapped_column(Text)
    job_title: Mapped[Optional[str]] = mapped_column(Text)
    linkedin: Mapped[Optional[str]] = mapped_column(Text)
    website: Mapped[Optional[str]] = mapped_column(Text)
    full_data: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON)
    record_hash: Mapped[Optional[str]] = mapped_column(Text)
    last_synced_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # Deduplication metadata
    duplicate_group_id: Mapped[Optional[str]] = mapped_column(Text)
    duplicate_resolution: Mapped[Optional[str]] = mapped_column(Text)
    primary_contact_id: Mapped[Optional[str]] = mapped_column(Text)

    # Name parsing columns
    name_given: Mapped[Optional[str]] = mapped_column(Text)
    name_surname: Mapped[Optional[str]] = mapped_column(Text)
    name_parsed: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON)

    # Enrichment columns
    company: Mapped[Optional[str]] = mapped_column(Text)
    role: Mapped[Optional[str]] = mapped_column(Text)

    # Relationships
    emails: Mapped[list["Email"]] = relationship(
        back_populates="contact", cascade="all, delete-orphan"
    )
    phones: Mapped[list["Phone"]] = relationship(
        back_populates="contact", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_contacts_name", "first_name", "last_name"),
        Index("idx_contacts_job_title", "job_title"),
        Index("idx_contacts_hash", "record_hash"),
        Index("idx_contacts_duplicate_group", "duplicate_group_id"),
        Index("idx_contacts_linkedin", "linkedin"),
        Index("idx_contacts_website", "website"),
    )


class Email(Base):
    """Email entity with FK to contact."""

    __tablename__ = "emails"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    contact_id: Mapped[Optional[str]] = mapped_column(
        String, ForeignKey("contacts.id", ondelete="CASCADE")
    )
    email: Mapped[Optional[str]] = mapped_column(Text)

    contact: Mapped[Optional["Contact"]] = relationship(back_populates="emails")

    __table_args__ = (Index("idx_emails_contact_id", "contact_id"),)


class Phone(Base):
    """Phone entity with FK to contact."""

    __tablename__ = "phones"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    contact_id: Mapped[Optional[str]] = mapped_column(
        String, ForeignKey("contacts.id", ondelete="CASCADE")
    )
    phone_number: Mapped[Optional[str]] = mapped_column(Text)
    label: Mapped[Optional[str]] = mapped_column(Text)

    contact: Mapped[Optional["Contact"]] = relationship(back_populates="phones")

    __table_args__ = (
        Index("idx_phones_contact_id", "contact_id"),
        Index("idx_phones_number", "phone_number"),
    )


class Reminder(Base):
    """Reminder entity."""

    __tablename__ = "reminders"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    body: Mapped[Optional[str]] = mapped_column(Text)
    is_complete: Mapped[Optional[bool]] = mapped_column(Boolean)
    due_date: Mapped[Optional[str]] = mapped_column(Text)
    full_data: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON)
    record_hash: Mapped[Optional[str]] = mapped_column(Text)
    last_synced_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    __table_args__ = (Index("idx_reminders_hash", "record_hash"),)


class ReminderContact(Base):
    """Many-to-many link between reminders and contacts."""

    __tablename__ = "reminder_contacts"

    reminder_id: Mapped[str] = mapped_column(
        String, ForeignKey("reminders.id", ondelete="CASCADE"), primary_key=True
    )
    contact_id: Mapped[str] = mapped_column(
        String, ForeignKey("contacts.id", ondelete="CASCADE"), primary_key=True
    )

    __table_args__ = (
        Index("idx_reminder_contacts_reminder", "reminder_id"),
        Index("idx_reminder_contacts_contact", "contact_id"),
    )


class Note(Base):
    """Note/timeline item entity."""

    __tablename__ = "notes"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    note: Mapped[Optional[str]] = mapped_column(Text)
    event_time: Mapped[Optional[datetime]] = mapped_column(DateTime)
    full_data: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON)
    record_hash: Mapped[Optional[str]] = mapped_column(Text)
    last_synced_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    __table_args__ = (Index("idx_notes_hash", "record_hash"),)


class NoteContact(Base):
    """Many-to-many link between notes and contacts."""

    __tablename__ = "note_contacts"

    note_id: Mapped[str] = mapped_column(
        String, ForeignKey("notes.id", ondelete="CASCADE"), primary_key=True
    )
    contact_id: Mapped[str] = mapped_column(
        String, ForeignKey("contacts.id", ondelete="CASCADE"), primary_key=True
    )

    __table_args__ = (
        Index("idx_note_contacts_note", "note_id"),
        Index("idx_note_contacts_contact", "contact_id"),
    )
