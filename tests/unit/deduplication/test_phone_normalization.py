"""Tests for phone number normalization in deduplication.

TDD tests for finding phone duplicates with normalized phone numbers.
"""

import sqlite3

import pytest


@pytest.fixture
def conn():
    """Create in-memory SQLite database with test schema."""
    conn = sqlite3.connect(":memory:")
    cursor = conn.cursor()
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
    cursor.execute("""
        CREATE TABLE phones (
            id INTEGER PRIMARY KEY,
            contact_id TEXT,
            phone_number TEXT
        )
    """)
    conn.commit()
    return conn


class TestPhoneNormalization:
    """Test phone duplicate detection with normalization."""

    def test_matches_different_formats(self, conn):
        """Different phone formats should match as duplicates."""
        from dex_python.deduplication import find_phone_duplicates

        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO contacts (id, first_name, last_name) VALUES (?, ?, ?)",
            ("c1", "John", "Doe"),
        )
        cursor.execute(
            "INSERT INTO contacts (id, first_name, last_name) VALUES (?, ?, ?)",
            ("c2", "Jane", "Smith"),
        )
        cursor.execute(
            "INSERT INTO phones (contact_id, phone_number) VALUES (?, ?)",
            ("c1", "(555) 123-4567"),
        )
        cursor.execute(
            "INSERT INTO phones (contact_id, phone_number) VALUES (?, ?)",
            ("c2", "555-123-4567"),
        )
        conn.commit()

        results = find_phone_duplicates(conn)
        assert len(results) == 1
        assert set(results[0]["contact_ids"]) == {"c1", "c2"}

    def test_matches_with_country_code(self, conn):
        """Phone with +1 prefix should match without."""
        from dex_python.deduplication import find_phone_duplicates

        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO contacts (id, first_name, last_name) VALUES (?, ?, ?)",
            ("c1", "John", "Doe"),
        )
        cursor.execute(
            "INSERT INTO contacts (id, first_name, last_name) VALUES (?, ?, ?)",
            ("c2", "Jane", "Smith"),
        )
        cursor.execute(
            "INSERT INTO phones (contact_id, phone_number) VALUES (?, ?)",
            ("c1", "+1 555-123-4567"),
        )
        cursor.execute(
            "INSERT INTO phones (contact_id, phone_number) VALUES (?, ?)",
            ("c2", "5551234567"),
        )
        conn.commit()

        results = find_phone_duplicates(conn)
        assert len(results) == 1
        assert set(results[0]["contact_ids"]) == {"c1", "c2"}

    def test_matches_with_dots(self, conn):
        """Phone with dots should match other formats."""
        from dex_python.deduplication import find_phone_duplicates

        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO contacts (id, first_name, last_name) VALUES (?, ?, ?)",
            ("c1", "John", "Doe"),
        )
        cursor.execute(
            "INSERT INTO contacts (id, first_name, last_name) VALUES (?, ?, ?)",
            ("c2", "Jane", "Smith"),
        )
        cursor.execute(
            "INSERT INTO phones (contact_id, phone_number) VALUES (?, ?)",
            ("c1", "555.123.4567"),
        )
        cursor.execute(
            "INSERT INTO phones (contact_id, phone_number) VALUES (?, ?)",
            ("c2", "555 123 4567"),
        )
        conn.commit()

        results = find_phone_duplicates(conn)
        assert len(results) == 1

    def test_different_numbers_no_match(self, conn):
        """Different phone numbers should not match."""
        from dex_python.deduplication import find_phone_duplicates

        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO contacts (id, first_name, last_name) VALUES (?, ?, ?)",
            ("c1", "John", "Doe"),
        )
        cursor.execute(
            "INSERT INTO contacts (id, first_name, last_name) VALUES (?, ?, ?)",
            ("c2", "Jane", "Smith"),
        )
        cursor.execute(
            "INSERT INTO phones (contact_id, phone_number) VALUES (?, ?)",
            ("c1", "555-123-4567"),
        )
        cursor.execute(
            "INSERT INTO phones (contact_id, phone_number) VALUES (?, ?)",
            ("c2", "555-987-6543"),
        )
        conn.commit()

        results = find_phone_duplicates(conn)
        assert len(results) == 0
