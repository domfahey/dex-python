"""Tests for Level 2 (Composite/Rule-Based) duplicate detection."""

import sqlite3

import pytest

from dex_python.deduplication import find_name_and_title_duplicates


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


def test_find_name_title_duplicates_none(db_connection: sqlite3.Connection) -> None:
    """Test finding duplicates when there are none."""
    cursor = db_connection.cursor()
    cursor.execute(
        """
        INSERT INTO contacts (id, first_name, last_name, job_title)
        VALUES ('c1', 'John', 'Doe', 'CEO')
        """
    )
    cursor.execute(
        """
        INSERT INTO contacts (id, first_name, last_name, job_title)
        VALUES ('c2', 'Jane', 'Doe', 'CEO')
        """
    )
    db_connection.commit()

    duplicates = find_name_and_title_duplicates(db_connection)
    assert len(duplicates) == 0


def test_find_name_title_duplicates_exact(db_connection: sqlite3.Connection) -> None:
    """Test finding duplicates with exact name and job title matches."""
    cursor = db_connection.cursor()
    # Same person, two entries
    cursor.execute(
        """
        INSERT INTO contacts (id, first_name, last_name, job_title)
        VALUES ('c1', 'John', 'Doe', 'Engineer')
        """
    )
    cursor.execute(
        """
        INSERT INTO contacts (id, first_name, last_name, job_title)
        VALUES ('c2', 'John', 'Doe', 'Engineer')
        """
    )
    db_connection.commit()

    duplicates = find_name_and_title_duplicates(db_connection)

    assert len(duplicates) == 1
    group = duplicates[0]
    assert group["match_type"] == "name_title"
    assert "john doe" in group["match_value"]
    assert "engineer" in group["match_value"]
    assert set(group["contact_ids"]) == {"c1", "c2"}


def test_find_name_title_duplicates_case_insensitive(
    db_connection: sqlite3.Connection,
) -> None:
    """Test that matching is case-insensitive and trims whitespace."""
    cursor = db_connection.cursor()
    cursor.execute(
        """
        INSERT INTO contacts (id, first_name, last_name, job_title)
        VALUES ('c1', 'John ', 'Doe', 'Manager')
        """
    )
    cursor.execute(
        """
        INSERT INTO contacts (id, first_name, last_name, job_title)
        VALUES ('c2', 'john', 'doe ', 'manager')
        """
    )
    db_connection.commit()

    duplicates = find_name_and_title_duplicates(db_connection)

    assert len(duplicates) == 1
    assert set(duplicates[0]["contact_ids"]) == {"c1", "c2"}


def test_find_name_title_duplicates_ignore_nulls(
    db_connection: sqlite3.Connection,
) -> None:
    """Test that records with missing fields are not matched."""
    cursor = db_connection.cursor()
    # Missing job title should not match even if names match
    cursor.execute(
        """
        INSERT INTO contacts (id, first_name, last_name, job_title)
        VALUES ('c1', 'John', 'Doe', NULL)
        """
    )
    cursor.execute(
        """
        INSERT INTO contacts (id, first_name, last_name, job_title)
        VALUES ('c2', 'John', 'Doe', NULL)
        """
    )
    db_connection.commit()

    duplicates = find_name_and_title_duplicates(db_connection)
    assert len(duplicates) == 0
