"Robust sync script with concurrency, integrity checks, and error handling."

import asyncio
import hashlib
import json
import os
import sqlite3
from datetime import UTC, datetime
from typing import Any

from rich.console import Console
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn

from src.dex_import.async_client import AsyncDexClient
from src.dex_import.models import PaginatedContacts

os.makedirs("output", exist_ok=True)
DB_PATH = "output/dex_contacts.db"
BATCH_Size = 100
CONCURRENCY = 5  # Max concurrent requests

console = Console()


def init_db(conn: sqlite3.Connection) -> None:
    """Initialize database with contacts table and hash column."""
    cursor = conn.cursor()

    # Create main table if not exists (using JSON for full data)
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

    # Ensure columns exist (for existing DBs)
    cols_to_add = [
        ("record_hash", "TEXT"),
        ("last_synced_at", "TIMESTAMP"),
        ("duplicate_group_id", "TEXT"),
        ("duplicate_resolution", "TEXT"),
        ("primary_contact_id", "TEXT"),
        ("full_data", "JSON"),
    ]

    for col_name, col_type in cols_to_add:
        try:
            cursor.execute(f"ALTER TABLE contacts ADD COLUMN {col_name} {col_type}")
        except sqlite3.OperationalError:
            # Column likely exists
            pass

    # Create related tables
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

    conn.commit()


def compute_hash(data: dict[str, Any]) -> str:
    """Compute SHA256 hash of contact data for integrity check."""
    # Sort keys to ensure deterministic JSON
    json_str = json.dumps(data, sort_keys=True)
    return hashlib.sha256(json_str.encode("utf-8")).hexdigest()


def save_batch(
    conn: sqlite3.Connection, contacts: list[dict[str, Any]]
) -> tuple[int, int, int]:
    """
    Save a batch of contacts to DB.
    Returns: (added, updated, unchanged)
    """
    cursor = conn.cursor()
    added = 0
    updated = 0
    unchanged = 0

    for contact in contacts:
        c_id = contact.get("id")
        if not c_id:
            continue

        new_hash = compute_hash(contact)

        # Check existing
        cursor.execute("SELECT record_hash FROM contacts WHERE id = ?", (c_id,))
        row = cursor.fetchone()

        if row:
            # Contact exists
            existing_hash = row[0]
            if existing_hash == new_hash:
                unchanged += 1
                continue
            updated += 1
        else:
            added += 1

        # Prepare fields
        first = contact.get("first_name")
        last = contact.get("last_name")
        job = contact.get("job_title")
        linkedin = contact.get("linkedin")
        website = contact.get("website")
        now = datetime.now(UTC).isoformat()

        # Insert/Update Contact - use ON CONFLICT to preserve dedup columns
        cursor.execute(
            """
            INSERT INTO contacts (
                id, first_name, last_name, job_title, linkedin, website,
                full_data, record_hash, last_synced_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                first_name = excluded.first_name,
                last_name = excluded.last_name,
                job_title = excluded.job_title,
                linkedin = excluded.linkedin,
                website = excluded.website,
                full_data = excluded.full_data,
                record_hash = excluded.record_hash,
                last_synced_at = excluded.last_synced_at
        """,
            (
                c_id,
                first,
                last,
                job,
                linkedin,
                website,
                json.dumps(contact),
                new_hash,
                now,
            ),
        )

        # Update emails/phones (simplest strategy: delete old, insert new)
        # Only needed if updated or added
        cursor.execute("DELETE FROM emails WHERE contact_id = ?", (c_id,))
        cursor.execute("DELETE FROM phones WHERE contact_id = ?", (c_id,))

        for email_item in contact.get("emails", []):
            if e := email_item.get("email"):
                cursor.execute(
                    "INSERT INTO emails (contact_id, email) VALUES (?, ?)", (c_id, e)
                )

        for phone_item in contact.get("phones", []):
            if p := phone_item.get("phone_number"):
                cursor.execute(
                    """
                    INSERT INTO phones (contact_id, phone_number, label)
                    VALUES (?, ?, ?)
                    """,
                    (c_id, p, phone_item.get("label")),
                )

    conn.commit()
    return added, updated, unchanged


async def fetch_batch_safe(
    client: AsyncDexClient, offset: int, limit: int, sem: asyncio.Semaphore
) -> PaginatedContacts | None:
    """Fetch a batch with semaphore and error handling."""
    async with sem:
        try:
            return await client.get_contacts_paginated(limit=limit, offset=offset)
        except Exception as e:
            console.print(f"[red]Error fetching batch offset={offset}: {e}[/red]")
            return None


async def sync_contacts() -> None:
    """Main sync loop."""
    conn = sqlite3.connect(DB_PATH)
    init_db(conn)

    sem = asyncio.Semaphore(CONCURRENCY)

    async with AsyncDexClient() as client:
        # 1. Initial Fetch to get Total
        console.print("[bold cyan]Connecting to Dex API...[/bold cyan]")
        try:
            first_page = await client.get_contacts_paginated(limit=1, offset=0)
        except Exception as e:
            console.print(f"[bold red]Failed to connect: {e}[/bold red]")
            return

        total_count = first_page.total
        console.print(f"Found [green]{total_count}[/green] total contacts.")

        # Handle edge case: API returns 0 but may have contacts
        if total_count == 0:
            # Check if first page actually has contacts (fallback)
            if first_page.contacts:
                console.print(
                    "[yellow]Warning: API returned total=0 but has contacts. "
                    "Using fallback sync.[/yellow]"
                )
                # Process whatever we got
                added, updated, unchanged = save_batch(conn, first_page.contacts)
                console.print(f"Fallback sync: Added={added} Updated={updated}")
            else:
                console.print("[yellow]No contacts to sync.[/yellow]")
            conn.close()
            return

        # 2. Plan Batches
        offsets = list(range(0, total_count, BATCH_Size))

        total_added = 0
        total_updated = 0
        total_unchanged = 0
        total_failed = 0

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("{task.percentage:>3.0f}%"),
            TextColumn("• {task.fields[stats]}"),
        ) as progress:
            task = progress.add_task(
                "Syncing...", total=len(offsets), stats="Starting..."
            )

            # Process in chunks of CONCURRENCY to control memory pressure
            chunk_size = CONCURRENCY * 2

            for i in range(0, len(offsets), chunk_size):
                chunk_offsets = offsets[i : i + chunk_size]

                # Create tasks
                tasks = [
                    fetch_batch_safe(client, off, BATCH_Size, sem)
                    for off in chunk_offsets
                ]

                # Await all in this chunk
                results = await asyncio.gather(*tasks)

                # Process results
                for res in results:
                    if res:
                        added, updated, unchanged = save_batch(conn, res.contacts)
                        total_added += added
                        total_updated += updated
                        total_unchanged += unchanged
                    else:
                        total_failed += 1

                    progress.advance(task)
                    progress.update(
                        task,
                        stats=(
                            f"Add:{total_added} Upd:{total_updated} "
                            f"Skp:{total_unchanged} Err:{total_failed}"
                        ),
                    )

    conn.close()
    console.print("\n[bold green]Sync Complete![/bold green]")
    console.print(f"Total Added:     {total_added}")
    console.print(f"Total Updated:   {total_updated}")
    console.print(f"Total Unchanged: {total_unchanged}")
    console.print(f"Failed Batches:  {total_failed}")


def main() -> None:
    try:
        asyncio.run(sync_contacts())
    except KeyboardInterrupt:
        console.print("[red]Sync interrupted.[/red]")


if __name__ == "__main__":
    main()
