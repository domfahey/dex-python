"""Tests for fingerprint-based name matching in deduplication.

TDD tests for finding duplicates using OpenRefine-style fingerprints.
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
    conn.commit()
    return conn


class TestFingerprintNameDuplicates:
    """Test fingerprint-based name duplicate detection."""

    def test_matches_reordered_names(self, conn):
        """'Tom Cruise' should match 'Cruise, Tom'."""
        from dex_python.deduplication import find_fingerprint_name_duplicates

        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO contacts (id, first_name, last_name) VALUES (?, ?, ?)",
            ("c1", "Tom", "Cruise"),
        )
        cursor.execute(
            "INSERT INTO contacts (id, first_name, last_name) VALUES (?, ?, ?)",
            ("c2", "Cruise", "Tom"),
        )
        conn.commit()

        results = find_fingerprint_name_duplicates(conn)
        assert len(results) == 1
        assert set(results[0]["contact_ids"]) == {"c1", "c2"}
        assert results[0]["match_type"] == "fingerprint_name"

    def test_matches_unicode_normalized(self, conn):
        """'José García' should match 'Jose Garcia'."""
        from dex_python.deduplication import find_fingerprint_name_duplicates

        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO contacts (id, first_name, last_name) VALUES (?, ?, ?)",
            ("c1", "José", "García"),
        )
        cursor.execute(
            "INSERT INTO contacts (id, first_name, last_name) VALUES (?, ?, ?)",
            ("c2", "Jose", "Garcia"),
        )
        conn.commit()

        results = find_fingerprint_name_duplicates(conn)
        assert len(results) == 1
        assert set(results[0]["contact_ids"]) == {"c1", "c2"}

    def test_matches_case_insensitive(self, conn):
        """'JOHN DOE' should match 'john doe'."""
        from dex_python.deduplication import find_fingerprint_name_duplicates

        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO contacts (id, first_name, last_name) VALUES (?, ?, ?)",
            ("c1", "JOHN", "DOE"),
        )
        cursor.execute(
            "INSERT INTO contacts (id, first_name, last_name) VALUES (?, ?, ?)",
            ("c2", "john", "doe"),
        )
        conn.commit()

        results = find_fingerprint_name_duplicates(conn)
        assert len(results) == 1

    def test_matches_with_punctuation(self, conn):
        """'O'Brien' should match 'OBrien'."""
        from dex_python.deduplication import find_fingerprint_name_duplicates

        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO contacts (id, first_name, last_name) VALUES (?, ?, ?)",
            ("c1", "Sean", "O'Brien"),
        )
        cursor.execute(
            "INSERT INTO contacts (id, first_name, last_name) VALUES (?, ?, ?)",
            ("c2", "Sean", "OBrien"),
        )
        conn.commit()

        results = find_fingerprint_name_duplicates(conn)
        assert len(results) == 1

    def test_no_match_different_names(self, conn):
        """Different names should not match."""
        from dex_python.deduplication import find_fingerprint_name_duplicates

        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO contacts (id, first_name, last_name) VALUES (?, ?, ?)",
            ("c1", "John", "Smith"),
        )
        cursor.execute(
            "INSERT INTO contacts (id, first_name, last_name) VALUES (?, ?, ?)",
            ("c2", "Jane", "Doe"),
        )
        conn.commit()

        results = find_fingerprint_name_duplicates(conn)
        assert len(results) == 0

    def test_handles_empty_names(self, conn):
        """Empty names should not cause errors."""
        from dex_python.deduplication import find_fingerprint_name_duplicates

        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO contacts (id, first_name, last_name) VALUES (?, ?, ?)",
            ("c1", "", "Smith"),
        )
        cursor.execute(
            "INSERT INTO contacts (id, first_name, last_name) VALUES (?, ?, ?)",
            ("c2", "John", ""),
        )
        conn.commit()

        results = find_fingerprint_name_duplicates(conn)
        assert len(results) == 0


class TestEnhancedFuzzyMatching:
    """Test enhanced fuzzy matching with ensemble similarity."""

    def test_uses_ensemble_similarity(self, conn):
        """Fuzzy matching should use ensemble (JW + Levenshtein)."""
        from dex_python.deduplication import find_fuzzy_name_duplicates

        cursor = conn.cursor()
        # Names that are very similar
        cursor.execute(
            "INSERT INTO contacts (id, first_name, last_name) VALUES (?, ?, ?)",
            ("c1", "Jonathan", "Smith"),
        )
        cursor.execute(
            "INSERT INTO contacts (id, first_name, last_name) VALUES (?, ?, ?)",
            ("c2", "Jonathon", "Smith"),
        )
        conn.commit()

        results = find_fuzzy_name_duplicates(conn, threshold=0.9)
        assert len(results) >= 1

    def test_catches_typos_with_lower_threshold(self, conn):
        """Typos should be caught with appropriate threshold."""
        from dex_python.deduplication import find_fuzzy_name_duplicates

        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO contacts (id, first_name, last_name) VALUES (?, ?, ?)",
            ("c1", "Krzysztof", "Kowalski"),
        )
        cursor.execute(
            "INSERT INTO contacts (id, first_name, last_name) VALUES (?, ?, ?)",
            ("c2", "Krzystof", "Kowalski"),
        )
        conn.commit()

        # With high threshold might miss, but should catch
        results = find_fuzzy_name_duplicates(conn, threshold=0.85)
        assert len(results) >= 1
