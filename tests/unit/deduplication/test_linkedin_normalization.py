"""Tests for LinkedIn URL normalization in deduplication.

TDD tests for finding duplicate contacts by LinkedIn profile URL.
"""

import sqlite3

import pytest


@pytest.fixture
def conn():
    """
    Create an in-memory SQLite database initialized with the test contacts schema and index.
    
    Returns:
        sqlite3.Connection: Connection to the in-memory database with the `contacts` table and `idx_contacts_linkedin` index already created and committed.
    """
    conn = sqlite3.connect(":memory:")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE contacts (
            id TEXT PRIMARY KEY,
            first_name TEXT,
            last_name TEXT,
            linkedin TEXT
        )
    """)
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_contacts_linkedin ON contacts(linkedin)"
    )
    conn.commit()
    return conn


class TestLinkedInDuplicates:
    """Test LinkedIn duplicate detection with URL normalization."""

    def test_matches_different_url_formats(self, conn):
        """Different LinkedIn URL formats should match as duplicates."""
        from dex_python.deduplication import find_linkedin_duplicates

        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO contacts (id, first_name, last_name, linkedin) "
            "VALUES (?, ?, ?, ?)",
            ("c1", "John", "Doe", "https://www.linkedin.com/in/johndoe"),
        )
        cursor.execute(
            "INSERT INTO contacts (id, first_name, last_name, linkedin) "
            "VALUES (?, ?, ?, ?)",
            ("c2", "John", "D", "linkedin.com/in/johndoe"),
        )
        conn.commit()

        results = find_linkedin_duplicates(conn)
        assert len(results) == 1
        assert set(results[0]["contact_ids"]) == {"c1", "c2"}

    def test_matches_username_only(self, conn):
        """Username-only should match full URL."""
        from dex_python.deduplication import find_linkedin_duplicates

        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO contacts (id, first_name, last_name, linkedin) "
            "VALUES (?, ?, ?, ?)",
            ("c1", "John", "Doe", "johndoe"),
        )
        cursor.execute(
            "INSERT INTO contacts (id, first_name, last_name, linkedin) "
            "VALUES (?, ?, ?, ?)",
            ("c2", "John", "D", "https://linkedin.com/in/johndoe/"),
        )
        conn.commit()

        results = find_linkedin_duplicates(conn)
        assert len(results) == 1
        assert set(results[0]["contact_ids"]) == {"c1", "c2"}

    def test_case_insensitive_matching(self, conn):
        """LinkedIn matching should be case-insensitive."""
        from dex_python.deduplication import find_linkedin_duplicates

        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO contacts (id, first_name, last_name, linkedin) "
            "VALUES (?, ?, ?, ?)",
            ("c1", "John", "Doe", "JohnDoe"),
        )
        cursor.execute(
            "INSERT INTO contacts (id, first_name, last_name, linkedin) "
            "VALUES (?, ?, ?, ?)",
            ("c2", "John", "D", "johndoe"),
        )
        conn.commit()

        results = find_linkedin_duplicates(conn)
        assert len(results) == 1

    def test_different_profiles_no_match(self, conn):
        """Different LinkedIn profiles should not match."""
        from dex_python.deduplication import find_linkedin_duplicates

        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO contacts (id, first_name, last_name, linkedin) "
            "VALUES (?, ?, ?, ?)",
            ("c1", "John", "Doe", "johndoe"),
        )
        cursor.execute(
            "INSERT INTO contacts (id, first_name, last_name, linkedin) "
            "VALUES (?, ?, ?, ?)",
            ("c2", "Jane", "Smith", "janesmith"),
        )
        conn.commit()

        results = find_linkedin_duplicates(conn)
        assert len(results) == 0

    def test_handles_null_linkedin(self, conn):
        """Contacts with NULL linkedin should be excluded."""
        from dex_python.deduplication import find_linkedin_duplicates

        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO contacts (id, first_name, last_name, linkedin) "
            "VALUES (?, ?, ?, ?)",
            ("c1", "John", "Doe", None),
        )
        cursor.execute(
            "INSERT INTO contacts (id, first_name, last_name, linkedin) "
            "VALUES (?, ?, ?, ?)",
            ("c2", "Jane", "Smith", "janesmith"),
        )
        conn.commit()

        results = find_linkedin_duplicates(conn)
        assert len(results) == 0

    def test_handles_empty_linkedin(self, conn):
        """Contacts with empty linkedin should be excluded."""
        from dex_python.deduplication import find_linkedin_duplicates

        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO contacts (id, first_name, last_name, linkedin) "
            "VALUES (?, ?, ?, ?)",
            ("c1", "John", "Doe", ""),
        )
        cursor.execute(
            "INSERT INTO contacts (id, first_name, last_name, linkedin) "
            "VALUES (?, ?, ?, ?)",
            ("c2", "Jane", "Smith", "janesmith"),
        )
        conn.commit()

        results = find_linkedin_duplicates(conn)
        assert len(results) == 0

    def test_strips_query_parameters(self, conn):
        """LinkedIn URLs with query params should match clean URLs."""
        from dex_python.deduplication import find_linkedin_duplicates

        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO contacts (id, first_name, last_name, linkedin) "
            "VALUES (?, ?, ?, ?)",
            ("c1", "John", "Doe", "https://linkedin.com/in/johndoe?utm_source=email"),
        )
        cursor.execute(
            "INSERT INTO contacts (id, first_name, last_name, linkedin) "
            "VALUES (?, ?, ?, ?)",
            ("c2", "John", "D", "linkedin.com/in/johndoe"),
        )
        conn.commit()

        results = find_linkedin_duplicates(conn)
        assert len(results) == 1

    def test_returns_correct_structure(self, conn):
        """Results should have expected keys."""
        from dex_python.deduplication import find_linkedin_duplicates

        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO contacts (id, first_name, last_name, linkedin) "
            "VALUES (?, ?, ?, ?)",
            ("c1", "John", "Doe", "johndoe"),
        )
        cursor.execute(
            "INSERT INTO contacts (id, first_name, last_name, linkedin) "
            "VALUES (?, ?, ?, ?)",
            ("c2", "John", "D", "johndoe"),
        )
        conn.commit()

        results = find_linkedin_duplicates(conn)
        assert len(results) == 1
        result = results[0]
        assert "match_type" in result
        assert result["match_type"] == "linkedin"
        assert "match_value" in result
        assert "contact_ids" in result

    def test_multiple_duplicate_groups(self, conn):
        """Multiple distinct duplicate groups should be found."""
        from dex_python.deduplication import find_linkedin_duplicates

        cursor = conn.cursor()
        # Group 1: johndoe
        cursor.execute(
            "INSERT INTO contacts (id, first_name, last_name, linkedin) "
            "VALUES (?, ?, ?, ?)",
            ("c1", "John", "Doe", "johndoe"),
        )
        cursor.execute(
            "INSERT INTO contacts (id, first_name, last_name, linkedin) "
            "VALUES (?, ?, ?, ?)",
            ("c2", "John", "D", "johndoe"),
        )
        # Group 2: janesmith
        cursor.execute(
            "INSERT INTO contacts (id, first_name, last_name, linkedin) "
            "VALUES (?, ?, ?, ?)",
            ("c3", "Jane", "Smith", "janesmith"),
        )
        cursor.execute(
            "INSERT INTO contacts (id, first_name, last_name, linkedin) "
            "VALUES (?, ?, ?, ?)",
            ("c4", "Jane", "S", "https://linkedin.com/in/janesmith"),
        )
        conn.commit()

        results = find_linkedin_duplicates(conn)
        assert len(results) == 2