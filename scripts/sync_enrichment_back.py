"""CLI script to sync enriched data back to Dex API."""

import argparse
import os
import sqlite3
from pathlib import Path

from rich.console import Console
from rich.table import Table

from dex_python.client import DexClient
from dex_python.sync_back import SyncBackMode, run_sync

DATA_DIR = Path(os.getenv("DEX_DATA_DIR", "output"))
DB_PATH = DATA_DIR / "dex_contacts.db"

console = Console()


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Sync enriched data (company/role) back to Dex API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Sync as notes (adds enrichment as timeline notes)
  python sync_enrichment_back.py --mode notes

  # Sync to description field (appends to existing descriptions)
  python sync_enrichment_back.py --mode description

  # Sync by reformatting job_title as "Role | Company"
  python sync_enrichment_back.py --mode job_title

  # Preview what would be synced (dry run)
  python sync_enrichment_back.py --mode notes --dry-run
        """,
    )
    parser.add_argument(
        "--mode",
        type=str,
        choices=["notes", "description", "job_title"],
        required=True,
        help="Sync mode: notes, description, or job_title",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without making API calls",
    )
    parser.add_argument(
        "--db",
        type=str,
        default=str(DB_PATH),
        help=f"Path to SQLite database (default: {DB_PATH})",
    )
    return parser.parse_args()


def preview_sync(conn: sqlite3.Connection, mode: SyncBackMode) -> None:
    """Preview what would be synced without making API calls."""
    from dex_python.sync_back import (
        build_description_update,
        build_enrichment_note,
        build_job_title_update,
        get_contacts_for_sync,
    )

    contacts = get_contacts_for_sync(conn)

    table = Table(title=f"Preview: {mode.value} sync ({len(contacts)} contacts)")
    table.add_column("Contact ID", style="cyan")
    table.add_column("Company", style="green")
    table.add_column("Role", style="yellow")
    table.add_column("Output", style="white")

    for contact in contacts[:20]:  # Limit preview to 20
        if mode == SyncBackMode.NOTES:
            output = build_enrichment_note(contact["company"], contact["role"])
        elif mode == SyncBackMode.DESCRIPTION:
            output = build_description_update(
                contact["company"],
                contact["role"],
                contact["existing_description"],
            )
        else:
            output = build_job_title_update(contact["role"], contact["company"])

        # Truncate long output for display
        if output and len(output) > 50:
            output = output[:47] + "..."

        table.add_row(
            contact["id"][:8] + "...",
            contact["company"] or "-",
            contact["role"] or "-",
            output or "-",
        )

    console.print(table)

    if len(contacts) > 20:
        console.print(f"[dim]... and {len(contacts) - 20} more contacts[/dim]")


def main() -> None:
    """Main entry point."""
    args = parse_args()

    # Validate database exists
    db_path = Path(args.db)
    if not db_path.exists():
        console.print(f"[red]Database not found: {db_path}[/red]")
        return

    # Parse mode
    mode = SyncBackMode(args.mode)

    console.print("[bold]Sync Enrichment Back to Dex[/bold]")
    console.print(f"Mode: [cyan]{mode.value}[/cyan]")
    console.print(f"Database: {db_path}\n")

    conn = sqlite3.connect(db_path)

    if args.dry_run:
        console.print("[yellow]DRY RUN - No changes will be made[/yellow]\n")
        preview_sync(conn, mode)
        conn.close()
        return

    # Run actual sync
    console.print("[bold cyan]Starting sync...[/bold cyan]")

    def progress_callback(current: int, total: int, stats: dict) -> None:
        console.print(
            f"  Progress: {current}/{total} "
            f"(created={stats.get('created', 0)}, "
            f"errors={stats.get('errors', 0)})"
        )

    with DexClient() as client:
        if mode == SyncBackMode.NOTES:
            from dex_python.sync_back import sync_as_notes

            stats = sync_as_notes(conn, client, progress_callback)
        else:
            stats = run_sync(conn, client, mode)

    conn.close()

    # Display results
    console.print("\n[bold green]Sync Complete![/bold green]")

    if mode == SyncBackMode.NOTES:
        console.print(f"  Notes created: {stats.get('created', 0)}")
        console.print(f"  Skipped:       {stats.get('skipped', 0)}")
    else:
        console.print(f"  Contacts updated: {stats.get('updated', 0)}")
        console.print(f"  Skipped:          {stats.get('skipped', 0)}")

    if stats.get("errors", 0) > 0:
        console.print(f"  [red]Errors: {stats['errors']}[/red]")


if __name__ == "__main__":
    main()
