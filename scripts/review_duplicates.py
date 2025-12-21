"""Interactive CLI tool to review and label duplicate contacts."""

import os
import sqlite3
import urllib.parse
import webbrowser
from collections import Counter
from pathlib import Path

from rich.console import Console
from rich.prompt import Prompt
from rich.table import Table

DEX_SEARCH_URL = "https://getdex.com/appv3/search?terms="


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

    # Get all distinct group IDs that haven't been resolved yet
    cursor.execute("""
        SELECT DISTINCT duplicate_group_id
        FROM contacts
        WHERE duplicate_group_id IS NOT NULL
          AND (duplicate_resolution IS NULL OR duplicate_resolution = '')
    """)
    groups = [row[0] for row in cursor.fetchall()]

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
            console.rule(f"Group {i + 1}/{len(groups)} (ID: {group_id})")

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
                continue

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

                cursor.execute(
                    "SELECT phone_number FROM phones WHERE contact_id = ?", (c_id,)
                )
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

            # Build smart search term - use last name to catch all variations
            # Collect all name parts to find the best search term
            all_name_parts: list[str] = []
            for c in contacts:
                if c[1]:  # first_name
                    all_name_parts.append(c[1].strip().lower())
                if c[2]:  # last_name
                    all_name_parts.append(c[2].strip().lower())

            # Find most common name part (likely the shared last name)
            name_counts = Counter(all_name_parts)
            if name_counts:
                # Use the most common name part as search term
                search_term = name_counts.most_common(1)[0][0]
            else:
                # Fallback to first contact's last name
                search_term = (contacts[0][2] or contacts[0][1] or "").strip()

            # Prompt loop - allows reopening URL without advancing
            while True:
                choices = [str(x + 1) for x in range(len(contacts))] + ["o", "s", "q"]
                choice = Prompt.ask(
                    "\n[bold]Actions:[/bold]\n"
                    "  [cyan][1-N][/cyan] Label this ID as PRIMARY (Confirm Duplicates)\n"
                    f"  [blue][o][/blue]   Open in Dex (search: '{search_term}')\n"
                    "  [yellow][s][/yellow]   Mark as NOT Duplicates (False Positive)\n"
                    "  [red][q][/red]   Quit\n"
                    "Select",
                    choices=choices,
                    default="s",
                )

                if choice == "o":
                    # Open Dex search in browser
                    encoded_term = urllib.parse.quote(search_term)
                    url = f"{DEX_SEARCH_URL}{encoded_term}"
                    webbrowser.open(url)
                    console.print(f"[blue]↗ Opened: {url}[/blue]")
                    continue  # Stay on same group
                else:
                    break  # Exit prompt loop, process choice

            if choice == "q":
                console.print("\n[bold red]Exiting...[/bold red]")
                break

            elif choice == "s":
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
                rejected_count += 1

            else:
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
                labeled_count += 1

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
