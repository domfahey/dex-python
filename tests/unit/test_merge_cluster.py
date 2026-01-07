"""Edge case tests for merge_cluster function in deduplication module.

Tests various edge cases, error conditions, and data merging behaviors.
"""

import json
import sqlite3

import pytest

from dex_python.deduplication import (
    cluster_duplicates,
    find_email_duplicates,
    find_fingerprint_name_duplicates,
    find_phone_duplicates,
    merge_cluster,
)


@pytest.fixture
def test_db() -> sqlite3.Connection:
    """Create an in-memory test database with schema."""
    conn = sqlite3.connect(":memory:")
    cursor = conn.cursor()

    # Create contacts table
    cursor.execute("""
        CREATE TABLE contacts (
            id TEXT PRIMARY KEY,
            first_name TEXT,
            last_name TEXT,
            job_title TEXT,
            linkedin TEXT,
            website TEXT,
            full_data TEXT
        )
    """)

    # Create emails table
    cursor.execute("""
        CREATE TABLE emails (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            contact_id TEXT,
            email TEXT,
            FOREIGN KEY (contact_id) REFERENCES contacts(id)
        )
    """)

    # Create phones table
    cursor.execute("""
        CREATE TABLE phones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            contact_id TEXT,
            phone_number TEXT,
            label TEXT,
            FOREIGN KEY (contact_id) REFERENCES contacts(id)
        )
    """)

    conn.commit()
    return conn


class TestMergeClusterEdgeCases:
    """Test edge cases for merge_cluster function."""

    def test_empty_contact_ids_raises_error(self, test_db: sqlite3.Connection) -> None:
        """merge_cluster should raise ValueError for empty contact_ids list."""
        with pytest.raises(ValueError, match="No contact IDs provided"):
            merge_cluster(test_db, [])

    def test_nonexistent_contacts_raises_error(
        self, test_db: sqlite3.Connection
    ) -> None:
        """merge_cluster should raise ValueError when contacts don't exist."""
        with pytest.raises(ValueError, match="Contacts not found"):
            merge_cluster(test_db, ["nonexistent-1", "nonexistent-2"])

    def test_primary_id_not_in_cluster_raises_error(
        self, test_db: sqlite3.Connection
    ) -> None:
        """merge_cluster should raise ValueError when primary_id not in contact_ids."""
        cursor = test_db.cursor()
        cursor.execute(
            "INSERT INTO contacts (id, first_name, last_name) VALUES (?, ?, ?)",
            ("c1", "John", "Doe"),
        )
        cursor.execute(
            "INSERT INTO contacts (id, first_name, last_name) VALUES (?, ?, ?)",
            ("c2", "Jane", "Doe"),
        )
        test_db.commit()

        with pytest.raises(ValueError, match="Primary ID .* not found"):
            merge_cluster(test_db, ["c1", "c2"], primary_id="c3")

    def test_single_contact_returns_same_id(
        self, test_db: sqlite3.Connection
    ) -> None:
        """merge_cluster with single contact should return that contact's ID."""
        cursor = test_db.cursor()
        cursor.execute(
            "INSERT INTO contacts (id, first_name, last_name) VALUES (?, ?, ?)",
            ("only-one", "Solo", "Contact"),
        )
        test_db.commit()

        result = merge_cluster(test_db, ["only-one"])
        assert result == "only-one"

    def test_merge_selects_most_complete_as_primary(
        self, test_db: sqlite3.Connection
    ) -> None:
        """Without explicit primary_id, merge should select most complete contact."""
        cursor = test_db.cursor()
        # Less complete contact
        cursor.execute(
            "INSERT INTO contacts (id, first_name) VALUES (?, ?)",
            ("sparse", "John"),
        )
        # More complete contact
        cursor.execute(
            """INSERT INTO contacts (id, first_name, last_name, job_title, linkedin, website)
               VALUES (?, ?, ?, ?, ?, ?)""",
            ("complete", "John", "Doe", "Engineer", "johndoe", "example.com"),
        )
        test_db.commit()

        result = merge_cluster(test_db, ["sparse", "complete"])

        # Should select "complete" as primary due to more fields
        assert result == "complete"

        # Sparse contact should be deleted
        cursor.execute("SELECT COUNT(*) FROM contacts WHERE id = ?", ("sparse",))
        assert cursor.fetchone()[0] == 0

    def test_merge_fills_missing_fields(self, test_db: sqlite3.Connection) -> None:
        """Merge should fill missing fields from other contacts."""
        cursor = test_db.cursor()
        # Contact 1 has first_name and job_title
        cursor.execute(
            "INSERT INTO contacts (id, first_name, job_title) VALUES (?, ?, ?)",
            ("c1", "John", "Engineer"),
        )
        # Contact 2 has last_name and linkedin
        cursor.execute(
            "INSERT INTO contacts (id, last_name, linkedin) VALUES (?, ?, ?)",
            ("c2", "Doe", "johndoe"),
        )
        test_db.commit()

        merge_cluster(test_db, ["c1", "c2"], primary_id="c1")

        cursor.execute(
            "SELECT first_name, last_name, job_title, linkedin FROM contacts WHERE id = ?",
            ("c1",),
        )
        row = cursor.fetchone()
        assert row == ("John", "Doe", "Engineer", "johndoe")

    def test_merge_does_not_overwrite_existing_fields(
        self, test_db: sqlite3.Connection
    ) -> None:
        """Merge should not overwrite existing non-empty fields in primary."""
        cursor = test_db.cursor()
        cursor.execute(
            "INSERT INTO contacts (id, first_name, last_name) VALUES (?, ?, ?)",
            ("primary", "John", "Doe"),
        )
        cursor.execute(
            "INSERT INTO contacts (id, first_name, last_name) VALUES (?, ?, ?)",
            ("secondary", "Jane", "Smith"),
        )
        test_db.commit()

        merge_cluster(test_db, ["primary", "secondary"], primary_id="primary")

        cursor.execute(
            "SELECT first_name, last_name FROM contacts WHERE id = ?", ("primary",)
        )
        row = cursor.fetchone()
        # Primary's values should be preserved
        assert row == ("John", "Doe")

    def test_merge_reassigns_emails(self, test_db: sqlite3.Connection) -> None:
        """Merge should reassign emails from merged contacts to primary."""
        cursor = test_db.cursor()
        cursor.execute(
            "INSERT INTO contacts (id, first_name) VALUES (?, ?)", ("c1", "John")
        )
        cursor.execute(
            "INSERT INTO contacts (id, first_name) VALUES (?, ?)", ("c2", "John")
        )
        cursor.execute(
            "INSERT INTO emails (contact_id, email) VALUES (?, ?)",
            ("c1", "john@work.com"),
        )
        cursor.execute(
            "INSERT INTO emails (contact_id, email) VALUES (?, ?)",
            ("c2", "john@personal.com"),
        )
        test_db.commit()

        merge_cluster(test_db, ["c1", "c2"], primary_id="c1")

        cursor.execute(
            "SELECT email FROM emails WHERE contact_id = ? ORDER BY email", ("c1",)
        )
        emails = [row[0] for row in cursor.fetchall()]
        assert "john@work.com" in emails
        assert "john@personal.com" in emails

    def test_merge_deduplicates_emails(self, test_db: sqlite3.Connection) -> None:
        """Merge should deduplicate identical emails."""
        cursor = test_db.cursor()
        cursor.execute(
            "INSERT INTO contacts (id, first_name) VALUES (?, ?)", ("c1", "John")
        )
        cursor.execute(
            "INSERT INTO contacts (id, first_name) VALUES (?, ?)", ("c2", "John")
        )
        # Both contacts have same email
        cursor.execute(
            "INSERT INTO emails (contact_id, email) VALUES (?, ?)",
            ("c1", "john@example.com"),
        )
        cursor.execute(
            "INSERT INTO emails (contact_id, email) VALUES (?, ?)",
            ("c2", "john@example.com"),
        )
        test_db.commit()

        merge_cluster(test_db, ["c1", "c2"], primary_id="c1")

        cursor.execute(
            "SELECT COUNT(*) FROM emails WHERE contact_id = ? AND email = ?",
            ("c1", "john@example.com"),
        )
        assert cursor.fetchone()[0] == 1  # Should be deduplicated

    def test_merge_reassigns_phones(self, test_db: sqlite3.Connection) -> None:
        """Merge should reassign phones from merged contacts to primary."""
        cursor = test_db.cursor()
        cursor.execute(
            "INSERT INTO contacts (id, first_name) VALUES (?, ?)", ("c1", "John")
        )
        cursor.execute(
            "INSERT INTO contacts (id, first_name) VALUES (?, ?)", ("c2", "John")
        )
        cursor.execute(
            "INSERT INTO phones (contact_id, phone_number, label) VALUES (?, ?, ?)",
            ("c1", "555-1111", "Work"),
        )
        cursor.execute(
            "INSERT INTO phones (contact_id, phone_number, label) VALUES (?, ?, ?)",
            ("c2", "555-2222", "Mobile"),
        )
        test_db.commit()

        merge_cluster(test_db, ["c1", "c2"], primary_id="c1")

        cursor.execute(
            "SELECT phone_number FROM phones WHERE contact_id = ? ORDER BY phone_number",
            ("c1",),
        )
        phones = [row[0] for row in cursor.fetchall()]
        assert "555-1111" in phones
        assert "555-2222" in phones

    def test_merge_deduplicates_phones(self, test_db: sqlite3.Connection) -> None:
        """Merge should deduplicate identical phone numbers."""
        cursor = test_db.cursor()
        cursor.execute(
            "INSERT INTO contacts (id, first_name) VALUES (?, ?)", ("c1", "John")
        )
        cursor.execute(
            "INSERT INTO contacts (id, first_name) VALUES (?, ?)", ("c2", "John")
        )
        # Both have same phone number
        cursor.execute(
            "INSERT INTO phones (contact_id, phone_number, label) VALUES (?, ?, ?)",
            ("c1", "555-1234", "Work"),
        )
        cursor.execute(
            "INSERT INTO phones (contact_id, phone_number, label) VALUES (?, ?, ?)",
            ("c2", "555-1234", "Office"),
        )
        test_db.commit()

        merge_cluster(test_db, ["c1", "c2"], primary_id="c1")

        cursor.execute(
            "SELECT COUNT(*) FROM phones WHERE contact_id = ? AND phone_number = ?",
            ("c1", "555-1234"),
        )
        assert cursor.fetchone()[0] == 1  # Should be deduplicated

    def test_merge_deletes_secondary_contacts(
        self, test_db: sqlite3.Connection
    ) -> None:
        """Merge should delete all non-primary contacts."""
        cursor = test_db.cursor()
        cursor.execute(
            "INSERT INTO contacts (id, first_name) VALUES (?, ?)", ("c1", "John")
        )
        cursor.execute(
            "INSERT INTO contacts (id, first_name) VALUES (?, ?)", ("c2", "Jane")
        )
        cursor.execute(
            "INSERT INTO contacts (id, first_name) VALUES (?, ?)", ("c3", "Bob")
        )
        test_db.commit()

        merge_cluster(test_db, ["c1", "c2", "c3"], primary_id="c1")

        cursor.execute("SELECT id FROM contacts")
        remaining = [row[0] for row in cursor.fetchall()]
        assert remaining == ["c1"]

    def test_merge_handles_null_fields(self, test_db: sqlite3.Connection) -> None:
        """Merge should correctly handle NULL vs empty string fields."""
        cursor = test_db.cursor()
        cursor.execute(
            "INSERT INTO contacts (id, first_name, last_name, job_title) VALUES (?, ?, ?, ?)",
            ("c1", "John", None, ""),
        )
        cursor.execute(
            "INSERT INTO contacts (id, first_name, last_name, job_title) VALUES (?, ?, ?, ?)",
            ("c2", None, "Doe", "Engineer"),
        )
        test_db.commit()

        merge_cluster(test_db, ["c1", "c2"], primary_id="c1")

        cursor.execute(
            "SELECT first_name, last_name, job_title FROM contacts WHERE id = ?",
            ("c1",),
        )
        row = cursor.fetchone()
        assert row[0] == "John"  # Preserved from c1
        assert row[1] == "Doe"  # Filled from c2
        assert row[2] == "Engineer"  # Filled from c2 (empty string treated as empty)

    def test_merge_preserves_full_data_json(self, test_db: sqlite3.Connection) -> None:
        """Merge should preserve full_data JSON from primary or fill from secondary."""
        cursor = test_db.cursor()
        full_data_1 = json.dumps({"birthday": "1990-05-15", "notes": "VIP"})
        cursor.execute(
            "INSERT INTO contacts (id, first_name, full_data) VALUES (?, ?, ?)",
            ("c1", "John", full_data_1),
        )
        cursor.execute(
            "INSERT INTO contacts (id, first_name, full_data) VALUES (?, ?, ?)",
            ("c2", "John", None),
        )
        test_db.commit()

        merge_cluster(test_db, ["c1", "c2"], primary_id="c1")

        cursor.execute("SELECT full_data FROM contacts WHERE id = ?", ("c1",))
        row = cursor.fetchone()
        assert row[0] == full_data_1

    def test_merge_fills_full_data_from_secondary(
        self, test_db: sqlite3.Connection
    ) -> None:
        """Merge should fill full_data from secondary if primary is empty."""
        cursor = test_db.cursor()
        full_data_2 = json.dumps({"birthday": "1990-05-15"})
        cursor.execute(
            "INSERT INTO contacts (id, first_name, full_data, job_title) VALUES (?, ?, ?, ?)",
            ("c1", "John", None, "CEO"),
        )
        cursor.execute(
            "INSERT INTO contacts (id, first_name, full_data) VALUES (?, ?, ?)",
            ("c2", "John", full_data_2),
        )
        test_db.commit()

        merge_cluster(test_db, ["c1", "c2"], primary_id="c1")

        cursor.execute("SELECT full_data FROM contacts WHERE id = ?", ("c1",))
        row = cursor.fetchone()
        assert row[0] == full_data_2

    def test_merge_three_contacts(self, test_db: sqlite3.Connection) -> None:
        """Merge should work correctly with more than two contacts."""
        cursor = test_db.cursor()
        cursor.execute(
            "INSERT INTO contacts (id, first_name) VALUES (?, ?)", ("c1", "John")
        )
        cursor.execute(
            "INSERT INTO contacts (id, last_name) VALUES (?, ?)", ("c2", "Doe")
        )
        cursor.execute(
            "INSERT INTO contacts (id, job_title) VALUES (?, ?)", ("c3", "Engineer")
        )
        test_db.commit()

        merge_cluster(test_db, ["c1", "c2", "c3"], primary_id="c1")

        cursor.execute(
            "SELECT first_name, last_name, job_title FROM contacts WHERE id = ?",
            ("c1",),
        )
        row = cursor.fetchone()
        assert row == ("John", "Doe", "Engineer")

    def test_merge_with_explicit_primary_overrides_auto_selection(
        self, test_db: sqlite3.Connection
    ) -> None:
        """Explicit primary_id should override auto-selection of most complete."""
        cursor = test_db.cursor()
        # More complete contact
        cursor.execute(
            """INSERT INTO contacts (id, first_name, last_name, job_title)
               VALUES (?, ?, ?, ?)""",
            ("complete", "John", "Doe", "Engineer"),
        )
        # Less complete contact
        cursor.execute(
            "INSERT INTO contacts (id, first_name) VALUES (?, ?)",
            ("sparse", "Jane"),
        )
        test_db.commit()

        # Force sparse to be primary
        result = merge_cluster(test_db, ["complete", "sparse"], primary_id="sparse")

        assert result == "sparse"
        cursor.execute("SELECT first_name FROM contacts WHERE id = ?", ("sparse",))
        # Should have Jane (not overwritten by John)
        assert cursor.fetchone()[0] == "Jane"


class TestClusterDuplicates:
    """Test cluster_duplicates function."""

    def test_cluster_empty_matches(self) -> None:
        """cluster_duplicates should return empty list for empty input."""
        result = cluster_duplicates([])
        assert result == []

    def test_cluster_single_match(self) -> None:
        """cluster_duplicates should handle single match."""
        matches = [{"match_type": "email", "contact_ids": ["c1", "c2"]}]
        result = cluster_duplicates(matches)
        assert len(result) == 1
        assert set(result[0]) == {"c1", "c2"}

    def test_cluster_transitive_matches(self) -> None:
        """cluster_duplicates should group transitive matches."""
        # c1 matches c2, c2 matches c3 -> all should be in same cluster
        matches = [
            {"match_type": "email", "contact_ids": ["c1", "c2"]},
            {"match_type": "phone", "contact_ids": ["c2", "c3"]},
        ]
        result = cluster_duplicates(matches)
        assert len(result) == 1
        assert set(result[0]) == {"c1", "c2", "c3"}

    def test_cluster_independent_matches(self) -> None:
        """cluster_duplicates should keep independent matches separate."""
        matches = [
            {"match_type": "email", "contact_ids": ["c1", "c2"]},
            {"match_type": "email", "contact_ids": ["c3", "c4"]},
        ]
        result = cluster_duplicates(matches)
        assert len(result) == 2
        cluster_sets = [set(c) for c in result]
        assert {"c1", "c2"} in cluster_sets
        assert {"c3", "c4"} in cluster_sets

    def test_cluster_multiple_ids_in_single_match(self) -> None:
        """cluster_duplicates should handle matches with multiple contact_ids."""
        matches = [{"match_type": "email", "contact_ids": ["c1", "c2", "c3", "c4"]}]
        result = cluster_duplicates(matches)
        assert len(result) == 1
        assert set(result[0]) == {"c1", "c2", "c3", "c4"}

    def test_cluster_ignores_single_id_matches(self) -> None:
        """cluster_duplicates should ignore matches with single contact_id."""
        matches = [
            {"match_type": "email", "contact_ids": ["c1"]},  # Single ID - ignored
            {"match_type": "email", "contact_ids": ["c2", "c3"]},
        ]
        result = cluster_duplicates(matches)
        assert len(result) == 1
        assert set(result[0]) == {"c2", "c3"}


class TestFindDuplicates:
    """Test duplicate finding functions."""

    def test_find_email_duplicates_empty_db(self, test_db: sqlite3.Connection) -> None:
        """find_email_duplicates should return empty list for empty DB."""
        result = find_email_duplicates(test_db)
        assert result == []

    def test_find_email_duplicates_no_duplicates(
        self, test_db: sqlite3.Connection
    ) -> None:
        """find_email_duplicates should return empty when no duplicates exist."""
        cursor = test_db.cursor()
        cursor.execute(
            "INSERT INTO contacts (id, first_name) VALUES (?, ?)", ("c1", "John")
        )
        cursor.execute(
            "INSERT INTO contacts (id, first_name) VALUES (?, ?)", ("c2", "Jane")
        )
        cursor.execute(
            "INSERT INTO emails (contact_id, email) VALUES (?, ?)",
            ("c1", "john@example.com"),
        )
        cursor.execute(
            "INSERT INTO emails (contact_id, email) VALUES (?, ?)",
            ("c2", "jane@example.com"),
        )
        test_db.commit()

        result = find_email_duplicates(test_db)
        assert result == []

    def test_find_email_duplicates_case_insensitive(
        self, test_db: sqlite3.Connection
    ) -> None:
        """find_email_duplicates should match case-insensitively."""
        cursor = test_db.cursor()
        cursor.execute(
            "INSERT INTO contacts (id, first_name) VALUES (?, ?)", ("c1", "John")
        )
        cursor.execute(
            "INSERT INTO contacts (id, first_name) VALUES (?, ?)", ("c2", "JOHN")
        )
        cursor.execute(
            "INSERT INTO emails (contact_id, email) VALUES (?, ?)",
            ("c1", "john@example.com"),
        )
        cursor.execute(
            "INSERT INTO emails (contact_id, email) VALUES (?, ?)",
            ("c2", "JOHN@EXAMPLE.COM"),
        )
        test_db.commit()

        result = find_email_duplicates(test_db)
        assert len(result) == 1
        assert set(result[0]["contact_ids"]) == {"c1", "c2"}

    def test_find_phone_duplicates_normalized(
        self, test_db: sqlite3.Connection
    ) -> None:
        """find_phone_duplicates should normalize phone numbers."""
        cursor = test_db.cursor()
        cursor.execute(
            "INSERT INTO contacts (id, first_name) VALUES (?, ?)", ("c1", "John")
        )
        cursor.execute(
            "INSERT INTO contacts (id, first_name) VALUES (?, ?)", ("c2", "John")
        )
        # Different formats, same number
        cursor.execute(
            "INSERT INTO phones (contact_id, phone_number) VALUES (?, ?)",
            ("c1", "+1 (555) 123-4567"),
        )
        cursor.execute(
            "INSERT INTO phones (contact_id, phone_number) VALUES (?, ?)",
            ("c2", "5551234567"),
        )
        test_db.commit()

        result = find_phone_duplicates(test_db)
        assert len(result) == 1
        assert set(result[0]["contact_ids"]) == {"c1", "c2"}

    def test_find_fingerprint_duplicates(self, test_db: sqlite3.Connection) -> None:
        """find_fingerprint_name_duplicates should match reordered names."""
        cursor = test_db.cursor()
        cursor.execute(
            "INSERT INTO contacts (id, first_name, last_name) VALUES (?, ?, ?)",
            ("c1", "John", "Doe"),
        )
        cursor.execute(
            "INSERT INTO contacts (id, first_name, last_name) VALUES (?, ?, ?)",
            ("c2", "Doe", "John"),  # Reversed name
        )
        test_db.commit()

        result = find_fingerprint_name_duplicates(test_db)
        assert len(result) == 1
        assert set(result[0]["contact_ids"]) == {"c1", "c2"}

    def test_find_fingerprint_skips_empty_names(
        self, test_db: sqlite3.Connection
    ) -> None:
        """find_fingerprint_name_duplicates should skip contacts with empty names."""
        cursor = test_db.cursor()
        cursor.execute(
            "INSERT INTO contacts (id, first_name, last_name) VALUES (?, ?, ?)",
            ("c1", "", ""),
        )
        cursor.execute(
            "INSERT INTO contacts (id, first_name, last_name) VALUES (?, ?, ?)",
            ("c2", None, None),
        )
        test_db.commit()

        result = find_fingerprint_name_duplicates(test_db)
        assert result == []
