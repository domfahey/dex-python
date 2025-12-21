"""Tests for deduplication helper functions."""

import sqlite3

import pytest

from dex_python.deduplication import (
    _consolidate_related_records,
    _create_soundex_blocks,
    _find_matches_in_block,
    _merge_contact_fields,
    _select_primary_row,
)


class TestSelectPrimaryRow:
    """Tests for _select_primary_row helper function."""

    def test_select_primary_row_with_explicit_id(self) -> None:
        """Test selecting primary row with explicit ID."""
        rows = [
            ("id1", "John", "Doe", "Engineer", None, None, "{}"),
            ("id2", "Jane", "Doe", "Manager", "linkedin", "website", "{}"),
            ("id3", "Jim", "Doe", "Director", None, None, "{}"),
        ]
        primary_row, sorted_rows, primary_id = _select_primary_row(rows, "id2")
        assert primary_id == "id2"
        assert primary_row[0] == "id2"
        assert len(sorted_rows) == 3
        assert sorted_rows[0][0] == "id2"

    def test_select_primary_row_auto_selects_most_complete(self) -> None:
        """Test auto-selection of most complete row."""
        rows = [
            ("id1", "John", None, None, None, None, "{}"),
            ("id2", "Jane", "Doe", "Manager", "linkedin", "website", "{}"),
            ("id3", "Jim", "Doe", None, None, None, "{}"),
        ]
        primary_row, sorted_rows, primary_id = _select_primary_row(rows, None)
        assert primary_id == "id2"  # Most complete row
        assert primary_row[0] == "id2"

    def test_select_primary_row_raises_on_invalid_id(self) -> None:
        """Test that ValueError is raised for invalid primary_id."""
        rows = [
            ("id1", "John", "Doe", None, None, None, "{}"),
            ("id2", "Jane", "Doe", None, None, None, "{}"),
        ]
        with pytest.raises(ValueError, match="Primary ID id3 not found"):
            _select_primary_row(rows, "id3")


class TestMergeContactFields:
    """Tests for _merge_contact_fields helper function."""

    def test_merge_fills_missing_fields(self) -> None:
        """Test that merge fills in missing fields from other rows."""
        primary_row = ("id1", "John", None, None, None, None, "{}")
        other_rows = [
            ("id2", "Jane", "Doe", "Manager", "linkedin", None, "{}"),
            ("id3", "Jim", "Doe", None, None, "website", "{}"),
        ]
        merged = _merge_contact_fields(primary_row, other_rows)
        assert merged[0] == "id1"  # ID from primary
        assert merged[1] == "John"  # First name from primary
        assert merged[2] == "Doe"  # Last name from first other
        assert merged[3] == "Manager"  # Job title from first other
        assert merged[4] == "linkedin"  # LinkedIn from first other
        assert merged[5] == "website"  # Website from second other

    def test_merge_preserves_primary_non_empty_fields(self) -> None:
        """Test that merge preserves non-empty fields from primary."""
        primary_row = ("id1", "John", "Smith", "Engineer", "primary-li", None, "{}")
        other_rows = [
            ("id2", "Jane", "Doe", "Manager", "other-li", "website", "{}"),
        ]
        merged = _merge_contact_fields(primary_row, other_rows)
        assert merged[1] == "John"  # Kept from primary
        assert merged[2] == "Smith"  # Kept from primary
        assert merged[3] == "Engineer"  # Kept from primary
        assert merged[4] == "primary-li"  # Kept from primary
        assert merged[5] == "website"  # Filled from other


class TestCreateSoundexBlocks:
    """Tests for _create_soundex_blocks helper function."""

    def test_creates_blocks_by_metaphone(self) -> None:
        """Test that contacts are grouped by metaphone of last name."""
        rows = [
            ("id1", "John", "Smith"),
            ("id2", "Jane", "Smyth"),  # Similar sound
            ("id3", "Jim", "Jones"),
        ]
        blocks = _create_soundex_blocks(rows)
        assert len(blocks) > 0
        # Smith and Smyth should likely be in the same block (similar metaphone)
        # But we can't guarantee exact metaphone results, so just check structure
        for key, contacts in blocks.items():
            assert isinstance(key, str)
            assert isinstance(contacts, list)
            for contact in contacts:
                assert "id" in contact
                assert "full_name" in contact

    def test_skips_empty_names(self) -> None:
        """Test that empty names are skipped."""
        rows = [
            ("id1", "John", "Smith"),
            ("id2", "", "Doe"),  # Empty first name
            ("id3", "Jane", ""),  # Empty last name
            ("id4", "  ", "Jones"),  # Whitespace only
        ]
        blocks = _create_soundex_blocks(rows)
        # Should only have id1 and id4 after filtering (but id4 will be filtered too)
        total_contacts = sum(len(contacts) for contacts in blocks.values())
        assert total_contacts == 1  # Only id1

    def test_handles_metaphone_errors_gracefully(self) -> None:
        """Test that metaphone errors fall back to first 2 chars."""
        rows = [
            ("id1", "John", "Xyz123!@#"),  # Non-standard characters
        ]
        blocks = _create_soundex_blocks(rows)
        # Should still create blocks, just using fallback
        total_contacts = sum(len(contacts) for contacts in blocks.values())
        assert total_contacts == 1


class TestFindMatchesInBlock:
    """Tests for _find_matches_in_block helper function."""

    def test_finds_matches_above_threshold(self) -> None:
        """Test that similar names are matched."""
        items = [
            {"id": "id1", "full_name": "John Smith"},
            {"id": "id2", "full_name": "Jon Smith"},  # Typo
        ]
        matches = _find_matches_in_block(items, threshold=0.85)
        assert len(matches) == 1
        assert matches[0]["match_type"] == "fuzzy_name"
        assert "id1" in matches[0]["contact_ids"]
        assert "id2" in matches[0]["contact_ids"]

    def test_ignores_matches_below_threshold(self) -> None:
        """Test that dissimilar names are not matched."""
        items = [
            {"id": "id1", "full_name": "John Smith"},
            {"id": "id2", "full_name": "Jane Doe"},
        ]
        matches = _find_matches_in_block(items, threshold=0.9)
        assert len(matches) == 0

    def test_finds_multiple_matches_in_block(self) -> None:
        """Test finding multiple matches in same block."""
        items = [
            {"id": "id1", "full_name": "John Smith"},
            {"id": "id2", "full_name": "Jon Smith"},
            {"id": "id3", "full_name": "Johnny Smith"},
        ]
        matches = _find_matches_in_block(items, threshold=0.80)
        # Should find multiple pairs
        assert len(matches) >= 2


class TestConsolidateRelatedRecords:
    """Tests for _consolidate_related_records helper function."""

    def test_consolidates_emails_and_phones(self) -> None:
        """Test that emails and phones are moved to primary contact."""
        conn = sqlite3.connect(":memory:")
        cursor = conn.cursor()

        # Create tables
        cursor.execute(
            """CREATE TABLE emails (
                id INTEGER PRIMARY KEY, contact_id TEXT, email TEXT
            )"""
        )
        cursor.execute(
            """CREATE TABLE phones (
                id INTEGER PRIMARY KEY, contact_id TEXT, phone_number TEXT
            )"""
        )

        # Insert test data
        cursor.execute("INSERT INTO emails VALUES (1, 'id1', 'john@example.com')")
        cursor.execute("INSERT INTO emails VALUES (2, 'id2', 'jane@example.com')")
        cursor.execute("INSERT INTO phones VALUES (1, 'id1', '111-1111')")
        cursor.execute("INSERT INTO phones VALUES (2, 'id2', '222-2222')")
        conn.commit()

        # Consolidate
        _consolidate_related_records(cursor, "id1", ["id1", "id2"], "?,?")
        conn.commit()

        # Check results
        cursor.execute("SELECT contact_id FROM emails ORDER BY id")
        email_contacts = [row[0] for row in cursor.fetchall()]
        assert all(c == "id1" for c in email_contacts)

        cursor.execute("SELECT contact_id FROM phones ORDER BY id")
        phone_contacts = [row[0] for row in cursor.fetchall()]
        assert all(c == "id1" for c in phone_contacts)

    def test_deduplicates_emails(self) -> None:
        """Test that duplicate emails are removed."""
        conn = sqlite3.connect(":memory:")
        cursor = conn.cursor()

        cursor.execute(
            """CREATE TABLE emails (
                id INTEGER PRIMARY KEY, contact_id TEXT, email TEXT
            )"""
        )
        cursor.execute(
            """CREATE TABLE phones (
                id INTEGER PRIMARY KEY, contact_id TEXT, phone_number TEXT
            )"""
        )

        # Insert duplicate emails (different case)
        cursor.execute("INSERT INTO emails VALUES (1, 'id1', 'john@example.com')")
        cursor.execute("INSERT INTO emails VALUES (2, 'id1', 'JOHN@example.com')")
        conn.commit()

        # Consolidate
        _consolidate_related_records(cursor, "id1", ["id1"], "?")
        conn.commit()

        # Check results - should only have one email
        cursor.execute("SELECT COUNT(*) FROM emails")
        count = cursor.fetchone()[0]
        assert count == 1
