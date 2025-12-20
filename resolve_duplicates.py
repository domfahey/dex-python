"""Script to resolve duplicates in the local database by merging them."""

import sqlite3
from pathlib import Path

from src.dex_import.deduplication import (
    cluster_duplicates,
    find_email_duplicates,
    find_fuzzy_name_duplicates,
    find_name_and_title_duplicates,
    find_phone_duplicates,
    merge_cluster,
)


def main(db_path: str = "output/dex_contacts.db") -> None:
    if not Path(db_path).exists():
        print(f"Error: Database {db_path} not found.")
        return

    conn = sqlite3.connect(db_path)

    print("Finding all potential duplicates...")

    # Collect all signals
    matches = []
    matches.extend(find_email_duplicates(conn))
    matches.extend(find_phone_duplicates(conn))
    matches.extend(find_name_and_title_duplicates(conn))
    # Using a very high threshold for auto-merging fuzzy matches
    matches.extend(find_fuzzy_name_duplicates(conn, threshold=0.98))

    print(f"Found {len(matches)} duplicate signals.")

    # Cluster into entities
    clusters = cluster_duplicates(matches)
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
