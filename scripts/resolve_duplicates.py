"""Script to resolve duplicates in the local database by merging them."""

import os
import sqlite3
from pathlib import Path

from dex_python.deduplication import find_all_duplicates, merge_cluster

DATA_DIR = Path(os.getenv("DEX_DATA_DIR", "output"))
DEFAULT_DB_PATH = DATA_DIR / "dex_contacts.db"


def main(db_path: str = str(DEFAULT_DB_PATH)) -> None:
    if not Path(db_path).exists():
        print(f"Error: Database {db_path} not found.")
        return

    conn = sqlite3.connect(db_path)

    print("Finding all potential duplicates...")

    # Use shared duplicate detection function
    matches, clusters = find_all_duplicates(conn, fuzzy_threshold=0.98)

    print(f"Found {len(matches)} duplicate signals.")
    print(f"Clustered into {len(clusters)} unique entities to be merged.")

    if not clusters:
        print("No duplicates to resolve.")
        return

    # Count contacts before
    cursor = conn.cursor()
    cursor.execute("SELECT count(*) FROM contacts")
    before_count = cursor.fetchone()[0]

    total_merged = 0
    print("\nMerging clusters...")
    for cluster in clusters:
        try:
            merge_cluster(conn, cluster)
            total_merged += len(cluster) - 1
        except Exception as e:
            print(f"Error merging cluster {cluster}: {e}")

    # Count contacts after
    cursor.execute("SELECT count(*) FROM contacts")
    after_count = cursor.fetchone()[0]

    print("\nResolution Complete!")
    print(f"Total contacts before: {before_count}")
    print(f"Total contacts after:  {after_count}")
    print(f"Reduction: {total_merged} redundant records removed.")

    conn.close()


if __name__ == "__main__":
    main()
