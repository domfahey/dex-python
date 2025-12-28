"""Tests for SQLAlchemy models matching current schema.

TDD tests ensuring SQLAlchemy models produce identical schema to raw SQL.
"""

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
        index_names = {idx["name"] for idx in indexes}

        expected = {"idx_phones_contact_id", "idx_phones_number"}
        assert expected.issubset(index_names)
