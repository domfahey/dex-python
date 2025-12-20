"""Tests for merging duplicate contact data."""

import sqlite3

import pytest

from src.dex_import.deduplication import merge_cluster


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
            phone_number TEXT,
            label TEXT
        )
    """)
    return conn


def test_merge_cluster_basic(db_connection: sqlite3.Connection) -> None:
    """Test merging two contacts into one."""
    cursor = db_connection.cursor()

    # Contact 1: Has Name, no Job Title, Email A
    cursor.execute(
        "INSERT INTO contacts (id, first_name, last_name) VALUES ('c1', 'John', 'Doe')"
    )
    cursor.execute("INSERT INTO emails (contact_id, email) VALUES ('c1', 'john@a.com')")

    # Contact 2: Has Name, Job Title, Email B
    cursor.execute(
        """
        INSERT INTO contacts (id, first_name, last_name, job_title)
        VALUES ('c2', 'John', 'Doe', 'CEO')
        """
    )
    cursor.execute("INSERT INTO emails (contact_id, email) VALUES ('c2', 'john@b.com')")

    db_connection.commit()

    # Merge c1 and c2
    primary_id = merge_cluster(db_connection, ["c1", "c2"])

    # Verify: One contact should remain, with combined data
    cursor.execute("SELECT count(*) FROM contacts")
    assert cursor.fetchone()[0] == 1

    cursor.execute("SELECT id, job_title FROM contacts")
    row = cursor.fetchone()
    assert row[0] == primary_id
    assert row[1] == "CEO"  # Should have taken the non-null job title

    # Verify emails are combined
    cursor.execute("SELECT email FROM emails")
    emails = {r[0] for r in cursor.fetchall()}
    assert emails == {"john@a.com", "john@b.com"}

    # Verify all remaining emails point to primary_id
    cursor.execute("SELECT contact_id FROM emails")
    for r in cursor.fetchall():
        assert r[0] == primary_id


def test_merge_cluster_removes_duplicates(db_connection: sqlite3.Connection) -> None:
    """Test that merging handles duplicate data entries (e.g. same email in both)."""
    cursor = db_connection.cursor()

    cursor.execute(
        "INSERT INTO contacts (id, first_name, last_name) VALUES ('c1', 'John', 'Doe')"
    )
    cursor.execute("INSERT INTO emails (contact_id, email) VALUES ('c1', 'shared@com')")

    cursor.execute(
        "INSERT INTO contacts (id, first_name, last_name) VALUES ('c2', 'John', 'Doe')"
    )
    cursor.execute("INSERT INTO emails (contact_id, email) VALUES ('c2', 'shared@com')")

    db_connection.commit()

    merge_cluster(db_connection, ["c1", "c2"])

    # Verify only one email record remains
    cursor.execute("SELECT count(*) FROM emails")
    assert cursor.fetchone()[0] == 1
