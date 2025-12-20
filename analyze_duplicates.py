"""Script to analyze duplicates in the local database across all levels."""

import sqlite3
from pathlib import Path
from typing import Any

from src.dex_import.deduplication import (
    find_email_duplicates,
    find_fuzzy_name_duplicates,
    find_name_and_title_duplicates,
    find_phone_duplicates,
)


def get_contact_summary(conn: sqlite3.Connection, contact_id: str) -> dict[str, Any]:
    """Fetch basic info for a contact to display in the report."""
    cursor = conn.cursor()
    cursor.execute(
        "SELECT first_name, last_name, job_title FROM contacts WHERE id = ?",
        (contact_id,),
    )
    row = cursor.fetchone()
    if row:
        return {
            "id": contact_id,
            "name": f"{row[0] or ''} {row[1] or ''}".strip(),
            "job": row[2] or "N/A",
        }
    return {"id": contact_id, "name": "Unknown", "job": "N/A"}


def write_group_to_file(
    f: Any, conn: sqlite3.Connection, group: dict[str, Any], title: str
) -> None:
    """Helper to write a duplicate group to the report file."""
    f.write(f"### {title}: `{group['match_value']}`\n")
    f.write("| ID | Name | Job Title |\n")
    f.write("|---|---|---|\n")
    for cid in group["contact_ids"]:
        info = get_contact_summary(conn, cid)
        f.write(f"| `{info['id']}` | {info['name']} | {info['job']} |\n")
    f.write("\n")


def generate_report(db_path: str, output_path: str) -> None:
    """Run duplicate analysis across all levels and generate a Markdown report."""
    if not Path(db_path).exists():
        print(f"Error: Database {db_path} not found.")
        return

    conn = sqlite3.connect(db_path)

    print("Running Level 1 Analysis (Exact Emails/Phones)...")
    email_dupes = find_email_duplicates(conn)
    phone_dupes = find_phone_duplicates(conn)

    print("Running Level 2 Analysis (Name + Title)...")
    name_title_dupes = find_name_and_title_duplicates(conn)

    print("Running Level 3 Analysis (Fuzzy Name)...")
    # High threshold for report
    fuzzy_dupes = find_fuzzy_name_duplicates(conn, threshold=0.95)

    # Calculate total unique contacts involved
    all_dupe_ids = set()
    for dupes in [email_dupes, phone_dupes, name_title_dupes, fuzzy_dupes]:
        for group in dupes:
            all_dupe_ids.update(group["contact_ids"])

    print(f"Total contacts flagged as potential duplicates: {len(all_dupe_ids)}")

    # Generate Markdown Report
    with open(output_path, "w") as f:
        f.write("# Comprehensive Duplicate Contact Report\n\n")
        f.write(f"**Database:** `{db_path}`\n")
        f.write(f"**Total Flagged Contacts:** {len(all_dupe_ids)}\n\n")

        f.write("## Level 1: Exact Matches (Highest Confidence)\n")
        f.write("### Shared Emails\n")
        if not email_dupes:
            f.write("_No shared emails found._\n")
        for group in email_dupes:
            write_group_to_file(f, conn, group, "Email")

        f.write("### Shared Phones\n")
        if not phone_dupes:
            f.write("_No shared phone numbers found._\n")
        for group in phone_dupes:
            write_group_to_file(f, conn, group, "Phone")

        f.write("## Level 2: Rule-Based Matches (Medium Confidence)\n")
        f.write("### Shared Name + Job Title\n")
        if not name_title_dupes:
            f.write("_No Name + Job Title duplicates found._\n")
        for group in name_title_dupes:
            write_group_to_file(f, conn, group, "Match")

        f.write("## Level 3: Fuzzy Matches (Lower Confidence)\n")
        f.write("### Fuzzy Name Matches (Jaro-Winkler > 0.95)\n")
        if not fuzzy_dupes:
            f.write("_No fuzzy name duplicates found._\n")
        for group in fuzzy_dupes:
            write_group_to_file(f, conn, group, "Fuzzy Match")

    conn.close()
    print(f"Report generated: {output_path}")


if __name__ == "__main__":
    generate_report("dex_contacts.db", "DUPLICATE_REPORT.md")
