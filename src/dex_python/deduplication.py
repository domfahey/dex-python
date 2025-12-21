"""Duplicate detection, clustering, and merging logic.

This module provides a multi-level deduplication system for contact records:
- Level 1: Exact email and phone matching
- Level 1.5: Birthday + name matching
- Level 2: Exact name + job title matching
- Level 3: Fuzzy name matching using Jaro-Winkler similarity

The clustering function uses graph theory (connected components) to group
related duplicates that may have been found through different match types.

Example:
    >>> import sqlite3
    >>> conn = sqlite3.connect("contacts.db")
    >>> email_dups = find_email_duplicates(conn)
    >>> phone_dups = find_phone_duplicates(conn)
    >>> clusters = cluster_duplicates(email_dups + phone_dups)
"""

import sqlite3
from typing import Any

import jellyfish
import networkx as nx


def find_email_duplicates(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    """Find groups of contacts sharing the same email address.

    Uses case-insensitive matching on email addresses.

    Args:
        conn: SQLite database connection.

    Returns:
        List of match dictionaries with 'match_type', 'match_value',
        and 'contact_ids' keys.
    """
    cursor = conn.cursor()

    query = """
        SELECT lower(email) as norm_email, GROUP_CONCAT(DISTINCT contact_id) as ids
        FROM emails
        WHERE email IS NOT NULL AND email != ''
        GROUP BY lower(email)
        HAVING COUNT(DISTINCT contact_id) > 1
    """

    cursor.execute(query)
    results = []
    for row in cursor.fetchall():
        email, ids_str = row
        results.append(
            {
                "match_type": "email",
                "match_value": email,
                "contact_ids": ids_str.split(","),
            }
        )
    return results


def find_phone_duplicates(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    """Find groups of contacts sharing the same phone number.

    Args:
        conn: SQLite database connection.

    Returns:
        List of match dictionaries with 'match_type', 'match_value',
        and 'contact_ids' keys.
    """
    cursor = conn.cursor()

    query = """
        SELECT phone_number, GROUP_CONCAT(DISTINCT contact_id) as ids
        FROM phones
        WHERE phone_number IS NOT NULL AND phone_number != ''
        GROUP BY phone_number
        HAVING COUNT(DISTINCT contact_id) > 1
    """

    cursor.execute(query)
    results = []
    for row in cursor.fetchall():
        phone, ids_str = row
        results.append(
            {
                "match_type": "phone",
                "match_value": phone,
                "contact_ids": ids_str.split(","),
            }
        )
    return results


def find_birthday_name_duplicates(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    """Find duplicates with same name AND same birthday month-day.

    Level 1.5 matching: more confident than name-only but less than email.
    Excludes placeholder date 2001-01-01. Matches on month-day only since
    the year field often contains entry date rather than birth year.

    Args:
        conn: SQLite database connection.

    Returns:
        List of match dictionaries with 'match_type', 'match_value',
        and 'contact_ids' keys.
    """
    cursor = conn.cursor()

    query = """
        SELECT
            lower(trim(first_name)) || ' ' || lower(trim(last_name)) as full_name,
            substr(json_extract(full_data, '$.birthday'), 6) as month_day,
            GROUP_CONCAT(DISTINCT id) as ids
        FROM contacts
        WHERE
            json_extract(full_data, '$.birthday') IS NOT NULL
            AND json_extract(full_data, '$.birthday') NOT LIKE '2001-01-01%'
            AND first_name IS NOT NULL AND first_name != ''
            AND last_name IS NOT NULL AND last_name != ''
        GROUP BY lower(trim(first_name)), lower(trim(last_name)), month_day
        HAVING COUNT(DISTINCT id) > 1
    """

    cursor.execute(query)
    results = []
    for row in cursor.fetchall():
        full_name, month_day, ids_str = row
        results.append(
            {
                "match_type": "birthday_name",
                "match_value": f"{full_name} (birthday: {month_day})",
                "contact_ids": ids_str.split(","),
            }
        )
    return results


def find_name_and_title_duplicates(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    """Find duplicates based on exact full name + job title match.

    Level 2 matching: requires both name and title to match exactly
    (case-insensitive, trimmed).

    Args:
        conn: SQLite database connection.

    Returns:
        List of match dictionaries with 'match_type', 'match_value',
        and 'contact_ids' keys.
    """
    cursor = conn.cursor()

    query = """
        SELECT
            lower(trim(first_name)) || ' ' || lower(trim(last_name)) as full_name,
            lower(trim(job_title)) as title,
            GROUP_CONCAT(id) as ids
        FROM contacts
        WHERE
            first_name IS NOT NULL AND first_name != '' AND
            last_name IS NOT NULL AND last_name != '' AND
            job_title IS NOT NULL AND job_title != ''
        GROUP BY lower(trim(first_name)), lower(trim(last_name)), lower(trim(job_title))
        HAVING COUNT(DISTINCT id) > 1
    """

    cursor.execute(query)
    results = []
    for row in cursor.fetchall():
        full_name, title, ids_str = row
        results.append(
            {
                "match_type": "name_title",
                "match_value": f"{full_name} | {title}",
                "contact_ids": ids_str.split(","),
            }
        )
    return results


def find_fuzzy_name_duplicates(
    conn: sqlite3.Connection, threshold: float = 0.9
) -> list[dict[str, Any]]:
    """Find duplicates using fuzzy name matching with blocking.

    Level 3 matching: uses Jaro-Winkler similarity on full names.
    Blocking by Soundex reduces O(n²) comparisons to near-linear.

    Args:
        conn: SQLite database connection.
        threshold: Minimum Jaro-Winkler score (0.0-1.0) for a match.

    Returns:
        List of match dictionaries with 'match_type', 'match_value',
        and 'contact_ids' keys.
    """
    cursor = conn.cursor()

    query = """
        SELECT id, first_name, last_name
        FROM contacts
        WHERE first_name IS NOT NULL AND last_name IS NOT NULL
    """
    cursor.execute(query)
    rows = cursor.fetchall()

    blocks: dict[str, list[dict[str, str]]] = {}
    for contact_id, first, last in rows:
        first, last = first.strip(), last.strip()

        # Skip empty names after stripping
        if not first or not last:
            continue

        try:
            phonetic_key = jellyfish.metaphone(last) or last.lower()[:2]
        except Exception:
            phonetic_key = last.lower()[:2]

        if phonetic_key not in blocks:
            blocks[phonetic_key] = []
        blocks[phonetic_key].append({"id": contact_id, "full_name": f"{first} {last}"})

    results = []
    for items in blocks.values():
        if len(items) < 2:
            continue
        for first_index in range(len(items)):
            for second_index in range(first_index + 1, len(items)):
                contact1, contact2 = items[first_index], items[second_index]
                score = jellyfish.jaro_winkler_similarity(
                    contact1["full_name"], contact2["full_name"]
                )
                if score >= threshold:
                    match_value = (
                        f"{contact1['full_name']} <-> "
                        f"{contact2['full_name']} ({score:.2f})"
                    )
                    results.append(
                        {
                            "match_type": "fuzzy_name",
                            "match_value": match_value,
                            "contact_ids": [contact1["id"], contact2["id"]],
                        }
                    )
    return results


def cluster_duplicates(matches: list[dict[str, Any]]) -> list[list[str]]:
    """Cluster match pairs into transitive groups using connected components.

    If A matches B and B matches C, they all end up in the same cluster
    even if A and C never matched directly.

    Args:
        matches: List of match dictionaries with 'contact_ids' key.

    Returns:
        List of clusters, where each cluster is a list of contact IDs.
    """
    graph: nx.Graph[str] = nx.Graph()
    for match in matches:
        contact_ids = match["contact_ids"]
        for first_index in range(len(contact_ids)):
            for second_index in range(first_index + 1, len(contact_ids)):
                graph.add_edge(contact_ids[first_index], contact_ids[second_index])
    return [list(cluster) for cluster in nx.connected_components(graph)]


def merge_cluster(
    conn: sqlite3.Connection, contact_ids: list[str], primary_id: str | None = None
) -> str:
    """Merge multiple contacts into a single primary record.

    Consolidates data from all contacts into the primary record, keeping
    the most complete data. Moves all emails and phones to the primary,
    deduplicates them, and deletes the merged contacts.

    Args:
        conn: SQLite database connection.
        contact_ids: List of contact IDs to merge.
        primary_id: Optional ID to use as the primary record.
            If None, auto-selects the most complete record.

    Returns:
        The ID of the primary (surviving) contact.

    Raises:
        ValueError: If no contact IDs provided or contacts not found.
    """
    if not contact_ids:
        raise ValueError("No contact IDs provided")

    cursor = conn.cursor()
    placeholders = ",".join(["?"] * len(contact_ids))
    cursor.execute(f"SELECT * FROM contacts WHERE id IN ({placeholders})", contact_ids)
    rows = cursor.fetchall()

    if not rows:
        raise ValueError("Contacts not found in database")

    if primary_id:
        # Find the row corresponding to primary_id
        primary_row_list = [row for row in rows if row[0] == primary_id]
        if not primary_row_list:
            raise ValueError(f"Primary ID {primary_id} not found in contact cluster")
        primary_row = primary_row_list[0]
        # Remove primary from candidates to merge FROM
        other_rows = [row for row in rows if row[0] != primary_id]
        sorted_rows = [primary_row] + other_rows
    else:
        # Auto-select best primary
        def score_row(row: tuple[Any, ...]) -> int:
            return sum(1 for field in row if field is not None and field != "")

        sorted_rows = sorted(rows, key=score_row, reverse=True)
        primary_row = sorted_rows[0]
        primary_id = primary_row[0]

    current_primary = list(primary_row)
    for other_row in sorted_rows[1:]:
        for field_index in range(len(current_primary)):
            current_field = current_primary[field_index]
            is_empty = current_field is None or current_field == ""
            if is_empty and other_row[field_index]:
                current_primary[field_index] = other_row[field_index]

    cursor.execute(
        """
        UPDATE contacts
        SET first_name=?, last_name=?, job_title=?, linkedin=?, website=?, full_data=?
        WHERE id=?
        """,
        (
            current_primary[1],
            current_primary[2],
            current_primary[3],
            current_primary[4],
            current_primary[5],
            current_primary[6],
            primary_id,
        ),
    )

    for table in ["emails", "phones"]:
        cursor.execute(
            f"UPDATE {table} SET contact_id = ? WHERE contact_id IN ({placeholders})",
            [primary_id] + contact_ids,
        )
        if table == "emails":
            cursor.execute("""
                DELETE FROM emails WHERE id NOT IN (
                    SELECT MIN(id) FROM emails GROUP BY contact_id, lower(email)
                )
            """)
        else:
            cursor.execute("""
                DELETE FROM phones WHERE id NOT IN (
                    SELECT MIN(id) FROM phones GROUP BY contact_id, phone_number
                )
            """)

    cursor.execute(
        f"DELETE FROM contacts WHERE id IN ({placeholders}) AND id != ?",
        contact_ids + [primary_id],
    )
    conn.commit()
    return primary_id
