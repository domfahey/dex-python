"""Tests for Level 1 (Deterministic) duplicate detection."""

import sqlite3
from typing import Generator

import pytest

from dex_python.deduplication import find_email_duplicates, find_phone_duplicates


@pytest.fixture
def db_connection() -> Generator[sqlite3.Connection, None, None]:
    """Create an in-memory SQLite database for testing."""
    conn = sqlite3.connect(":memory:")
    cursor = conn.cursor()

    # Create tables matching the production schema
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

    cursor.execute("""
        CREATE TABLE emails (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            contact_id TEXT,
            email TEXT,
            FOREIGN KEY(contact_id) REFERENCES contacts(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE phones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            contact_id TEXT,
            phone_number TEXT,
            label TEXT,
            FOREIGN KEY(contact_id) REFERENCES contacts(id)
        )
    """)

    yield conn
    conn.close()


def test_find_email_duplicates_none(db_connection: sqlite3.Connection) -> None:
    """Test finding duplicates when there are none."""
    cursor = db_connection.cursor()
    # Insert unique contacts
    cursor.execute("INSERT INTO contacts (id) VALUES ('c1'), ('c2')")
    cursor.execute(
        "INSERT INTO emails (contact_id, email) VALUES ('c1', 'a@example.com')"
    )
    cursor.execute(
        "INSERT INTO emails (contact_id, email) VALUES ('c2', 'b@example.com')"
    )
    db_connection.commit()

    duplicates = find_email_duplicates(db_connection)
    assert len(duplicates) == 0


def test_find_email_duplicates_basic(db_connection: sqlite3.Connection) -> None:
    """Test finding a basic pair of duplicates sharing an email."""
    cursor = db_connection.cursor()
    # Insert duplicate contacts
    cursor.execute("INSERT INTO contacts (id) VALUES ('c1'), ('c2')")
    cursor.execute(
        "INSERT INTO emails (contact_id, email) VALUES ('c1', 'shared@example.com')"
    )
    cursor.execute(
        "INSERT INTO emails (contact_id, email) VALUES ('c2', 'shared@example.com')"
    )
    db_connection.commit()

    duplicates = find_email_duplicates(db_connection)

    # Should find 1 group
    assert len(duplicates) == 1

    group = duplicates[0]
    assert group["match_type"] == "email"
    assert group["match_value"] == "shared@example.com"
    # Set comparison because order is not guaranteed
    assert set(group["contact_ids"]) == {"c1", "c2"}


def test_find_email_duplicates_case_insensitive(
    db_connection: sqlite3.Connection,
) -> None:
    """Test that email matching is case-insensitive."""
    cursor = db_connection.cursor()
    cursor.execute("INSERT INTO contacts (id) VALUES ('c1'), ('c2')")
    cursor.execute(
        "INSERT INTO emails (contact_id, email) VALUES ('c1', 'test@EXAMPLE.com')"
    )
    cursor.execute(
        "INSERT INTO emails (contact_id, email) VALUES ('c2', 'TEST@example.com')"
    )
    db_connection.commit()

    duplicates = find_email_duplicates(db_connection)
    assert len(duplicates) == 1
    assert set(duplicates[0]["contact_ids"]) == {"c1", "c2"}


def test_find_phone_duplicates_basic(db_connection: sqlite3.Connection) -> None:
    """Test finding duplicates sharing a phone number."""
    cursor = db_connection.cursor()
    cursor.execute("INSERT INTO contacts (id) VALUES ('c1'), ('c2')")
    cursor.execute(
        "INSERT INTO phones (contact_id, phone_number) VALUES ('c1', '555-0100')"
    )
    cursor.execute(
        "INSERT INTO phones (contact_id, phone_number) VALUES ('c2', '555-0100')"
    )
    db_connection.commit()

    duplicates = find_phone_duplicates(db_connection)

    assert len(duplicates) == 1
    assert set(duplicates[0]["contact_ids"]) == {"c1", "c2"}
    assert duplicates[0]["match_type"] == "phone"
