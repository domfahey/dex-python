"""Tests for birthday-based duplicate detection."""

import json
import sqlite3
from typing import Generator

import pytest

from dex_python.deduplication import find_birthday_name_duplicates


@pytest.fixture
def db_connection() -> Generator[sqlite3.Connection, None, None]:
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

    yield conn
    conn.close()


def insert_contact(
    cursor: sqlite3.Cursor,
    contact_id: str,
    first_name: str,
    last_name: str,
    birthday: str | None = None,
) -> None:
    """Helper to insert a contact with optional birthday."""
    full_data = {"birthday": birthday} if birthday else {}
    cursor.execute(
        """INSERT INTO contacts (id, first_name, last_name, full_data)
        VALUES (?, ?, ?, ?)""",
        (contact_id, first_name, last_name, json.dumps(full_data)),
    )


class TestBirthdayNameDuplicates:
    """Tests for find_birthday_name_duplicates."""

    def test_same_name_same_birthday(self, db_connection: sqlite3.Connection) -> None:
        """Two contacts with same name and birthday should be flagged."""
        cursor = db_connection.cursor()
        insert_contact(cursor, "c1", "Melissa", "Conklin", "2022-02-28")
        # Same month-day (02-28), different year
        insert_contact(cursor, "c2", "Melissa", "Conklin", "2023-02-28")
        db_connection.commit()

        results = find_birthday_name_duplicates(db_connection)

        assert len(results) == 1
        assert results[0]["match_type"] == "birthday_name"
        assert set(results[0]["contact_ids"]) == {"c1", "c2"}

    def test_same_name_different_birthday(
        self, db_connection: sqlite3.Connection
    ) -> None:
        """Same name but different birthdays should not match."""
        cursor = db_connection.cursor()
        insert_contact(cursor, "c1", "John", "Doe", "2022-03-15")
        insert_contact(cursor, "c2", "John", "Doe", "2022-07-20")
        db_connection.commit()

        results = find_birthday_name_duplicates(db_connection)

        assert len(results) == 0

    def test_different_name_same_birthday(
        self, db_connection: sqlite3.Connection
    ) -> None:
        """Different names with same birthday should not match."""
        cursor = db_connection.cursor()
        insert_contact(cursor, "c1", "John", "Smith", "2022-05-10")
        insert_contact(cursor, "c2", "Jane", "Doe", "2022-05-10")
        db_connection.commit()

        results = find_birthday_name_duplicates(db_connection)

        assert len(results) == 0

    def test_excludes_placeholder_date(self, db_connection: sqlite3.Connection) -> None:
        """Placeholder date 2001-01-01 should be excluded."""
        cursor = db_connection.cursor()
        insert_contact(cursor, "c1", "John", "Doe", "2001-01-01")
        insert_contact(cursor, "c2", "John", "Doe", "2001-01-01")
        db_connection.commit()

        results = find_birthday_name_duplicates(db_connection)

        assert len(results) == 0

    def test_case_insensitive_name(self, db_connection: sqlite3.Connection) -> None:
        """Name matching should be case-insensitive."""
        cursor = db_connection.cursor()
        insert_contact(cursor, "c1", "JOHN", "DOE", "2022-06-15")
        insert_contact(cursor, "c2", "john", "doe", "2023-06-15")
        db_connection.commit()

        results = find_birthday_name_duplicates(db_connection)

        assert len(results) == 1
        assert set(results[0]["contact_ids"]) == {"c1", "c2"}

    def test_no_birthday_data(self, db_connection: sqlite3.Connection) -> None:
        """Contacts without birthday data should not match."""
        cursor = db_connection.cursor()
        insert_contact(cursor, "c1", "John", "Doe", None)
        insert_contact(cursor, "c2", "John", "Doe", None)
        db_connection.commit()

        results = find_birthday_name_duplicates(db_connection)

        assert len(results) == 0
