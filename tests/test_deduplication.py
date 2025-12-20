"""Tests for deduplication.py - duplicate detection logic."""

import sqlite3

import pytest

from src.dex_import.deduplication import (
    find_email_duplicates,
    find_fuzzy_name_duplicates,
    find_phone_duplicates,
)


@pytest.fixture
def db_connection() -> sqlite3.Connection:
    """Create in-memory SQLite database with test schema."""
    conn = sqlite3.connect(":memory:")
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE contacts (
            id TEXT PRIMARY KEY,
            first_name TEXT,
            last_name TEXT,
            job_title TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE emails (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            contact_id TEXT,
            email TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE phones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            contact_id TEXT,
            phone_number TEXT
        )
    """)

    conn.commit()
    return conn


class TestFuzzyNameDuplicates:
    """Tests for find_fuzzy_name_duplicates."""

    def test_empty_last_name_not_matched(
        self, db_connection: sqlite3.Connection
    ) -> None:
        """Empty last names should not be matched together."""
        cursor = db_connection.cursor()

        # Insert contacts with empty last names - should NOT match
        cursor.execute(
            "INSERT INTO contacts (id, first_name, last_name) VALUES ('c1', 'John', '')"
        )
        cursor.execute(
            "INSERT INTO contacts (id, first_name, last_name) VALUES ('c2', 'Jane', '')"
        )
        # Insert a valid contact
        cursor.execute(
            "INSERT INTO contacts (id, first_name, last_name) VALUES ('c3', 'Bob', 'Smith')"
        )
        db_connection.commit()

        results = find_fuzzy_name_duplicates(db_connection, threshold=0.9)

        # Empty last names should be filtered out, no matches
        matched_ids = set()
        for r in results:
            matched_ids.update(r["contact_ids"])

        assert "c1" not in matched_ids, "Empty last name contacts should not match"
        assert "c2" not in matched_ids, "Empty last name contacts should not match"

    def test_whitespace_last_name_not_matched(
        self, db_connection: sqlite3.Connection
    ) -> None:
        """Whitespace-only last names should not be matched."""
        cursor = db_connection.cursor()

        cursor.execute(
            "INSERT INTO contacts (id, first_name, last_name) VALUES ('c1', 'John', '   ')"
        )
        cursor.execute(
            "INSERT INTO contacts (id, first_name, last_name) VALUES ('c2', 'Jane', '  ')"
        )
        db_connection.commit()

        results = find_fuzzy_name_duplicates(db_connection, threshold=0.9)

        matched_ids = set()
        for r in results:
            matched_ids.update(r["contact_ids"])

        assert "c1" not in matched_ids
        assert "c2" not in matched_ids


class TestEmailDuplicates:
    """Tests for find_email_duplicates."""

    def test_duplicate_email_on_same_contact_no_repeat(
        self, db_connection: sqlite3.Connection
    ) -> None:
        """Same email twice on one contact should not produce duplicate IDs."""
        cursor = db_connection.cursor()

        cursor.execute(
            "INSERT INTO contacts (id, first_name) VALUES ('c1', 'John')"
        )
        # Same email twice on c1
        cursor.execute(
            "INSERT INTO emails (contact_id, email) VALUES ('c1', 'john@example.com')"
        )
        cursor.execute(
            "INSERT INTO emails (contact_id, email) VALUES ('c1', 'john@example.com')"
        )
        # Different contact with same email
        cursor.execute(
            "INSERT INTO contacts (id, first_name) VALUES ('c2', 'Jane')"
        )
        cursor.execute(
            "INSERT INTO emails (contact_id, email) VALUES ('c2', 'john@example.com')"
        )
        db_connection.commit()

        results = find_email_duplicates(db_connection)

        assert len(results) == 1
        # Should only have unique contact IDs
        contact_ids = results[0]["contact_ids"]
        assert len(contact_ids) == len(set(contact_ids)), "contact_ids should be unique"


class TestPhoneDuplicates:
    """Tests for find_phone_duplicates."""

    def test_duplicate_phone_on_same_contact_no_repeat(
        self, db_connection: sqlite3.Connection
    ) -> None:
        """Same phone twice on one contact should not produce duplicate IDs."""
        cursor = db_connection.cursor()

        cursor.execute(
            "INSERT INTO contacts (id, first_name) VALUES ('c1', 'John')"
        )
        cursor.execute(
            "INSERT INTO phones (contact_id, phone_number) VALUES ('c1', '555-1234')"
        )
        cursor.execute(
            "INSERT INTO phones (contact_id, phone_number) VALUES ('c1', '555-1234')"
        )
        cursor.execute(
            "INSERT INTO contacts (id, first_name) VALUES ('c2', 'Jane')"
        )
        cursor.execute(
            "INSERT INTO phones (contact_id, phone_number) VALUES ('c2', '555-1234')"
        )
        db_connection.commit()

        results = find_phone_duplicates(db_connection)

        assert len(results) == 1
        contact_ids = results[0]["contact_ids"]
        assert len(contact_ids) == len(set(contact_ids)), "contact_ids should be unique"
