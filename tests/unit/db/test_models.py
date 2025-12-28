"""Tests for SQLAlchemy models matching current schema.

TDD tests ensuring SQLAlchemy models produce identical schema to raw SQL.
"""

import pytest
from sqlalchemy import create_engine, inspect


class TestContactModel:
    """Test Contact SQLAlchemy model."""

    def test_contacts_table_columns(self):
        """Contact model has all expected columns."""
        from dex_python.db.models import Base

        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)

        inspector = inspect(engine)
        columns = {col["name"] for col in inspector.get_columns("contacts")}

        # All columns from current schema
        expected = {
            "id",
            "first_name",
            "last_name",
            "job_title",
            "linkedin",
            "website",
            "full_data",
            "record_hash",
            "last_synced_at",
            "duplicate_group_id",
            "duplicate_resolution",
            "primary_contact_id",
            "name_given",
            "name_surname",
            "name_parsed",
            "company",
            "role",
        }
        assert expected.issubset(columns)

    def test_contacts_primary_key(self):
        """Contact primary key is 'id' column."""
        from dex_python.db.models import Base

        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)

        inspector = inspect(engine)
        pk = inspector.get_pk_constraint("contacts")
        assert pk["constrained_columns"] == ["id"]


class TestEmailModel:
    """Test Email SQLAlchemy model."""

    def test_emails_table_columns(self):
        """Email model has expected columns."""
        from dex_python.db.models import Base

        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)

        inspector = inspect(engine)
        columns = {col["name"] for col in inspector.get_columns("emails")}

        expected = {"id", "contact_id", "email"}
        assert expected.issubset(columns)

    def test_emails_foreign_key_to_contacts(self):
        """Email table has FK to contacts.id."""
        from dex_python.db.models import Base

        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)

        inspector = inspect(engine)
        fks = inspector.get_foreign_keys("emails")
        assert len(fks) == 1
        assert fks[0]["referred_table"] == "contacts"
        assert fks[0]["referred_columns"] == ["id"]


class TestPhoneModel:
    """Test Phone SQLAlchemy model."""

    def test_phones_table_columns(self):
        """Phone model has expected columns."""
        from dex_python.db.models import Base

        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)

        inspector = inspect(engine)
        columns = {col["name"] for col in inspector.get_columns("phones")}

        expected = {"id", "contact_id", "phone_number", "label"}
        assert expected.issubset(columns)

    def test_phones_foreign_key_to_contacts(self):
        """Phone table has FK to contacts.id."""
        from dex_python.db.models import Base

        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)

        inspector = inspect(engine)
        fks = inspector.get_foreign_keys("phones")
        assert len(fks) == 1
        assert fks[0]["referred_table"] == "contacts"


class TestReminderModel:
    """Test Reminder SQLAlchemy model."""

    def test_reminders_table_columns(self):
        """Reminder model has expected columns."""
        from dex_python.db.models import Base

        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)

        inspector = inspect(engine)
        columns = {col["name"] for col in inspector.get_columns("reminders")}

        expected = {
            "id",
            "body",
            "is_complete",
            "due_date",
            "full_data",
            "record_hash",
            "last_synced_at",
        }
        assert expected.issubset(columns)


class TestNoteModel:
    """Test Note SQLAlchemy model."""

    def test_notes_table_columns(self):
        """Note model has expected columns."""
        from dex_python.db.models import Base

        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)

        inspector = inspect(engine)
        columns = {col["name"] for col in inspector.get_columns("notes")}

        expected = {
            "id",
            "note",
            "event_time",
            "full_data",
            "record_hash",
            "last_synced_at",
        }
        assert expected.issubset(columns)


class TestLinkTables:
    """Test many-to-many link tables."""

    def test_reminder_contacts_composite_pk(self):
        """reminder_contacts has composite PK (reminder_id, contact_id)."""
        from dex_python.db.models import Base

        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)

        inspector = inspect(engine)
        pk = inspector.get_pk_constraint("reminder_contacts")
        assert set(pk["constrained_columns"]) == {"reminder_id", "contact_id"}

    def test_note_contacts_composite_pk(self):
        """note_contacts has composite PK (note_id, contact_id)."""
        from dex_python.db.models import Base

        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)

        inspector = inspect(engine)
        pk = inspector.get_pk_constraint("note_contacts")
        assert set(pk["constrained_columns"]) == {"note_id", "contact_id"}


class TestIndexes:
    """Test that required indexes are created."""

    def test_contact_indexes_exist(self):
        """Contact table has required indexes."""
        from dex_python.db.models import Base

        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)

        inspector = inspect(engine)
        indexes = inspector.get_indexes("contacts")
        index_names = {idx["name"] for idx in indexes}

        # Key indexes for performance
        expected = {
            "idx_contacts_name",
            "idx_contacts_job_title",
            "idx_contacts_hash",
            "idx_contacts_duplicate_group",
            "idx_contacts_linkedin",
            "idx_contacts_website",
        }
        assert expected.issubset(index_names)

    def test_email_indexes_exist(self):
        """Email table has required indexes."""
        from dex_python.db.models import Base

        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)

        inspector = inspect(engine)
        indexes = inspector.get_indexes("emails")
        index_names = {idx["name"] for idx in indexes}

        assert "idx_emails_contact_id" in index_names

    def test_phone_indexes_exist(self):
        """Phone table has required indexes."""
        from dex_python.db.models import Base

        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)

        inspector = inspect(engine)
        indexes = inspector.get_indexes("phones")

        expected = {"idx_phones_contact_id", "idx_phones_number"}
        assert expected.issubset(index_names)


class TestORMRelationships:
    """Test SQLAlchemy ORM relationships and operations."""

    def test_contact_emails_relationship(self):
        """Contact should have working relationship with emails."""
        from dex_python.db.models import Base, Contact, Email
        from dex_python.db.session import get_engine, get_session

        engine = get_engine(":memory:")
        Base.metadata.create_all(engine)
        session = get_session(":memory:")
        Base.metadata.create_all(session.bind)

        contact = Contact(id="c1", first_name="John", last_name="Doe")
        email1 = Email(contact_id="c1", email="john@example.com")
        email2 = Email(contact_id="c1", email="john.doe@work.com")

        session.add(contact)
        session.add(email1)
        session.add(email2)
        session.commit()

        retrieved = session.query(Contact).filter_by(id="c1").first()
        assert len(retrieved.emails) == 2
        assert any(e.email == "john@example.com" for e in retrieved.emails)
        session.close()

    def test_contact_phones_relationship(self):
        """Contact should have working relationship with phones."""
        from dex_python.db.models import Base, Contact, Phone
        from dex_python.db.session import get_engine, get_session

        engine = get_engine(":memory:")
        Base.metadata.create_all(engine)
        session = get_session(":memory:")
        Base.metadata.create_all(session.bind)

        contact = Contact(id="c1", first_name="Jane", last_name="Smith")
        phone1 = Phone(contact_id="c1", phone_number="555-1234", label="Work")
        phone2 = Phone(contact_id="c1", phone_number="555-5678", label="Mobile")

        session.add(contact)
        session.add(phone1)
        session.add(phone2)
        session.commit()

        retrieved = session.query(Contact).filter_by(id="c1").first()
        assert len(retrieved.phones) == 2
        assert any(p.phone_number == "555-1234" for p in retrieved.phones)
        session.close()

    def test_cascade_delete_emails(self):
        """Deleting contact should cascade delete emails."""
        from dex_python.db.models import Base, Contact, Email
        from dex_python.db.session import get_engine, get_session

        engine = get_engine(":memory:")
        Base.metadata.create_all(engine)
        session = get_session(":memory:")
        Base.metadata.create_all(session.bind)

        contact = Contact(id="c1", first_name="Test", last_name="User")
        email = Email(contact_id="c1", email="test@example.com")

        session.add(contact)
        session.add(email)
        session.commit()

        # Delete contact
        session.delete(contact)
        session.commit()

        # Email should be deleted too
        remaining_emails = session.query(Email).filter_by(contact_id="c1").all()
        assert len(remaining_emails) == 0
        session.close()

    def test_cascade_delete_phones(self):
        """Deleting contact should cascade delete phones."""
        from dex_python.db.models import Base, Contact, Phone
        from dex_python.db.session import get_engine, get_session

        engine = get_engine(":memory:")
        Base.metadata.create_all(engine)
        session = get_session(":memory:")
        Base.metadata.create_all(session.bind)

        contact = Contact(id="c1", first_name="Test", last_name="User")
        phone = Phone(contact_id="c1", phone_number="555-0000")

        session.add(contact)
        session.add(phone)
        session.commit()

        # Delete contact
        session.delete(contact)
        session.commit()

        # Phone should be deleted too
        remaining_phones = session.query(Phone).filter_by(contact_id="c1").all()
        assert len(remaining_phones) == 0
        session.close()

    def test_contact_with_json_fields(self):
        """Contact JSON fields should serialize/deserialize correctly."""
        from dex_python.db.models import Base, Contact
        from dex_python.db.session import get_engine, get_session

        engine = get_engine(":memory:")
        Base.metadata.create_all(engine)
        session = get_session(":memory:")
        Base.metadata.create_all(session.bind)

        full_data = {"key": "value", "nested": {"a": 1}}
        name_parsed = {"given": "John", "surname": "Doe"}

        contact = Contact(
            id="c1",
            first_name="John",
            full_data=full_data,
            name_parsed=name_parsed,
        )

        session.add(contact)
        session.commit()

        retrieved = session.query(Contact).filter_by(id="c1").first()
        assert retrieved.full_data == full_data
        assert retrieved.name_parsed == name_parsed
        session.close()

    def test_reminder_with_full_data(self):
        """Reminder JSON fields should work correctly."""
        from dex_python.db.models import Base, Reminder
        from dex_python.db.session import get_engine, get_session

        engine = get_engine(":memory:")
        Base.metadata.create_all(engine)
        session = get_session(":memory:")
        Base.metadata.create_all(session.bind)

        full_data = {"priority": "high", "tags": ["work", "urgent"]}
        reminder = Reminder(
            id="r1",
            body="Test reminder",
            is_complete=False,
            due_date="2024-12-31",
            full_data=full_data,
        )

        session.add(reminder)
        session.commit()

        retrieved = session.query(Reminder).filter_by(id="r1").first()
        assert retrieved.full_data == full_data
        assert retrieved.is_complete is False
        session.close()

    def test_note_with_datetime(self):
        """Note event_time should handle datetime correctly."""
        from datetime import datetime

        from dex_python.db.models import Base, Note
        from dex_python.db.session import get_engine, get_session

        engine = get_engine(":memory:")
        Base.metadata.create_all(engine)
        session = get_session(":memory:")
        Base.metadata.create_all(session.bind)

        event_time = datetime(2024, 1, 15, 10, 30, 0)
        note = Note(id="n1", note="Test note", event_time=event_time)

        session.add(note)
        session.commit()

        retrieved = session.query(Note).filter_by(id="n1").first()
        assert retrieved.event_time == event_time
        session.close()

    def test_cascade_delete_reminder_contacts(self):
        """Deleting reminder should cascade delete link table entries."""
        from dex_python.db.models import Base, Contact, Reminder, ReminderContact
        from dex_python.db.session import get_engine, get_session

        engine = get_engine(":memory:")
        Base.metadata.create_all(engine)
        session = get_session(":memory:")
        Base.metadata.create_all(session.bind)

        contact = Contact(id="c1", first_name="Test")
        reminder = Reminder(id="r1", body="Test reminder")
        link = ReminderContact(reminder_id="r1", contact_id="c1")

        session.add(contact)
        session.add(reminder)
        session.add(link)
        session.commit()

        # Delete reminder
        session.delete(reminder)
        session.commit()

        # Link should be deleted too
        remaining_links = (
            session.query(ReminderContact).filter_by(reminder_id="r1").all()
        )
        assert len(remaining_links) == 0
        session.close()

    def test_cascade_delete_note_contacts(self):
        """Deleting note should cascade delete link table entries."""
        from dex_python.db.models import Base, Contact, Note, NoteContact
        from dex_python.db.session import get_engine, get_session

        engine = get_engine(":memory:")
        Base.metadata.create_all(engine)
        session = get_session(":memory:")
        Base.metadata.create_all(session.bind)

        contact = Contact(id="c1", first_name="Test")
        note = Note(id="n1", note="Test note")
        link = NoteContact(note_id="n1", contact_id="c1")

        session.add(contact)
        session.add(note)
        session.add(link)
        session.commit()

        # Delete note
        session.delete(note)
        session.commit()

        # Link should be deleted too
        remaining_links = session.query(NoteContact).filter_by(note_id="n1").all()
        assert len(remaining_links) == 0
        session.close()

    def test_contact_optional_fields_are_nullable(self):
        """Contact optional fields should accept None."""
        from dex_python.db.models import Base, Contact
        from dex_python.db.session import get_engine, get_session

        engine = get_engine(":memory:")
        Base.metadata.create_all(engine)
        session = get_session(":memory:")
        Base.metadata.create_all(session.bind)

        # Create contact with only required field (id)
        contact = Contact(
            id="c1",
            first_name=None,
            last_name=None,
            job_title=None,
            linkedin=None,
        )

        session.add(contact)
        session.commit()

        retrieved = session.query(Contact).filter_by(id="c1").first()
        assert retrieved.first_name is None
        assert retrieved.job_title is None
        session.close()

    def test_email_label_is_optional(self):
        """Email label should be optional (phones have labels, emails don't typically)."""
        from dex_python.db.models import Base, Contact, Email
        from dex_python.db.session import get_engine, get_session

        engine = get_engine(":memory:")
        Base.metadata.create_all(engine)
        session = get_session(":memory:")
        Base.metadata.create_all(session.bind)

        contact = Contact(id="c1", first_name="Test")
        email = Email(contact_id="c1", email="test@example.com")

        session.add(contact)
        session.add(email)
        session.commit()

        retrieved = session.query(Email).filter_by(contact_id="c1").first()
        assert retrieved.email == "test@example.com"
        session.close()

    def test_phone_with_label(self):
        """Phone should support label field."""
        from dex_python.db.models import Base, Contact, Phone
        from dex_python.db.session import get_engine, get_session

        engine = get_engine(":memory:")
        Base.metadata.create_all(engine)
        session = get_session(":memory:")
        Base.metadata.create_all(session.bind)

        contact = Contact(id="c1", first_name="Test")
        phone = Phone(contact_id="c1", phone_number="555-1234", label="Mobile")

        session.add(contact)
        session.add(phone)
        session.commit()

        retrieved = session.query(Phone).filter_by(contact_id="c1").first()
        assert retrieved.label == "Mobile"
        session.close()

    def test_multiple_contacts_with_duplicates(self):
        """Should handle duplicate group relationships."""
        from dex_python.db.models import Base, Contact
        from dex_python.db.session import get_engine, get_session

        engine = get_engine(":memory:")
        Base.metadata.create_all(engine)
        session = get_session(":memory:")
        Base.metadata.create_all(session.bind)

        group_id = "group-123"
        contact1 = Contact(
            id="c1",
            first_name="John",
            last_name="Doe",
            duplicate_group_id=group_id,
            primary_contact_id="c1",
        )
        contact2 = Contact(
            id="c2",
            first_name="John",
            last_name="Doe",
            duplicate_group_id=group_id,
            primary_contact_id="c1",
            duplicate_resolution="merged",
        )

        session.add(contact1)
        session.add(contact2)
        session.commit()

        # Query by duplicate group
        duplicates = (
            session.query(Contact).filter_by(duplicate_group_id=group_id).all()
        )
        assert len(duplicates) == 2
        session.close()

    def test_contact_enrichment_fields(self):
        """Contact should support enrichment fields."""
        from dex_python.db.models import Base, Contact
        from dex_python.db.session import get_engine, get_session

        engine = get_engine(":memory:")
        Base.metadata.create_all(engine)
        session = get_session(":memory:")
        Base.metadata.create_all(session.bind)

        contact = Contact(
            id="c1",
            first_name="Jane",
            job_title="Software Engineer at Google",
            company="Google",
            role="Software Engineer",
        )

        session.add(contact)
        session.commit()

        retrieved = session.query(Contact).filter_by(id="c1").first()
        assert retrieved.company == "Google"
        assert retrieved.role == "Software Engineer"
        session.close()
        assert expected.issubset(index_names)
