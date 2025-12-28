"""Robust sync script with concurrency, integrity checks, and error handling.

Now supports Contacts, Reminders, and Timeline Items (Notes).
"""

import asyncio
import hashlib
import json
import sqlite3
from datetime import UTC, datetime
from typing import Any

from rich.console import Console
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn

from dex_python.async_client import AsyncDexClient
from dex_python.enrichment import parse_job_title
from dex_python.models import (
    PaginatedContacts,
    PaginatedNotes,
    PaginatedReminders,
)
from dex_python.name_parsing import parse_contact_name

DB_PATH = "dex_contacts.db"
BATCH_Size = 100
CONCURRENCY = 5

console = Console()


def init_db(conn: sqlite3.Connection) -> None:
    """Initialize database with tables for contacts, reminders, and notes."""
    cursor = conn.cursor()

    # --- Contacts (Existing) ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS contacts (
            id TEXT PRIMARY KEY,
            first_name TEXT,
            last_name TEXT,
            job_title TEXT,
            linkedin TEXT,
            website TEXT,
            full_data JSON,
            record_hash TEXT,
            last_synced_at TIMESTAMP,
            duplicate_group_id TEXT,
            duplicate_resolution TEXT,
            primary_contact_id TEXT
        )
    """)

    # Ensure contact columns exist (for existing DBs)
    contact_cols = [
        ("record_hash", "TEXT"),
        ("last_synced_at", "TIMESTAMP"),
        ("duplicate_group_id", "TEXT"),
        ("duplicate_resolution", "TEXT"),
        ("primary_contact_id", "TEXT"),
        ("full_data", "JSON"),
        # Name parsing columns
        ("name_given", "TEXT"),
        ("name_surname", "TEXT"),
        ("name_parsed", "JSON"),
        # Enrichment columns
        ("company", "TEXT"),
        ("role", "TEXT"),
    ]
    for col_name, col_type in contact_cols:
        try:
            cursor.execute(f"ALTER TABLE contacts ADD COLUMN {col_name} {col_type}")
        except sqlite3.OperationalError:
            pass

    # --- Derived Tables (Existing) ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS emails (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            contact_id TEXT,
            email TEXT,
            FOREIGN KEY(contact_id) REFERENCES contacts(id)
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS phones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            contact_id TEXT,
            phone_number TEXT,
            label TEXT,
            FOREIGN KEY(contact_id) REFERENCES contacts(id)
        )
    """)

    # --- Reminders (New) ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reminders (
            id TEXT PRIMARY KEY,
            body TEXT,
            is_complete BOOLEAN,
            due_date TEXT,
            full_data JSON,
            record_hash TEXT,
            last_synced_at TIMESTAMP
        )
    """)
    # Reminder-Contact Link Table (Many-to-Many)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reminder_contacts (
            reminder_id TEXT,
            contact_id TEXT,
            FOREIGN KEY(reminder_id) REFERENCES reminders(id),
            FOREIGN KEY(contact_id) REFERENCES contacts(id),
            PRIMARY KEY (reminder_id, contact_id)
        )
    """)

    # --- Notes/Timeline Items (New) ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS notes (
            id TEXT PRIMARY KEY,
            note TEXT,
            event_time TIMESTAMP,
            full_data JSON,
            record_hash TEXT,
            last_synced_at TIMESTAMP
        )
    """)
    # Note-Contact Link Table (Many-to-Many)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS note_contacts (
            note_id TEXT,
            contact_id TEXT,
            FOREIGN KEY(note_id) REFERENCES notes(id),
            FOREIGN KEY(contact_id) REFERENCES contacts(id),
            PRIMARY KEY (note_id, contact_id)
        )
    """)

    # Create indexes for performance optimization
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_emails_contact_id ON emails(contact_id)"
    )
    # Functional index supports case-insensitive email lookups.
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
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_contacts_hash ON contacts(record_hash)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_reminder_contacts_reminder "
        "ON reminder_contacts(reminder_id)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_reminder_contacts_contact "
        "ON reminder_contacts(contact_id)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_note_contacts_note ON note_contacts(note_id)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_note_contacts_contact "
        "ON note_contacts(contact_id)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_reminders_hash ON reminders(record_hash)"
    )
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_notes_hash ON notes(record_hash)")

    # Performance indexes for deduplication queries
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_contacts_duplicate_group "
        "ON contacts(duplicate_group_id)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_contacts_linkedin ON contacts(linkedin)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_contacts_website ON contacts(website)"
    )

    conn.commit()


def compute_hash(data: dict[str, Any]) -> str:
    """Compute SHA256 hash of data for integrity check."""
    json_str = json.dumps(data, sort_keys=True)
    return hashlib.sha256(json_str.encode("utf-8")).hexdigest()


def save_contacts_batch(
    conn: sqlite3.Connection,
    items: list[dict[str, Any]],
) -> tuple[int, int, int]:
    """Save contacts to DB with name parsing, enrichment, and dedup preservation."""
    cursor = conn.cursor()
    added = 0
    updated = 0
    unchanged = 0

    for item in items:
        c_id = item.get("id")
        if not c_id:
            continue

        new_hash = compute_hash(item)
        cursor.execute(
            """SELECT record_hash, duplicate_group_id, duplicate_resolution,
               primary_contact_id FROM contacts WHERE id = ?""",
            (c_id,),
        )
        row = cursor.fetchone()

        # Preserve dedup metadata from existing record
        existing_dedup = None
        if row:
            if row[0] == new_hash:
                unchanged += 1
                continue
            updated += 1
            existing_dedup = {
                "duplicate_group_id": row[1],
                "duplicate_resolution": row[2],
                "primary_contact_id": row[3],
            }
        else:
            added += 1

        first = item.get("first_name")
        last = item.get("last_name")
        job = item.get("job_title")
        linkedin = item.get("linkedin")
        website = item.get("website")
        now = datetime.now(UTC).isoformat()

        # Parse name
        name_data = parse_contact_name(item)
        name_given = name_data.get("name_given")
        name_surname = name_data.get("name_surname")
        name_parsed = name_data.get("name_parsed")

        # Extract company/role from job title
        job_data = parse_job_title(job)
        company = job_data.get("company")
        role = job_data.get("role")

        # Use preserved dedup metadata or None for new contacts
        dup_group = existing_dedup["duplicate_group_id"] if existing_dedup else None
        dup_resolution = (
            existing_dedup["duplicate_resolution"] if existing_dedup else None
        )
        primary_id = existing_dedup["primary_contact_id"] if existing_dedup else None

        cursor.execute(
            """
            INSERT OR REPLACE INTO contacts (
                id, first_name, last_name, job_title, linkedin, website,
                full_data, record_hash, last_synced_at,
                duplicate_group_id, duplicate_resolution, primary_contact_id,
                name_given, name_surname, name_parsed, company, role
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                c_id,
                first,
                last,
                job,
                linkedin,
                website,
                json.dumps(item),
                new_hash,
                now,
                dup_group,
                dup_resolution,
                primary_id,
                name_given,
                name_surname,
                name_parsed,
                company,
                role,
            ),
        )

        # Refresh derived tables
        cursor.execute("DELETE FROM emails WHERE contact_id = ?", (c_id,))
        cursor.execute("DELETE FROM phones WHERE contact_id = ?", (c_id,))

        # Batch insert emails for better performance
        email_data = [
            (c_id, email_item.get("email"))
            for email_item in item.get("emails", [])
            if email_item.get("email")
        ]
        if email_data:
            cursor.executemany(
                "INSERT INTO emails (contact_id, email) VALUES (?, ?)", email_data
            )

        # Batch insert phones for better performance
        phone_data = [
            (c_id, phone_item.get("phone_number"), phone_item.get("label"))
            for phone_item in item.get("phones", [])
            if phone_item.get("phone_number")
        ]
        if phone_data:
            cursor.executemany(
                "INSERT INTO phones (contact_id, phone_number, label) VALUES (?, ?, ?)",
                phone_data,
            )

    conn.commit()
    return added, updated, unchanged


def save_reminders_batch(
    conn: sqlite3.Connection,
    items: list[dict[str, Any]],
) -> tuple[int, int, int]:
    """Save reminders to DB."""
    cursor = conn.cursor()
    added = 0
    updated = 0
    unchanged = 0

    for item in items:
        r_id = item.get("id")
        if not r_id:
            continue

        new_hash = compute_hash(item)
        cursor.execute("SELECT record_hash FROM reminders WHERE id = ?", (r_id,))
        row = cursor.fetchone()

        if row:
            if row[0] == new_hash:
                unchanged += 1
                continue
            updated += 1
        else:
            added += 1

        body = item.get("body")
        is_complete = item.get("is_complete", False)
        due_date = item.get("due_at_date")
        now = datetime.now(UTC).isoformat()

        cursor.execute(
            """
            INSERT OR REPLACE INTO reminders (
                id, body, is_complete, due_date, full_data, record_hash, last_synced_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (r_id, body, is_complete, due_date, json.dumps(item), new_hash, now),
        )

        # Update links
        cursor.execute("DELETE FROM reminder_contacts WHERE reminder_id = ?", (r_id,))
        # Batch insert contact links for better performance
        contact_links = [
            (r_id, contact.get("id"))
            for contact in item.get("contact_ids", [])
            if contact.get("id")
        ]
        if contact_links:
            cursor.executemany(
                "INSERT INTO reminder_contacts (reminder_id, contact_id) VALUES (?, ?)",
                contact_links,
            )

    conn.commit()
    return added, updated, unchanged


def save_notes_batch(
    conn: sqlite3.Connection,
    items: list[dict[str, Any]],
) -> tuple[int, int, int]:
    """Save notes (timeline items) to DB."""
    cursor = conn.cursor()
    added = 0
    updated = 0
    unchanged = 0

    for item in items:
        n_id = item.get("id")
        if not n_id:
            continue

        new_hash = compute_hash(item)
        cursor.execute("SELECT record_hash FROM notes WHERE id = ?", (n_id,))
        row = cursor.fetchone()

        if row:
            if row[0] == new_hash:
                unchanged += 1
                continue
            updated += 1
        else:
            added += 1

        note_text = item.get("note")
        event_time = item.get("event_time")
        now = datetime.now(UTC).isoformat()

        cursor.execute(
            """
            INSERT OR REPLACE INTO notes (
                id, note, event_time, full_data, record_hash, last_synced_at
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (n_id, note_text, event_time, json.dumps(item), new_hash, now),
        )

        # Update links
        cursor.execute("DELETE FROM note_contacts WHERE note_id = ?", (n_id,))
        # Batch insert contact links for better performance
        contact_links = [
            (n_id, contact.get("id"))
            for contact in item.get("contacts", [])
            if contact.get("id")
        ]
        if contact_links:
            cursor.executemany(
                "INSERT INTO note_contacts (note_id, contact_id) VALUES (?, ?)",
                contact_links,
            )

    conn.commit()
    return added, updated, unchanged


async def fetch_generic_batch(
    fetch_method: Any,
    offset: int,
    limit: int,
    sem: asyncio.Semaphore,
) -> Any | None:
    """Generic safe fetcher."""
    async with sem:
        try:
            return await fetch_method(limit=limit, offset=offset)
        except Exception as e:
            console.print(f"[red]Error fetching batch offset={offset}: {e}[/red]")
            return None


async def sync_resource(
    resource_name: str,
    fetch_method: Any,
    save_method: Any,
    client: AsyncDexClient,
    conn: sqlite3.Connection,
    sem: asyncio.Semaphore,
) -> None:
    """Generic sync loop for a resource (Contacts, Reminders, Notes)."""
    console.print(f"[bold cyan]Syncing {resource_name}...[/bold cyan]")

    try:
        first_page = await fetch_method(limit=1, offset=0)
    except Exception as e:
        console.print(f"[bold red]Failed to fetch {resource_name}: {e}[/bold red]")
        return

    total_count = first_page.total
    console.print(f"Found [green]{total_count}[/green] {resource_name}.")

    if total_count == 0:
        return

    offsets = list(range(0, total_count, BATCH_Size))

    # Statistics
    stats = {"added": 0, "updated": 0, "unchanged": 0, "failed": 0}

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("{task.percentage:>3.0f}%"),
        TextColumn("• {task.fields[stats]}"),
    ) as progress:
        task = progress.add_task("Fetching...", total=len(offsets), stats="Init...")

        chunk_size = CONCURRENCY * 2

        for i in range(0, len(offsets), chunk_size):
            chunk_offsets = offsets[i : i + chunk_size]
            tasks = [
                fetch_generic_batch(fetch_method, off, BATCH_Size, sem)
                for off in chunk_offsets
            ]

            results = await asyncio.gather(*tasks)

            for res in results:
                if res:
                    # Determine which list to save based on type
                    items = []
                    if isinstance(res, PaginatedContacts):
                        items = res.contacts
                    elif isinstance(res, PaginatedReminders):
                        items = res.reminders
                    elif isinstance(res, PaginatedNotes):
                        items = res.notes

                    a, u, k = save_method(conn, items)
                    stats["added"] += a
                    stats["updated"] += u
                    stats["unchanged"] += k
                else:
                    stats["failed"] += 1

                progress.advance(task)
                stat_str = (
                    f"Add:{stats['added']} Upd:{stats['updated']} "
                    f"Skp:{stats['unchanged']} Err:{stats['failed']}"
                )
                progress.update(task, stats=stat_str)

    console.print(f"[green]Done {resource_name}![/green]\n")


async def sync_all() -> None:
    """Master sync function."""
    conn = sqlite3.connect(DB_PATH)
    init_db(conn)
    sem = asyncio.Semaphore(CONCURRENCY)

    async with AsyncDexClient() as client:
        # 1. Sync Contacts
        await sync_resource(
            "Contacts",
            client.get_contacts_paginated,
            save_contacts_batch,
            client,
            conn,
            sem,
        )

        # 2. Sync Reminders
        await sync_resource(
            "Reminders",
            client.get_reminders_paginated,
            save_reminders_batch,
            client,
            conn,
            sem,
        )

        # 3. Sync Notes
        await sync_resource(
            "Notes", client.get_notes_paginated, save_notes_batch, client, conn, sem
        )

    conn.close()
    console.print("[bold green]All Syncs Complete![/bold green]")


def main() -> None:
    try:
        asyncio.run(sync_all())
    except KeyboardInterrupt:
        console.print("[red]Sync interrupted.[/red]")


if __name__ == "__main__":
    main()
