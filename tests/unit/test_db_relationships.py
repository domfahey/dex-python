"""Tests for SQLAlchemy ORM model relationships and constraints.

Tests cascade behaviors, foreign key constraints, and model relationships.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from dex_python.db.models import (
    Base,
    Contact,
    Email,
    Note,
    NoteContact,
    Phone,
    Reminder,
    ReminderContact,
)


@pytest.fixture
def engine():
    """Create an in-memory SQLite engine."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return engine


@pytest.fixture
def session(engine):
    """Create a database session."""
    with Session(engine) as session:
        yield session


class TestContactRelationships:
    """Test Contact model relationships."""

    def test_contact_has_emails_relationship(self, session: Session) -> None:
        """Contact should have emails relationship."""
        contact = Contact(id="c1", first_name="John", last_name="Doe")
        email = Email(email="john@example.com", contact=contact)
        session.add(contact)
        session.commit()

        loaded = session.get(Contact, "c1")
        assert len(loaded.emails) == 1
        assert loaded.emails[0].email == "john@example.com"

    def test_contact_has_phones_relationship(self, session: Session) -> None:
        """Contact should have phones relationship."""
        contact = Contact(id="c1", first_name="John")
        phone = Phone(phone_number="555-1234", label="Work", contact=contact)
        session.add(contact)
        session.commit()

        loaded = session.get(Contact, "c1")
        assert len(loaded.phones) == 1
        assert loaded.phones[0].phone_number == "555-1234"

    def test_contact_can_have_multiple_emails(self, session: Session) -> None:
        """Contact can have multiple email addresses."""
        contact = Contact(id="c1", first_name="John")
        contact.emails = [
            Email(email="john@work.com"),
            Email(email="john@personal.com"),
            Email(email="john@other.com"),
        ]
        session.add(contact)
        session.commit()

        loaded = session.get(Contact, "c1")
        assert len(loaded.emails) == 3

    def test_contact_can_have_multiple_phones(self, session: Session) -> None:
        """Contact can have multiple phone numbers."""
        contact = Contact(id="c1", first_name="John")
        contact.phones = [
            Phone(phone_number="555-1111", label="Work"),
            Phone(phone_number="555-2222", label="Mobile"),
        ]
        session.add(contact)
        session.commit()

        loaded = session.get(Contact, "c1")
        assert len(loaded.phones) == 2


class TestCascadeDelete:
    """Test cascade delete behaviors."""

    def test_delete_contact_cascades_to_emails(self, session: Session) -> None:
        """Deleting contact should delete associated emails."""
        contact = Contact(id="c1", first_name="John")
        contact.emails = [
            Email(email="john@example.com"),
            Email(email="john@work.com"),
        ]
        session.add(contact)
        session.commit()

        # Verify emails exist
        assert session.query(Email).count() == 2

        # Delete contact
        session.delete(contact)
        session.commit()

        # Emails should be deleted
        assert session.query(Email).count() == 0

    def test_delete_contact_cascades_to_phones(self, session: Session) -> None:
        """Deleting contact should delete associated phones."""
        contact = Contact(id="c1", first_name="John")
        contact.phones = [Phone(phone_number="555-1234", label="Work")]
        session.add(contact)
        session.commit()

        assert session.query(Phone).count() == 1

        session.delete(contact)
        session.commit()

        assert session.query(Phone).count() == 0

    def test_delete_orphan_emails(self, session: Session) -> None:
        """Removing email from contact should delete the email."""
        contact = Contact(id="c1", first_name="John")
        email = Email(email="john@example.com")
        contact.emails.append(email)
        session.add(contact)
        session.commit()

        assert session.query(Email).count() == 1

        # Remove email from contact
        contact.emails.remove(email)
        session.commit()

        # Email should be deleted (delete-orphan cascade)
        assert session.query(Email).count() == 0

    def test_delete_orphan_phones(self, session: Session) -> None:
        """Removing phone from contact should delete the phone."""
        contact = Contact(id="c1", first_name="John")
        phone = Phone(phone_number="555-1234")
        contact.phones.append(phone)
        session.add(contact)
        session.commit()

        assert session.query(Phone).count() == 1

        contact.phones.remove(phone)
        session.commit()

        assert session.query(Phone).count() == 0


class TestEmailModel:
    """Test Email model."""

    def test_email_with_contact(self, session: Session) -> None:
        """Email should reference its contact."""
        contact = Contact(id="c1", first_name="John")
        email = Email(email="john@example.com", contact=contact)
        session.add(contact)
        session.commit()

        loaded_email = session.query(Email).first()
        assert loaded_email.contact_id == "c1"
        assert loaded_email.contact.first_name == "John"

    def test_email_without_contact(self, session: Session) -> None:
        """Email can exist without contact (nullable FK)."""
        email = Email(email="orphan@example.com")
        session.add(email)
        session.commit()

        assert email.contact_id is None
        assert email.contact is None


class TestPhoneModel:
    """Test Phone model."""

    def test_phone_with_label(self, session: Session) -> None:
        """Phone should store label."""
        contact = Contact(id="c1", first_name="John")
        phone = Phone(phone_number="555-1234", label="Mobile", contact=contact)
        session.add(contact)
        session.commit()

        loaded = session.query(Phone).first()
        assert loaded.label == "Mobile"

    def test_phone_without_label(self, session: Session) -> None:
        """Phone can exist without label."""
        contact = Contact(id="c1", first_name="John")
        phone = Phone(phone_number="555-1234", contact=contact)
        session.add(contact)
        session.commit()

        loaded = session.query(Phone).first()
        assert loaded.label is None


class TestReminderModel:
    """Test Reminder model."""

    def test_create_reminder(self, session: Session) -> None:
        """Reminder should be creatable."""
        reminder = Reminder(id="rem1", body="Call John", is_complete=False)
        session.add(reminder)
        session.commit()

        loaded = session.get(Reminder, "rem1")
        assert loaded.body == "Call John"
        assert loaded.is_complete is False

    def test_reminder_with_due_date(self, session: Session) -> None:
        """Reminder should store due date."""
        reminder = Reminder(id="rem1", body="Test", due_date="2025-01-15")
        session.add(reminder)
        session.commit()

        loaded = session.get(Reminder, "rem1")
        assert loaded.due_date == "2025-01-15"

    def test_reminder_full_data_json(self, session: Session) -> None:
        """Reminder should store full_data as JSON."""
        reminder = Reminder(
            id="rem1",
            body="Test",
            full_data={"title": "Important", "priority": 1},
        )
        session.add(reminder)
        session.commit()

        loaded = session.get(Reminder, "rem1")
        assert loaded.full_data["title"] == "Important"
        assert loaded.full_data["priority"] == 1


class TestReminderContactLink:
    """Test ReminderContact many-to-many link."""

    def test_link_reminder_to_contact(self, session: Session) -> None:
        """ReminderContact should link reminder and contact."""
        contact = Contact(id="c1", first_name="John")
        reminder = Reminder(id="rem1", body="Call John")
        link = ReminderContact(reminder_id="rem1", contact_id="c1")

        session.add_all([contact, reminder, link])
        session.commit()

        loaded_link = session.query(ReminderContact).first()
        assert loaded_link.reminder_id == "rem1"
        assert loaded_link.contact_id == "c1"

    def test_reminder_can_link_multiple_contacts(self, session: Session) -> None:
        """Reminder can be linked to multiple contacts."""
        contact1 = Contact(id="c1", first_name="John")
        contact2 = Contact(id="c2", first_name="Jane")
        reminder = Reminder(id="rem1", body="Team meeting")

        session.add_all([contact1, contact2, reminder])
        session.add(ReminderContact(reminder_id="rem1", contact_id="c1"))
        session.add(ReminderContact(reminder_id="rem1", contact_id="c2"))
        session.commit()

        links = session.query(ReminderContact).filter_by(reminder_id="rem1").all()
        assert len(links) == 2


class TestNoteModel:
    """Test Note model."""

    def test_create_note(self, session: Session) -> None:
        """Note should be creatable."""
        note = Note(id="note1", note="Meeting notes")
        session.add(note)
        session.commit()

        loaded = session.get(Note, "note1")
        assert loaded.note == "Meeting notes"

    def test_note_with_event_time(self, session: Session) -> None:
        """Note should store event_time."""
        from datetime import datetime

        event_time = datetime(2025, 1, 15, 10, 30, 0)
        note = Note(id="note1", note="Test", event_time=event_time)
        session.add(note)
        session.commit()

        loaded = session.get(Note, "note1")
        assert loaded.event_time == event_time

    def test_note_full_data_json(self, session: Session) -> None:
        """Note should store full_data as JSON."""
        note = Note(
            id="note1",
            note="Test",
            full_data={"type": "meeting", "attendees": ["John", "Jane"]},
        )
        session.add(note)
        session.commit()

        loaded = session.get(Note, "note1")
        assert loaded.full_data["type"] == "meeting"
        assert len(loaded.full_data["attendees"]) == 2


class TestNoteContactLink:
    """Test NoteContact many-to-many link."""

    def test_link_note_to_contact(self, session: Session) -> None:
        """NoteContact should link note and contact."""
        contact = Contact(id="c1", first_name="John")
        note = Note(id="note1", note="Discussed project")
        link = NoteContact(note_id="note1", contact_id="c1")

        session.add_all([contact, note, link])
        session.commit()

        loaded_link = session.query(NoteContact).first()
        assert loaded_link.note_id == "note1"
        assert loaded_link.contact_id == "c1"

    def test_note_can_link_multiple_contacts(self, session: Session) -> None:
        """Note can be linked to multiple contacts."""
        contact1 = Contact(id="c1", first_name="John")
        contact2 = Contact(id="c2", first_name="Jane")
        note = Note(id="note1", note="Group discussion")

        session.add_all([contact1, contact2, note])
        session.add(NoteContact(note_id="note1", contact_id="c1"))
        session.add(NoteContact(note_id="note1", contact_id="c2"))
        session.commit()

        links = session.query(NoteContact).filter_by(note_id="note1").all()
        assert len(links) == 2


class TestContactFields:
    """Test Contact model fields."""

    def test_contact_all_fields(self, session: Session) -> None:
        """Contact should store all fields correctly."""
        contact = Contact(
            id="c1",
            first_name="John",
            last_name="Doe",
            job_title="Engineer",
            linkedin="johndoe",
            website="https://johndoe.com",
            duplicate_group_id="group1",
            duplicate_resolution="keep",
            primary_contact_id="c1",
            company="Acme Inc",
            role="Senior Engineer",
        )
        session.add(contact)
        session.commit()

        loaded = session.get(Contact, "c1")
        assert loaded.first_name == "John"
        assert loaded.last_name == "Doe"
        assert loaded.job_title == "Engineer"
        assert loaded.linkedin == "johndoe"
        assert loaded.website == "https://johndoe.com"
        assert loaded.duplicate_group_id == "group1"
        assert loaded.company == "Acme Inc"
        assert loaded.role == "Senior Engineer"

    def test_contact_full_data_json(self, session: Session) -> None:
        """Contact should store full_data as JSON."""
        contact = Contact(
            id="c1",
            first_name="John",
            full_data={
                "birthday": "1990-05-15",
                "notes": "VIP customer",
                "tags": ["vip", "enterprise"],
            },
        )
        session.add(contact)
        session.commit()

        loaded = session.get(Contact, "c1")
        assert loaded.full_data["birthday"] == "1990-05-15"
        assert "vip" in loaded.full_data["tags"]

    def test_contact_name_parsed_json(self, session: Session) -> None:
        """Contact should store name_parsed as JSON."""
        contact = Contact(
            id="c1",
            first_name="John",
            name_given="John",
            name_surname="Doe",
            name_parsed={"title": "Dr.", "suffix": "Jr."},
        )
        session.add(contact)
        session.commit()

        loaded = session.get(Contact, "c1")
        assert loaded.name_parsed["title"] == "Dr."
        assert loaded.name_parsed["suffix"] == "Jr."


class TestIndexes:
    """Test that indexes are created correctly."""

    def test_contacts_name_index_exists(self, engine) -> None:
        """Contact name index should exist."""
        from sqlalchemy import inspect

        inspector = inspect(engine)
        indexes = inspector.get_indexes("contacts")
        index_names = [idx["name"] for idx in indexes]

        assert "idx_contacts_name" in index_names

    def test_emails_contact_id_index_exists(self, engine) -> None:
        """Email contact_id index should exist."""
        from sqlalchemy import inspect

        inspector = inspect(engine)
        indexes = inspector.get_indexes("emails")
        index_names = [idx["name"] for idx in indexes]

        assert "idx_emails_contact_id" in index_names

    def test_phones_indexes_exist(self, engine) -> None:
        """Phone indexes should exist."""
        from sqlalchemy import inspect

        inspector = inspect(engine)
        indexes = inspector.get_indexes("phones")
        index_names = [idx["name"] for idx in indexes]

        assert "idx_phones_contact_id" in index_names
        assert "idx_phones_number" in index_names
