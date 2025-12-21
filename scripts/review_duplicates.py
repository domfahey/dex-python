"""Interactive CLI tool to review and label duplicate contacts."""

import os
import sqlite3
from pathlib import Path

from rich.console import Console
from rich.prompt import Prompt
from rich.table import Table


def setup_db(cursor: sqlite3.Cursor) -> None:
    """Ensure necessary columns exist for labeling."""
    try:
        cursor.execute("ALTER TABLE contacts ADD COLUMN duplicate_resolution TEXT")
    except sqlite3.OperationalError:
        pass

    try:
        cursor.execute("ALTER TABLE contacts ADD COLUMN primary_contact_id TEXT")
    except sqlite3.OperationalError:
        pass


def _fetch_unresolved_groups(cursor: sqlite3.Cursor) -> list[str]:
    """Fetch all duplicate groups that haven't been resolved yet.

    Args:
        cursor: Database cursor.

    Returns:
        List of group IDs.
    """
    cursor.execute("""
        SELECT DISTINCT duplicate_group_id
        FROM contacts
        WHERE duplicate_group_id IS NOT NULL
          AND (duplicate_resolution IS NULL OR duplicate_resolution = '')
    """)
    return [row[0] for row in cursor.fetchall()]


def _display_contact_group(
    console: Console, cursor: sqlite3.Cursor, group_id: str, group_num: int, total: int
) -> list[str]:
    """Display contacts in a duplicate group as a table.

    Args:
        console: Rich console for output.
        cursor: Database cursor.
        group_id: Group ID to display.
        group_num: Current group number.
        total: Total number of groups.

    Returns:
        List of contact IDs in this group.
    """
    console.rule(f"Group {group_num}/{total} (ID: {group_id})")

    # Fetch contacts in this group
    cursor.execute(
        """
        SELECT id, first_name, last_name, job_title
        FROM contacts
        WHERE duplicate_group_id = ?
        """,
        (group_id,),
    )
    contacts = cursor.fetchall()

    if len(contacts) < 2:
        return []

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("#", style="dim", width=4)
    table.add_column("ID", style="cyan", width=12, overflow="ellipsis")
    table.add_column("Name", style="bold")
    table.add_column("Job Title")
    table.add_column("Emails")
    table.add_column("Phones")

    contact_ids = []

    for idx, row in enumerate(contacts):
        c_id, first, last, job = row
        contact_ids.append(c_id)

        cursor.execute("SELECT email FROM emails WHERE contact_id = ?", (c_id,))
        emails = "\n".join([r[0] for r in cursor.fetchall() if r[0]])

        cursor.execute("SELECT phone_number FROM phones WHERE contact_id = ?", (c_id,))
        phones = "\n".join([r[0] for r in cursor.fetchall() if r[0]])

        table.add_row(
            str(idx + 1),
            c_id,
            f"{first or ''} {last or ''}".strip(),
            job or "",
            emails,
            phones,
        )

    console.print(table)
    return contact_ids


def _handle_user_choice(
    cursor: sqlite3.Cursor,
    conn: sqlite3.Connection,
    console: Console,
    choice: str,
    contact_ids: list[str],
    group_id: str,
) -> tuple[int, int]:
    """Handle user's choice for a duplicate group.

    Args:
        cursor: Database cursor.
        conn: Database connection.
        console: Rich console for output.
        choice: User's choice ('s', 'q', or a number).
        contact_ids: List of contact IDs in the group.
        group_id: Group ID.

    Returns:
        Tuple of (labeled_count, rejected_count) increments.
    """
    if choice == "s":
        # Mark as false positive
        cursor.execute(
            """
            UPDATE contacts
            SET duplicate_resolution = 'false_positive'
            WHERE duplicate_group_id = ?
            """,
            (group_id,),
        )
        conn.commit()
        console.print("[yellow]✔ Marked as false positive.[/yellow]\n")
        return 0, 1

    # Label as confirmed with selected primary
    selected_idx = int(choice) - 1
    primary_id = contact_ids[selected_idx]

    cursor.execute(
        """
        UPDATE contacts
        SET duplicate_resolution = 'confirmed',
            primary_contact_id = ?
        WHERE duplicate_group_id = ?
        """,
        (primary_id, group_id),
    )
    conn.commit()
    res_msg = f"[green]✔ Confirmed. Primary: ...{primary_id[-8:]}[/green]\n"
    console.print(res_msg)
    return 1, 0


def main() -> None:
    data_dir = Path(os.getenv("DEX_DATA_DIR", "output"))
    db_path = data_dir / "dex_contacts.db"
    if not db_path.exists():
        print(f"Error: Database {db_path} not found.")
        return
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Check if duplicate_group_id exists
    try:
        cursor.execute("SELECT duplicate_group_id FROM contacts LIMIT 1")
    except sqlite3.OperationalError:
        print(
            "Error: duplicate_group_id column not found. Run flag_duplicates.py first."
        )
        return

    setup_db(cursor)

    groups = _fetch_unresolved_groups(cursor)

    console = Console()
    console.clear()
    msg = f"[bold green]Found {len(groups)} unresolved groups to review.[/bold green]\n"
    console.print(msg)

    if not groups:
        console.print(
            "No pending duplicates found! Run "
            "[bold]uv run python flag_duplicates.py[/bold] to generate new flags."
        )
        return

    labeled_count = 0
    rejected_count = 0

    try:
        for i, group_id in enumerate(groups):
            contact_ids = _display_contact_group(
                console, cursor, group_id, i + 1, len(groups)
            )

            if len(contact_ids) < 2:
                continue

            # Get user choice
            choices = [str(x + 1) for x in range(len(contact_ids))] + ["s", "q"]
            choice = Prompt.ask(
                "\n[bold]Actions:[/bold]\n"
                "  [cyan][1-N][/cyan] Label this ID as PRIMARY (Confirm Duplicates)\n"
                "  [yellow][s][/yellow]   Mark as NOT Duplicates (False Positive)\n"
                "  [red][q][/red]   Quit\n"
                "Select",
                choices=choices,
                default="s",
            )

            if choice == "q":
                console.print("\n[bold red]Exiting...[/bold red]")
                break

            # Handle the choice
            labeled_inc, rejected_inc = _handle_user_choice(
                cursor, conn, console, choice, contact_ids, group_id
            )
            labeled_count += labeled_inc
            rejected_count += rejected_inc

    except KeyboardInterrupt:
        console.print("\n[bold red]Interrupted![/bold red]")

    finally:
        conn.close()
        console.rule("Session Summary")
        console.print(f"Groups Confirmed: [green]{labeled_count}[/green]")
        console.print(f"False Positives:  [yellow]{rejected_count}[/yellow]")
        rem_count = len(groups) - (i + 1) if "i" in locals() else len(groups)
        console.print(f"Remaining:        {rem_count}")


if __name__ == "__main__":
    main()
