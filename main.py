"""Script to download all contacts from Dex API and save to SQLite.

Detailed tables version.
"""

import json
import sqlite3
from typing import Any

from src.dex_import import DexClient


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


def insert_contact_data(cursor: sqlite3.Cursor, contact: dict[str, Any]) -> None:
    """Insert contact and related data into database."""
    c_id = contact.get("id")

    # Insert main contact
    cursor.execute(
        """
        INSERT INTO contacts (
            id, first_name, last_name, job_title, linkedin, website, full_data
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            c_id,
            contact.get("first_name"),
            contact.get("last_name"),
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
    db_path = "dex_contacts.db"
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
