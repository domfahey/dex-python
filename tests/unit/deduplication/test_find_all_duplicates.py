"""Tests for find_all_duplicates convenience function."""

import sqlite3

from dex_python.deduplication import find_all_duplicates


def setup_test_db() -> sqlite3.Connection:
    """Create an in-memory test database with contacts."""
    conn = sqlite3.connect(":memory:")
    cursor = conn.cursor()

    # Create schema
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
            id INTEGER PRIMARY KEY,
            contact_id TEXT,
            email TEXT
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


def test_find_all_duplicates_basic() -> None:
    """Test find_all_duplicates with email duplicates."""
    conn = setup_test_db()
    cursor = conn.cursor()

    # Insert contacts with duplicate emails
    cursor.execute(
        "INSERT INTO contacts (id, first_name, last_name) VALUES (?, ?, ?)",
        ("1", "John", "Doe"),
    )
    cursor.execute(
        "INSERT INTO contacts (id, first_name, last_name) VALUES (?, ?, ?)",
        ("2", "Jane", "Doe"),
    )

    cursor.execute(
        "INSERT INTO emails (contact_id, email) VALUES (?, ?)",
        ("1", "john@example.com"),
    )
    cursor.execute(
        "INSERT INTO emails (contact_id, email) VALUES (?, ?)",
        ("2", "john@example.com"),
    )

    conn.commit()

    matches, clusters = find_all_duplicates(conn)

    assert len(matches) > 0
    assert len(clusters) == 1
    assert set(clusters[0]) == {"1", "2"}

    conn.close()


def test_find_all_duplicates_no_duplicates() -> None:
    """Test find_all_duplicates with no duplicates."""
    conn = setup_test_db()
    cursor = conn.cursor()

    # Insert contacts with unique data
    cursor.execute(
        "INSERT INTO contacts (id, first_name, last_name) VALUES (?, ?, ?)",
        ("1", "John", "Doe"),
    )
    cursor.execute(
        "INSERT INTO contacts (id, first_name, last_name) VALUES (?, ?, ?)",
        ("2", "Jane", "Smith"),
    )

    cursor.execute(
        "INSERT INTO emails (contact_id, email) VALUES (?, ?)",
        ("1", "john@example.com"),
    )
    cursor.execute(
        "INSERT INTO emails (contact_id, email) VALUES (?, ?)",
        ("2", "jane@example.com"),
    )

    conn.commit()

    matches, clusters = find_all_duplicates(conn)

    assert len(matches) == 0
    assert len(clusters) == 0

    conn.close()


def test_find_all_duplicates_multiple_signals() -> None:
    """Test find_all_duplicates with multiple duplicate signals."""
    conn = setup_test_db()
    cursor = conn.cursor()

    # Insert contacts with both email and phone duplicates
    cursor.execute(
        "INSERT INTO contacts (id, first_name, last_name) VALUES (?, ?, ?)",
        ("1", "John", "Doe"),
    )
    cursor.execute(
        "INSERT INTO contacts (id, first_name, last_name) VALUES (?, ?, ?)",
        ("2", "John", "Doe"),
    )

    cursor.execute(
        "INSERT INTO emails (contact_id, email) VALUES (?, ?)",
        ("1", "john@example.com"),
    )
    cursor.execute(
        "INSERT INTO emails (contact_id, email) VALUES (?, ?)",
        ("2", "john@example.com"),
    )

    cursor.execute(
        "INSERT INTO phones (contact_id, phone_number) VALUES (?, ?)",
        ("1", "1234567890"),
    )
    cursor.execute(
        "INSERT INTO phones (contact_id, phone_number) VALUES (?, ?)",
        ("2", "1234567890"),
    )

    conn.commit()

    matches, clusters = find_all_duplicates(conn)

    # Should find multiple signals (email and phone)
    assert len(matches) >= 2
    # But only one cluster since they're the same two contacts
    assert len(clusters) == 1
    assert set(clusters[0]) == {"1", "2"}

    conn.close()


def test_find_all_duplicates_custom_threshold() -> None:
    """Test find_all_duplicates with custom fuzzy threshold."""
    conn = setup_test_db()
    cursor = conn.cursor()

    # Insert contacts with similar names
    cursor.execute(
        "INSERT INTO contacts (id, first_name, last_name) VALUES (?, ?, ?)",
        ("1", "John", "Smith"),
    )
    cursor.execute(
        "INSERT INTO contacts (id, first_name, last_name) VALUES (?, ?, ?)",
        ("2", "Jon", "Smith"),
    )

    conn.commit()

    # With high threshold, should not match
    matches_high, clusters_high = find_all_duplicates(conn, fuzzy_threshold=0.99)
    assert len(clusters_high) == 0

    # With lower threshold, might match (depends on similarity score)
    matches_low, clusters_low = find_all_duplicates(conn, fuzzy_threshold=0.85)
    # This test is more about verifying the threshold parameter works
    # The actual result depends on the Jaro-Winkler similarity

    conn.close()
