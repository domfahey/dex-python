"""Script to flag duplicates in the database without merging."""

import os
import sqlite3
import uuid
from pathlib import Path

from dex_python.deduplication import find_all_duplicates

DATA_DIR = Path(os.getenv("DEX_DATA_DIR", "output"))
DEFAULT_DB_PATH = DATA_DIR / "dex_contacts.db"


def main(db_path: str = str(DEFAULT_DB_PATH)) -> None:
    if not Path(db_path).exists():
        print(f"Error: Database {db_path} not found.")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 1. Ensure the column exists
    print("Ensuring schema supports duplicate flagging...")
    try:
        cursor.execute("ALTER TABLE contacts ADD COLUMN duplicate_group_id TEXT")
    except sqlite3.OperationalError:
        print("  Column 'duplicate_group_id' already exists.")

    # 2. Reset existing flags
    cursor.execute("UPDATE contacts SET duplicate_group_id = NULL")
    conn.commit()

    print("Finding all potential duplicates...")

    # Use shared duplicate detection function
    matches, clusters = find_all_duplicates(conn, fuzzy_threshold=0.98)

    print(f"Found {len(matches)} duplicate signals.")
    print(f"Clustered into {len(clusters)} unique duplicate groups.")

    if not clusters:
        print("No duplicates to flag.")
        conn.close()
        return

    print("Flagging records...")
    count = 0
    for cluster in clusters:
        # Generate a short unique ID for the group
        group_id = str(uuid.uuid4())[:8]

        placeholders = ",".join(["?"] * len(cluster))
        cursor.execute(
            f"UPDATE contacts SET duplicate_group_id = ? WHERE id IN ({placeholders})",
            [group_id] + cluster,
        )
        count += len(cluster)

    conn.commit()
    conn.close()

    print(f"Success! Flagged {count} contacts across {len(clusters)} groups.")
    print(
        "You can now query duplicates using: "
        "SELECT * FROM contacts WHERE duplicate_group_id IS NOT NULL "
        "ORDER BY duplicate_group_id;"
    )


if __name__ == "__main__":
    main()
