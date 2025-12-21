"""Backfill company and role columns from existing job titles."""

import os
import sqlite3
from pathlib import Path

from rich.console import Console
from rich.progress import Progress

from dex_python.enrichment import parse_job_title

DATA_DIR = Path(os.getenv("DEX_DATA_DIR", "output"))
DB_PATH = DATA_DIR / "dex_contacts.db"

console = Console()


def ensure_columns(conn: sqlite3.Connection) -> None:
    """Add company and role columns if they don't exist."""
    cursor = conn.cursor()

    # Check existing columns
    cursor.execute("PRAGMA table_info(contacts)")
    columns = {row[1] for row in cursor.fetchall()}

    if "company" not in columns:
        console.print("[yellow]Adding 'company' column...[/yellow]")
        cursor.execute("ALTER TABLE contacts ADD COLUMN company TEXT")

    if "role" not in columns:
        console.print("[yellow]Adding 'role' column...[/yellow]")
        cursor.execute("ALTER TABLE contacts ADD COLUMN role TEXT")

    conn.commit()


def backfill(conn: sqlite3.Connection) -> dict:
    """Parse job titles and populate company/role columns."""
    cursor = conn.cursor()

    # Get contacts with job titles but no company/role yet
    cursor.execute("""
        SELECT id, job_title FROM contacts
        WHERE job_title IS NOT NULL AND job_title != ''
          AND (company IS NULL OR role IS NULL)
    """)
    rows = cursor.fetchall()

    stats = {"total": len(rows), "with_company": 0, "role_only": 0}

    with Progress() as progress:
        task = progress.add_task("Parsing job titles...", total=len(rows))

        for contact_id, job_title in rows:
            parsed = parse_job_title(job_title)

            cursor.execute(
                "UPDATE contacts SET company = ?, role = ? WHERE id = ?",
                (parsed["company"], parsed["role"], contact_id),
            )

            if parsed["company"]:
                stats["with_company"] += 1
            else:
                stats["role_only"] += 1

            progress.advance(task)

    conn.commit()
    return stats


def main() -> None:
    """Run the backfill process."""
    if not DB_PATH.exists():
        console.print(f"[red]Database not found: {DB_PATH}[/red]")
        return

    console.print("[bold]Backfilling company/role from job titles[/bold]")
    console.print(f"Database: {DB_PATH}\n")

    conn = sqlite3.connect(DB_PATH)

    # Add columns if needed
    ensure_columns(conn)

    # Run backfill
    stats = backfill(conn)

    conn.close()

    console.print("\n[bold green]Backfill Complete![/bold green]")
    console.print(f"  Total processed: {stats['total']}")
    console.print(f"  With company:    {stats['with_company']}")
    console.print(f"  Role only:       {stats['role_only']}")


if __name__ == "__main__":
    main()
