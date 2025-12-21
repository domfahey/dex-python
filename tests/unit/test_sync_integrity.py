"""Tests for sync_with_integrity.py - preserving dedup metadata."""

import json
import sqlite3

import pytest

from scripts.sync_with_integrity import init_db, save_contacts_batch


@pytest.fixture
def db_connection() -> sqlite3.Connection:
    """Create in-memory SQLite database."""
    conn = sqlite3.connect(":memory:")
    init_db(conn)
    return conn


class TestSaveBatchPreservesMetadata:
    """Test that save_contacts_batch preserves dedup columns on updates."""

    def test_update_preserves_duplicate_group_id(
        self, db_connection: sqlite3.Connection
    ) -> None:
        """Updating a contact should preserve duplicate_group_id."""
        cursor = db_connection.cursor()

        # Insert initial contact with dedup metadata
        cursor.execute("""
            INSERT INTO contacts (id, first_name, last_name, duplicate_group_id)
            VALUES ('c1', 'John', 'Doe', 'group-123')
        """)
        db_connection.commit()

        # Simulate sync update with changed name
        contacts = [{"id": "c1", "first_name": "Johnny", "last_name": "Doe"}]
        save_contacts_batch(db_connection, contacts)

        # Verify dedup metadata preserved
        cursor.execute(
            "SELECT first_name, duplicate_group_id FROM contacts WHERE id = 'c1'"
        )
        row = cursor.fetchone()
        assert row[0] == "Johnny", "Name should be updated"
        assert row[1] == "group-123", "duplicate_group_id should be preserved"

    def test_update_preserves_duplicate_resolution(
        self, db_connection: sqlite3.Connection
    ) -> None:
        """Updating a contact should preserve duplicate_resolution."""
        cursor = db_connection.cursor()

        cursor.execute("""
            INSERT INTO contacts (id, first_name, duplicate_resolution)
            VALUES ('c1', 'Jane', 'keep')
        """)
        db_connection.commit()

        contacts = [{"id": "c1", "first_name": "Janet"}]
        save_contacts_batch(db_connection, contacts)

        cursor.execute(
            "SELECT first_name, duplicate_resolution FROM contacts WHERE id = 'c1'"
        )
        row = cursor.fetchone()
        assert row[0] == "Janet"
        assert row[1] == "keep", "duplicate_resolution should be preserved"

    def test_update_preserves_primary_contact_id(
        self, db_connection: sqlite3.Connection
    ) -> None:
        """Updating a contact should preserve primary_contact_id."""
        cursor = db_connection.cursor()

        cursor.execute("""
            INSERT INTO contacts (id, first_name, primary_contact_id)
            VALUES ('c1', 'Bob', 'c2')
        """)
        db_connection.commit()

        contacts = [{"id": "c1", "first_name": "Robert"}]
        save_contacts_batch(db_connection, contacts)

        cursor.execute(
            "SELECT first_name, primary_contact_id FROM contacts WHERE id = 'c1'"
        )
        row = cursor.fetchone()
        assert row[0] == "Robert"
        assert row[1] == "c2", "primary_contact_id should be preserved"

    def test_new_contact_has_null_dedup_columns(
        self, db_connection: sqlite3.Connection
    ) -> None:
        """New contacts should have NULL dedup columns."""
        contacts = [{"id": "new1", "first_name": "New", "last_name": "Contact"}]
        save_contacts_batch(db_connection, contacts)

        cursor = db_connection.cursor()
        cursor.execute("""
            SELECT duplicate_group_id, duplicate_resolution, primary_contact_id
            FROM contacts WHERE id = 'new1'
        """)
        row = cursor.fetchone()
        assert row == (None, None, None)


class TestSaveBatchNameParsing:
    """Test that save_contacts_batch stores parsed name fields."""

    def test_save_contacts_batch_stores_name_parsing(
        self, db_connection: sqlite3.Connection
    ) -> None:
        """Store parsed name fields for new contacts."""
        contacts = [{"id": "c1", "first_name": "Ada", "last_name": "Lovelace"}]
        save_contacts_batch(db_connection, contacts)

        cursor = db_connection.cursor()
        cursor.execute("""
            SELECT name_given, name_surname, name_parsed
            FROM contacts WHERE id = 'c1'
        """)
        row = cursor.fetchone()

        assert row[0] == "Ada"
        assert row[1] == "Lovelace"
        parsed = json.loads(row[2])
        assert parsed["raw"] == "Ada Lovelace"

    def test_save_contacts_batch_updates_name_parsing(
        self, db_connection: sqlite3.Connection
    ) -> None:
        """Update parsed name fields when contact changes."""
        contacts = [{"id": "c1", "first_name": "Ada", "last_name": "Lovelace"}]
        save_contacts_batch(db_connection, contacts)

        updated = [{"id": "c1", "first_name": "Augusta", "last_name": "Lovelace"}]
        added, updated_count, unchanged = save_contacts_batch(db_connection, updated)

        assert added == 0
        assert updated_count == 1
        assert unchanged == 0

        cursor = db_connection.cursor()
        cursor.execute("""
            SELECT name_given, name_surname, name_parsed
            FROM contacts WHERE id = 'c1'
        """)
        row = cursor.fetchone()

        assert row[0] == "Augusta"
        assert row[1] == "Lovelace"
        parsed = json.loads(row[2])
        assert parsed["raw"] == "Augusta Lovelace"


class TestSaveBatchEnrichment:
    """Test that save_contacts_batch extracts company/role from job titles."""

    def test_extracts_company_from_job_title(
        self, db_connection: sqlite3.Connection
    ) -> None:
        """Save contact with 'Role at Company' pattern extracts both."""
        contacts = [
            {
                "id": "c1",
                "first_name": "John",
                "last_name": "Doe",
                "job_title": "Software Engineer at Google",
            }
        ]
        save_contacts_batch(db_connection, contacts)

        cursor = db_connection.cursor()
        cursor.execute("SELECT company, role FROM contacts WHERE id = 'c1'")
        row = cursor.fetchone()
        assert row[0] == "Google", "Company should be extracted"
        assert row[1] == "Software Engineer", "Role should be extracted"

    def test_extracts_role_only_when_no_company_pattern(
        self, db_connection: sqlite3.Connection
    ) -> None:
        """Save contact without 'at Company' pattern sets role only."""
        contacts = [
            {
                "id": "c2",
                "first_name": "Jane",
                "last_name": "Smith",
                "job_title": "Senior Developer",
            }
        ]
        save_contacts_batch(db_connection, contacts)

        cursor = db_connection.cursor()
        cursor.execute("SELECT company, role FROM contacts WHERE id = 'c2'")
        row = cursor.fetchone()
        assert row[0] is None, "Company should be None"
        assert row[1] == "Senior Developer", "Role should be the full title"

    def test_handles_no_job_title(self, db_connection: sqlite3.Connection) -> None:
        """Save contact without job_title sets both to None."""
        contacts = [{"id": "c3", "first_name": "Bob", "last_name": "Jones"}]
        save_contacts_batch(db_connection, contacts)

        cursor = db_connection.cursor()
        cursor.execute("SELECT company, role FROM contacts WHERE id = 'c3'")
        row = cursor.fetchone()
        assert row[0] is None
        assert row[1] is None

    def test_update_refreshes_company_role(
        self, db_connection: sqlite3.Connection
    ) -> None:
        """Updating job_title should refresh company/role."""
        # Initial insert
        contacts = [
            {
                "id": "c4",
                "first_name": "Alice",
                "last_name": "Brown",
                "job_title": "Engineer at StartupA",
            }
        ]
        save_contacts_batch(db_connection, contacts)

        # Update with new job
        contacts_updated = [
            {
                "id": "c4",
                "first_name": "Alice",
                "last_name": "Brown",
                "job_title": "VP at BigCorp",
            }
        ]
        save_contacts_batch(db_connection, contacts_updated)

        cursor = db_connection.cursor()
        cursor.execute("SELECT company, role FROM contacts WHERE id = 'c4'")
        row = cursor.fetchone()
        assert row[0] == "BigCorp", "Company should be updated"
        assert row[1] == "VP", "Role should be updated"
