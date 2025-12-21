"""Script to analyze duplicates in the local database across all levels."""

import os
import sqlite3
from pathlib import Path
from typing import Any

from dex_python.deduplication import (
    find_birthday_name_duplicates,
    find_email_duplicates,
    find_fuzzy_name_duplicates,
    find_name_and_title_duplicates,
    find_phone_duplicates,
)

DATA_DIR = Path(os.getenv("DEX_DATA_DIR", "output"))
DEFAULT_DB_PATH = DATA_DIR / "dex_contacts.db"
DEFAULT_REPORT_PATH = DATA_DIR / "DUPLICATE_REPORT.md"


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
    report_file: Any, conn: sqlite3.Connection, group: dict[str, Any], title: str
) -> None:
    """Helper to write a duplicate group to the report file."""
    report_file.write(f"### {title}: `{group['match_value']}`\n")
    report_file.write("| ID | Name | Job Title |\n")
    report_file.write("|---|---|---|\n")
    for contact_id in group["contact_ids"]:
        info = get_contact_summary(conn, contact_id)
        report_file.write(f"| `{info['id']}` | {info['name']} | {info['job']} |\n")
    report_file.write("\n")


def generate_report(db_path: str, output_path: str) -> None:
    """Run duplicate analysis across all levels and generate a Markdown report."""
    if not Path(db_path).exists():
        print(f"Error: Database {db_path} not found.")
        return

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(db_path)

    print("Running Level 1 Analysis (Exact Emails/Phones)...")
    email_dupes = find_email_duplicates(conn)
    phone_dupes = find_phone_duplicates(conn)

    print("Running Level 1.5 Analysis (Name + Birthday)...")
    birthday_dupes = find_birthday_name_duplicates(conn)

    print("Running Level 2 Analysis (Name + Title)...")
    name_title_dupes = find_name_and_title_duplicates(conn)

    print("Running Level 3 Analysis (Fuzzy Name)...")
    # High threshold for report
    fuzzy_dupes = find_fuzzy_name_duplicates(conn, threshold=0.95)

    # Calculate total unique contacts involved
    all_dupe_ids = set()
    all_dupes = [
        email_dupes,
        phone_dupes,
        birthday_dupes,
        name_title_dupes,
        fuzzy_dupes,
    ]
    for dupes in all_dupes:
        for group in dupes:
            all_dupe_ids.update(group["contact_ids"])

    print(f"Total contacts flagged as potential duplicates: {len(all_dupe_ids)}")

    # Generate Markdown Report
    with open(output_path, "w") as report_file:
        report_file.write("# Comprehensive Duplicate Contact Report\n\n")
        report_file.write(f"**Database:** `{db_path}`\n")
        report_file.write(f"**Total Flagged Contacts:** {len(all_dupe_ids)}\n\n")

        report_file.write("## Level 1: Exact Matches (Highest Confidence)\n")
        report_file.write("### Shared Emails\n")
        if not email_dupes:
            report_file.write("_No shared emails found._\n")
        for group in email_dupes:
            write_group_to_file(report_file, conn, group, "Email")

        report_file.write("### Shared Phones\n")
        if not phone_dupes:
            report_file.write("_No shared phone numbers found._\n")
        for group in phone_dupes:
            write_group_to_file(report_file, conn, group, "Phone")

        report_file.write("## Level 1.5: Name + Birthday (High Confidence)\n")
        report_file.write("### Same Name and Birthday\n")
        if not birthday_dupes:
            report_file.write("_No name + birthday duplicates found._\n")
        for group in birthday_dupes:
            write_group_to_file(report_file, conn, group, "Birthday")

        report_file.write("## Level 2: Rule-Based Matches (Medium Confidence)\n")
        report_file.write("### Shared Name + Job Title\n")
        if not name_title_dupes:
            report_file.write("_No Name + Job Title duplicates found._\n")
        for group in name_title_dupes:
            write_group_to_file(report_file, conn, group, "Match")

        report_file.write("## Level 3: Fuzzy Matches (Lower Confidence)\n")
        report_file.write("### Fuzzy Name Matches (Jaro-Winkler > 0.95)\n")
        if not fuzzy_dupes:
            report_file.write("_No fuzzy name duplicates found._\n")
        for group in fuzzy_dupes:
            write_group_to_file(report_file, conn, group, "Fuzzy Match")

    conn.close()
    print(f"Report generated: {output_path}")


if __name__ == "__main__":
    generate_report(str(DEFAULT_DB_PATH), str(DEFAULT_REPORT_PATH))
