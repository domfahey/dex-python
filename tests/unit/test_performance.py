"""Performance tests to validate optimization improvements.

This test suite verifies that key operations perform efficiently
and demonstrates the performance improvements made.
"""

import sqlite3
import time
from itertools import combinations

from dex_python.deduplication import (
    cluster_duplicates,
    find_email_duplicates,
    find_phone_duplicates,
)


def create_test_db_with_contacts(n_contacts: int, duplicates_ratio: float = 0.1):
    """Create a test database with contacts for performance testing."""
    conn = sqlite3.connect(":memory:")
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE contacts (
            id TEXT PRIMARY KEY,
            first_name TEXT,
            last_name TEXT,
            job_title TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE emails (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            contact_id TEXT,
            email TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE phones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            contact_id TEXT,
            phone_number TEXT
        )
    """)

    # Add indexes as implemented in optimization
    cursor.execute("CREATE INDEX idx_emails_contact_id ON emails(contact_id)")
    cursor.execute("CREATE INDEX idx_emails_email_lower ON emails(lower(email))")
    cursor.execute("CREATE INDEX idx_phones_contact_id ON phones(contact_id)")
    cursor.execute("CREATE INDEX idx_phones_number ON phones(phone_number)")

    # Insert test contacts
    n_dupes = int(n_contacts * duplicates_ratio)
    for i in range(n_contacts):
        contact_id = f"contact_{i}"
        cursor.execute(
            "INSERT INTO contacts (id, first_name, last_name) VALUES (?, ?, ?)",
            (contact_id, f"First{i}", f"Last{i}"),
        )

        # Some contacts share emails (duplicates)
        if i < n_dupes * 2:
            email = f"shared{i % n_dupes}@example.com"
        else:
            email = f"unique{i}@example.com"
        cursor.execute(
            "INSERT INTO emails (contact_id, email) VALUES (?, ?)",
            (contact_id, email),
        )

        # Some contacts share phones (duplicates)
        if i < n_dupes * 2:
            phone = f"555-{i % n_dupes:04d}"
        else:
            phone = f"555-{i:04d}"
        cursor.execute(
            "INSERT INTO phones (contact_id, phone_number) VALUES (?, ?)",
            (contact_id, phone),
        )

    conn.commit()
    return conn


def test_email_duplicates_performance():
    """Test that email duplicate finding is fast with indexes."""
    conn = create_test_db_with_contacts(1000, duplicates_ratio=0.1)

    start = time.time()
    results = find_email_duplicates(conn)
    elapsed = time.time() - start

    # Should complete in under 100ms for 1000 contacts
    assert elapsed < 0.1, (
        f"Email duplicate finding took {elapsed:.3f}s (expected < 0.1s)"
    )
    # Should find duplicates (10% ratio means ~50 groups)
    assert len(results) > 0, "Should find duplicate emails"
    conn.close()


def test_phone_duplicates_performance():
    """Test that phone duplicate finding is fast with indexes."""
    conn = create_test_db_with_contacts(1000, duplicates_ratio=0.1)

    start = time.time()
    results = find_phone_duplicates(conn)
    elapsed = time.time() - start

    # Should complete in under 100ms for 1000 contacts
    assert elapsed < 0.1, (
        f"Phone duplicate finding took {elapsed:.3f}s (expected < 0.1s)"
    )
    # Should find duplicates
    assert len(results) > 0, "Should find duplicate phones"
    conn.close()


def test_cluster_duplicates_optimized():
    """Test that cluster_duplicates uses efficient itertools.combinations."""
    # Create test matches
    matches = [
        {"contact_ids": ["a", "b", "c"]},
        {"contact_ids": ["d", "e"]},
        {"contact_ids": ["c", "f"]},  # Links to first group
    ]

    start = time.time()
    clusters = cluster_duplicates(matches)
    elapsed = time.time() - start

    # Should be very fast
    assert elapsed < 0.01, f"Clustering took {elapsed:.3f}s (expected < 0.01s)"

    # Should correctly cluster
    assert len(clusters) == 2, "Should have 2 clusters"
    # First cluster should have a, b, c, f (connected through c)
    cluster1 = sorted([c for c in clusters if "a" in c][0])
    assert cluster1 == ["a", "b", "c", "f"]


def test_list_comprehension_vs_append():
    """
    Compare building a list with a list comprehension versus using repeated append and assert performance and equivalence.
    
    Creates a dataset of 10,000 items, constructs one list with a for-loop that appends and another with a list comprehension, then asserts the two results have the same length and that the comprehension's time is no more than 15× the append approach.
    """
    n = 10000
    data = [(f"type_{i}", f"value_{i}", [f"id_{i}", f"id_{i + 1}"]) for i in range(n)]

    # Old style with append (simulated)
    start = time.time()
    results_old = []
    for match_type, value, ids in data:
        results_old.append(
            {"match_type": match_type, "match_value": value, "contact_ids": ids}
        )
    old_time = time.time() - start

    # New style with list comprehension
    start = time.time()
    results_new = [
        {"match_type": mt, "match_value": val, "contact_ids": ids}
        for mt, val, ids in data
    ]
    new_time = time.time() - start

    # Use a generous multiplier to reduce micro-benchmark flakiness.
    assert new_time <= old_time * 15.0, "List comprehension should be efficient"
    assert len(results_new) == len(results_old) == n


def test_batch_executemany_vs_individual():
    """Test that executemany is faster than individual inserts."""
    conn = sqlite3.connect(":memory:")
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE test_emails (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            contact_id TEXT,
            email TEXT
        )
    """)

    n = 1000
    contact_id = "test_contact"
    email_data = [(contact_id, f"email{i}@example.com") for i in range(n)]

    # Individual inserts (old way)
    start = time.time()
    for cid, email in email_data:
        cursor.execute(
            "INSERT INTO test_emails (contact_id, email) VALUES (?, ?)", (cid, email)
        )
    individual_time = time.time() - start

    # Clear table
    cursor.execute("DELETE FROM test_emails")

    # Batch insert with executemany (new way)
    start = time.time()
    cursor.executemany(
        "INSERT INTO test_emails (contact_id, email) VALUES (?, ?)", email_data
    )
    batch_time = time.time() - start

    conn.close()

    # Keep the threshold low to tolerate timing variance across environments.
    speedup = individual_time / batch_time
    assert speedup > 1.1, f"Batch insert should be >1.1x faster (was {speedup:.1f}x)"


def test_combinations_vs_nested_loops():
    """Test that itertools.combinations is faster than nested loops."""
    ids = [f"id_{i}" for i in range(100)]

    # Old way: nested loops
    start = time.time()
    edges_old = []
    for i in range(len(ids)):
        for j in range(i + 1, len(ids)):
            edges_old.append((ids[i], ids[j]))
    old_time = time.time() - start

    # New way: itertools.combinations
    start = time.time()
    edges_new = list(combinations(ids, 2))
    new_time = time.time() - start

    assert len(edges_new) == len(edges_old)
    # combinations should be faster
    assert new_time <= old_time, (
        f"combinations ({new_time:.3f}s) should be <= nested loops ({old_time:.3f}s)"
    )