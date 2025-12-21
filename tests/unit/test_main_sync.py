"""Tests for full sync database schema and inserts."""

import json
import sqlite3

from scripts.main import init_db, insert_contact_data


def test_init_db_creates_name_columns() -> None:
    """Ensure name parsing columns exist in the full sync schema."""
    conn = sqlite3.connect(":memory:")
    cursor = conn.cursor()

    init_db(cursor)

    cursor.execute("PRAGMA table_info(contacts)")
    columns = {row[1] for row in cursor.fetchall()}
    expected = {
        "name_parse_type",
        "name_parsed",
        "name_given",
        "name_middle",
        "name_surname",
        "name_prefix",
        "name_suffix",
        "name_nickname",
    }

    assert expected.issubset(columns)


def test_insert_contact_data_stores_parsed_name() -> None:
    """Insert contacts with parsed name fields."""
    conn = sqlite3.connect(":memory:")
    cursor = conn.cursor()
    init_db(cursor)

    contact = {
        "id": "c1",
        "first_name": "Ada",
        "last_name": "Lovelace",
    }
    insert_contact_data(cursor, contact)
    conn.commit()

    cursor.execute("""
        SELECT name_given, name_surname, name_parsed
        FROM contacts WHERE id = 'c1'
    """)
    row = cursor.fetchone()

    assert row[0] == "Ada"
    assert row[1] == "Lovelace"
    parsed = json.loads(row[2])
    assert parsed["raw"] == "Ada Lovelace"
