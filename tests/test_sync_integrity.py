"""Tests for sync_with_integrity.py - preserving dedup metadata."""

import sqlite3

import pytest

from sync_with_integrity import init_db, save_batch


@pytest.fixture
def db_connection() -> sqlite3.Connection:
    """Create in-memory SQLite database."""
    conn = sqlite3.connect(":memory:")
    init_db(conn)
    return conn


class TestSaveBatchPreservesMetadata:
    """Test that save_batch preserves dedup columns on updates."""

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
        save_batch(db_connection, contacts)

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
        save_batch(db_connection, contacts)

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
        save_batch(db_connection, contacts)

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
        save_batch(db_connection, contacts)

        cursor = db_connection.cursor()
        cursor.execute("""
            SELECT duplicate_group_id, duplicate_resolution, primary_contact_id
            FROM contacts WHERE id = 'new1'
        """)
        row = cursor.fetchone()
        assert row == (None, None, None)
