"""Tests for clustering duplicate contacts into entities."""

from dex_python.deduplication import cluster_duplicates


def test_cluster_duplicates_basic() -> None:
    """Test clustering simple pairs into groups."""
    # A matches B, B matches C
    matches = [
        {"contact_ids": ["A", "B"], "match_type": "email"},
        {"contact_ids": ["B", "C"], "match_type": "phone"},
    ]

    clusters = cluster_duplicates(matches)

    # Should result in one cluster with A, B, C
    assert len(clusters) == 1
    assert set(clusters[0]) == {"A", "B", "C"}


def test_cluster_duplicates_disjoint() -> None:
    """Test that disjoint groups remain separate."""
    matches = [
        {"contact_ids": ["A", "B"], "match_type": "email"},
        {"contact_ids": ["C", "D"], "match_type": "phone"},
    ]

    clusters = cluster_duplicates(matches)

    assert len(clusters) == 2
    # Check if {A, B} and {C, D} are present
    cluster_sets = [set(c) for c in clusters]
    assert {"A", "B"} in cluster_sets
    assert {"C", "D"} in cluster_sets


def test_cluster_duplicates_complex() -> None:
    """Test more complex overlapping matches."""
    matches = [
        {"contact_ids": ["A", "B"]},
        {"contact_ids": ["B", "C"]},
        {"contact_ids": ["D", "E"]},
        {"contact_ids": ["C", "F"]},
    ]

    clusters = cluster_duplicates(matches)

    # Clusters: {A, B, C, F} and {D, E}
    assert len(clusters) == 2
    cluster_sets = [set(c) for c in clusters]
    assert {"A", "B", "C", "F"} in cluster_sets
    assert {"D", "E"} in cluster_sets
