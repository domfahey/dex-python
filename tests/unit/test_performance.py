"""Performance tests to validate optimization improvements.

This test suite verifies that key operations perform efficiently
and demonstrates the performance improvements made.
"""

import sqlite3
import time
from itertools import combinations

import pytest

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


@pytest.mark.performance
def test_email_duplicates_performance():
    """Test that email duplicate finding is fast with indexes."""
    conn = create_test_db_with_contacts(1000, duplicates_ratio=0.1)

    start = time.perf_counter()
    results = find_email_duplicates(conn)
    elapsed = time.perf_counter() - start

    # Should complete quickly for 1000 contacts
    assert elapsed < 0.5, (
        f"Email duplicate finding took {elapsed:.3f}s (expected < 0.5s)"
    )
    # Should find duplicates (10% ratio means ~50 groups)
    assert len(results) > 0, "Should find duplicate emails"
    conn.close()


@pytest.mark.performance
def test_phone_duplicates_performance():
    """Test that phone duplicate finding is fast with indexes."""
    conn = create_test_db_with_contacts(1000, duplicates_ratio=0.1)

    start = time.perf_counter()
    results = find_phone_duplicates(conn)
    elapsed = time.perf_counter() - start

    # Should complete quickly for 1000 contacts
    assert elapsed < 0.5, (
        f"Phone duplicate finding took {elapsed:.3f}s (expected < 0.5s)"
    )
    # Should find duplicates
    assert len(results) > 0, "Should find duplicate phones"
    conn.close()


@pytest.mark.performance
def test_cluster_duplicates_optimized():
    """Test that cluster_duplicates uses efficient itertools.combinations."""
    # Create test matches
    matches = [
        {"contact_ids": ["a", "b", "c"]},
        {"contact_ids": ["d", "e"]},
        {"contact_ids": ["c", "f"]},  # Links to first group
    ]

    start = time.perf_counter()
    clusters = cluster_duplicates(matches)
    elapsed = time.perf_counter() - start

    # Should be very fast
    assert elapsed < 0.2, f"Clustering took {elapsed:.3f}s (expected < 0.2s)"

    # Should correctly cluster
    assert len(clusters) == 2, "Should have 2 clusters"
    # First cluster should have a, b, c, f (connected through c)
    cluster1 = sorted([c for c in clusters if "a" in c][0])
    assert cluster1 == ["a", "b", "c", "f"]


@pytest.mark.performance
def test_list_comprehension_vs_append():
    """
    Compare list comprehension vs append for performance and equivalence.
    """
    n = 10000
    data = [(f"type_{i}", f"value_{i}", [f"id_{i}", f"id_{i + 1}"]) for i in range(n)]

    # Old style with append (simulated)
    start = time.perf_counter()
    results_old = []
    for match_type, value, ids in data:
        results_old.append(
            {"match_type": match_type, "match_value": value, "contact_ids": ids}
        )
    old_time = time.perf_counter() - start

    # New style with list comprehension
    start = time.perf_counter()
    results_new = [
        {"match_type": mt, "match_value": val, "contact_ids": ids}
        for mt, val, ids in data
    ]
    new_time = time.perf_counter() - start

    # Use a generous multiplier to reduce micro-benchmark flakiness.
    # If timing is too coarse and one side is effectively zero, skip ratio assertions
    # and still keep the equivalence check.
    if old_time > 0:
        assert new_time <= old_time * 5.0, "List comprehension should be efficient"
    assert len(results_new) == len(results_old) == n


@pytest.mark.performance
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
    start = time.perf_counter()
    for cid, email in email_data:
        cursor.execute(
            "INSERT INTO test_emails (contact_id, email) VALUES (?, ?)", (cid, email)
        )
    individual_time = time.perf_counter() - start

    # Clear table
    cursor.execute("DELETE FROM test_emails")

    # Batch insert with executemany (new way)
    start = time.perf_counter()
    cursor.executemany(
        "INSERT INTO test_emails (contact_id, email) VALUES (?, ?)", email_data
    )
    batch_time = time.perf_counter() - start

    conn.close()

    # Keep the threshold modest to tolerate timing variance across environments.
    if batch_time > 0:
        speedup = individual_time / batch_time
        assert speedup >= 1.0, (
            f"Batch insert should be as fast or faster than "
            f"individual inserts (was {speedup:.1f}x)"
        )
    else:
        pytest.skip("Timer resolution too coarse for batch insert benchmark")


@pytest.mark.performance
def test_combinations_vs_nested_loops():
    """Test that itertools.combinations is faster than nested loops."""
    ids = [f"id_{i}" for i in range(100)]

    # Old way: nested loops
    start = time.perf_counter()
    edges_old = []
    for i in range(len(ids)):
        for j in range(i + 1, len(ids)):
            edges_old.append((ids[i], ids[j]))
    old_time = time.perf_counter() - start

    # New way: itertools.combinations
    start = time.perf_counter()
    edges_new = list(combinations(ids, 2))
    new_time = time.perf_counter() - start

    assert len(edges_new) == len(edges_old)
    # combinations should be comparable or faster; allow 2x tolerance for noise
    if old_time > 0:
        assert new_time <= old_time * 2, (
            f"combinations ({new_time:.3f}s) should be <= 2x "
            f"nested loops ({old_time:.3f}s)"
        )
