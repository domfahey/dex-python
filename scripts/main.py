"""Script to download all contacts from Dex API and save to SQLite.

WARNING: This script performs a FULL SYNC which drops and recreates all tables.
Use sync_with_integrity.py for incremental updates that preserve metadata.
"""

import json
import os
import sqlite3
import sys
from pathlib import Path
from typing import Any

from dex_python import DexClient
from dex_python.name_parsing import parse_contact_name


def init_db(cursor: sqlite3.Cursor) -> None:
    """Initialize the SQLite database with normalized tables."""
    # Drop existing tables to ensure schema update
    cursor.execute("DROP TABLE IF EXISTS emails")
    cursor.execute("DROP TABLE IF EXISTS phones")
    cursor.execute("DROP TABLE IF EXISTS contacts")

    # Main contacts table
    cursor.execute("""
        CREATE TABLE contacts (
            id TEXT PRIMARY KEY,
            first_name TEXT,
            last_name TEXT,
            name_parse_type TEXT,
            name_parsed JSON,
            name_given TEXT,
            name_middle TEXT,
            name_surname TEXT,
            name_prefix TEXT,
            name_suffix TEXT,
            name_nickname TEXT,
            job_title TEXT,
            linkedin TEXT,
            website TEXT,
            full_data JSON
        )
    """)

    # Emails table (one-to-many)
    cursor.execute("""
        CREATE TABLE emails (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            contact_id TEXT,
            email TEXT,
            FOREIGN KEY(contact_id) REFERENCES contacts(id)
        )
    """)

    # Phones table (one-to-many)
    cursor.execute("""
        CREATE TABLE phones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            contact_id TEXT,
            phone_number TEXT,
            label TEXT,
            FOREIGN KEY(contact_id) REFERENCES contacts(id)
        )
    """)

    # Create indexes for performance optimization
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_emails_contact_id ON emails(contact_id)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_emails_email_lower ON emails(lower(email))"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_phones_contact_id ON phones(contact_id)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_phones_number ON phones(phone_number)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_contacts_name "
        "ON contacts(first_name, last_name)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_contacts_job_title ON contacts(job_title)"
    )


def insert_contact_data(cursor: sqlite3.Cursor, contact: dict[str, Any]) -> None:
    """Insert contact and related data into database."""
    c_id = contact.get("id")

    # Insert main contact
    name_fields = parse_contact_name(contact)
    cursor.execute(
        """
        INSERT INTO contacts (
            id, first_name, last_name, name_parse_type, name_parsed, name_given,
            name_middle, name_surname, name_prefix, name_suffix, name_nickname,
            job_title, linkedin, website, full_data
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            c_id,
            contact.get("first_name"),
            contact.get("last_name"),
            name_fields["name_parse_type"],
            name_fields["name_parsed"],
            name_fields["name_given"],
            name_fields["name_middle"],
            name_fields["name_surname"],
            name_fields["name_prefix"],
            name_fields["name_suffix"],
            name_fields["name_nickname"],
            contact.get("job_title"),
            contact.get("linkedin"),
            contact.get("website"),
            json.dumps(contact),
        ),
    )

    # Insert emails
    for email_item in contact.get("emails", []):
        email_addr = email_item.get("email")
        if email_addr:
            cursor.execute(
                "INSERT INTO emails (contact_id, email) VALUES (?, ?)",
                (c_id, email_addr),
            )

    # Insert phones
    for phone_item in contact.get("phones", []):
        phone_num = phone_item.get("phone_number")
        label = phone_item.get("label")
        if phone_num:
            cursor.execute(
                "INSERT INTO phones (contact_id, phone_number, label) VALUES (?, ?, ?)",
                (c_id, phone_num, label),
            )


def main() -> None:
    """Fetch all contacts and save to database."""
    data_dir = Path(os.getenv("DEX_DATA_DIR", "output"))
    data_dir.mkdir(parents=True, exist_ok=True)
    db_path = data_dir / "dex_contacts.db"

    # Warn about destructive operation
    if db_path.exists():
        print("WARNING: This will DROP all tables and lose dedup metadata!")
        print("For incremental sync, use: uv run python sync_with_integrity.py")
        if "--force" not in sys.argv:
            response = input("Continue with full sync? [y/N]: ")
            if response.lower() != "y":
                print("Aborted. Use sync_with_integrity.py for incremental sync.")
                return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Enable foreign keys
    cursor.execute("PRAGMA foreign_keys = ON")

    init_db(cursor)

    batch_size = 100
    offset = 0
    total_synced = 0

    print(f"Syncing contacts with details to {db_path}...")

    try:
        with DexClient() as client:
            while True:
                print(f"Fetching batch offset={offset} limit={batch_size}...")
                contacts = client.get_contacts(limit=batch_size, offset=offset)

                if not contacts:
                    break

                for contact in contacts:
                    insert_contact_data(cursor, contact)

                conn.commit()

                count = len(contacts)
                total_synced += count
                offset += count

                print(f"Synced {count} contacts. Total: {total_synced}")

                if count < batch_size:
                    break

    except Exception as e:
        print(f"Error during sync: {e}")
        conn.rollback()
    finally:
        conn.close()
        print(f"Done! Total contacts synced: {total_synced}")


if __name__ == "__main__":
    main()
