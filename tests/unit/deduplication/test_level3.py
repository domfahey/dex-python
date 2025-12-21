"""Tests for Level 3 (Fuzzy/Phonetic) duplicate detection."""

import sqlite3

import pytest

from dex_python.deduplication import find_fuzzy_name_duplicates


@pytest.fixture
def db_connection() -> sqlite3.Connection:
    """Create an in-memory SQLite database for testing."""
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
            full_data JSON
        )
    """)
    return conn


def test_find_fuzzy_name_duplicates_typo(db_connection: sqlite3.Connection) -> None:
    """Test finding duplicates with slight typos (Levenshtein/Jaro-Winkler)."""
    cursor = db_connection.cursor()
    # "Jonathon" vs "Jonathan"
    cursor.execute(
        """
        INSERT INTO contacts (id, first_name, last_name)
        VALUES ('c1', 'Jonathan', 'Smith')
        """
    )
    cursor.execute(
        """
        INSERT INTO contacts (id, first_name, last_name)
        VALUES ('c2', 'Jonathon', 'Smith')
        """
    )
    # Control: Different person
    cursor.execute(
        """
        INSERT INTO contacts (id, first_name, last_name)
        VALUES ('c3', 'David', 'Smith')
        """
    )
    db_connection.commit()

    duplicates = find_fuzzy_name_duplicates(db_connection, threshold=0.9)

    assert len(duplicates) == 1
    group = duplicates[0]
    assert group["match_type"] == "fuzzy_name"
    assert set(group["contact_ids"]) == {"c1", "c2"}
    assert "c3" not in group["contact_ids"]


def test_find_fuzzy_name_duplicates_phonetic(db_connection: sqlite3.Connection) -> None:
    """Test finding duplicates with phonetic similarity."""
    cursor = db_connection.cursor()
    # "Cathy" vs "Kathy"
    cursor.execute(
        """
        INSERT INTO contacts (id, first_name, last_name)
        VALUES ('c1', 'Cathy', 'Miller')
        """
    )
    cursor.execute(
        """
        INSERT INTO contacts (id, first_name, last_name)
        VALUES ('c2', 'Kathy', 'Miller')
        """
    )
    db_connection.commit()

    duplicates = find_fuzzy_name_duplicates(db_connection, threshold=0.85)

    assert len(duplicates) == 1
    assert set(duplicates[0]["contact_ids"]) == {"c1", "c2"}


def test_find_fuzzy_name_blocking(db_connection: sqlite3.Connection) -> None:
    """Test that blocking prevents comparison of disparate records."""
    cursor = db_connection.cursor()
    # "John Smith" vs "John Smyth" (Should match if in same block)
    cursor.execute(
        """
        INSERT INTO contacts (id, first_name, last_name)
        VALUES ('c1', 'John', 'Smith')
        """
    )
    cursor.execute(
        """
        INSERT INTO contacts (id, first_name, last_name)
        VALUES ('c2', 'John', 'Smyth')
        """
    )

    # "John Doe" (Different block entirely)
    cursor.execute(
        """
        INSERT INTO contacts (id, first_name, last_name)
        VALUES ('c3', 'John', 'Doe')
        """
    )
    db_connection.commit()

    duplicates = find_fuzzy_name_duplicates(db_connection)

    # Should only match Smith/Smyth
    match_found = False
    for group in duplicates:
        if "c1" in group["contact_ids"]:
            match_found = True
            assert "c2" in group["contact_ids"]
            assert "c3" not in group["contact_ids"]

    assert match_found


def test_fuzzy_ignores_incomplete_names(db_connection: sqlite3.Connection) -> None:
    """Test that records without first or last names are ignored."""
    cursor = db_connection.cursor()
    cursor.execute(
        """
        INSERT INTO contacts (id, first_name, last_name)
        VALUES ('c1', 'John', NULL)
        """
    )
    cursor.execute(
        """
        INSERT INTO contacts (id, first_name, last_name)
        VALUES ('c2', 'John', 'Smith')
        """
    )
    db_connection.commit()

    duplicates = find_fuzzy_name_duplicates(db_connection)
    assert len(duplicates) == 0
