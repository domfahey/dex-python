"""Tests for syncing enriched data back to Dex API."""

import sqlite3
from unittest.mock import MagicMock

import pytest

from dex_python.sync_back import (
    SyncBackMode,
    build_description_update,
    build_enrichment_note,
    build_job_title_update,
    get_contacts_for_sync,
    sync_as_description,
    sync_as_job_title,
    sync_as_notes,
)


@pytest.fixture
def mock_db() -> sqlite3.Connection:
    """Create in-memory database with test contacts."""
    conn = sqlite3.connect(":memory:")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE contacts (
            id TEXT PRIMARY KEY,
            first_name TEXT,
            last_name TEXT,
            job_title TEXT,
            company TEXT,
            role TEXT,
            full_data JSON
        )
    """)
    # Contact with company and role
    cursor.execute("""
        INSERT INTO contacts
        (id, first_name, last_name, job_title, company, role, full_data)
        VALUES ('c1', 'John', 'Doe', 'Engineer at Google', 'Google',
                'Engineer', '{"description": null}')
    """)
    # Contact with role only (no company)
    cursor.execute("""
        INSERT INTO contacts
        (id, first_name, last_name, job_title, company, role, full_data)
        VALUES ('c2', 'Jane', 'Smith', 'Senior Developer', NULL,
                'Senior Developer', '{"description": "Existing description"}')
    """)
    # Contact with no job title
    cursor.execute("""
        INSERT INTO contacts
        (id, first_name, last_name, job_title, company, role, full_data)
        VALUES ('c3', 'Bob', 'Jones', NULL, NULL, NULL, '{}')
    """)
    conn.commit()
    return conn


class TestBuildEnrichmentNote:
    """Tests for building enrichment notes."""

    def test_builds_note_with_company_and_role(self) -> None:
        """Build note text with both company and role."""
        note = build_enrichment_note(company="Google", role="Engineer")
        assert "Company: Google" in note
        assert "Role: Engineer" in note

    def test_builds_note_with_role_only(self) -> None:
        """Build note text with role only when no company."""
        note = build_enrichment_note(company=None, role="Senior Developer")
        assert "Role: Senior Developer" in note
        assert "Company:" not in note

    def test_returns_none_when_no_data(self) -> None:
        """Return None when neither company nor role available."""
        note = build_enrichment_note(company=None, role=None)
        assert note is None

    def test_includes_enrichment_tag(self) -> None:
        """Note should include tag for identification."""
        note = build_enrichment_note(company="Acme", role="Manager")
        assert "[Enriched]" in note or "enriched" in note.lower()


class TestBuildDescriptionUpdate:
    """Tests for building description field updates."""

    def test_creates_description_with_company_role(self) -> None:
        """Create description with company and role."""
        desc = build_description_update(
            company="Google",
            role="Engineer",
            existing_description=None,
        )
        assert "Google" in desc
        assert "Engineer" in desc

    def test_appends_to_existing_description(self) -> None:
        """Append enrichment to existing description."""
        desc = build_description_update(
            company="Google",
            role="Engineer",
            existing_description="Met at conference 2024",
        )
        assert "Met at conference 2024" in desc
        assert "Google" in desc

    def test_returns_none_when_no_enrichment(self) -> None:
        """Return None when no company/role to add."""
        desc = build_description_update(
            company=None,
            role=None,
            existing_description="Some notes",
        )
        assert desc is None

    def test_role_only_description(self) -> None:
        """Handle role-only case."""
        desc = build_description_update(
            company=None,
            role="Consultant",
            existing_description=None,
        )
        assert "Consultant" in desc


class TestBuildJobTitleUpdate:
    """Tests for reformatting job titles."""

    def test_formats_role_and_company(self) -> None:
        """Format as 'Role | Company'."""
        title = build_job_title_update(role="Engineer", company="Google")
        assert title == "Engineer | Google"

    def test_returns_role_when_no_company(self) -> None:
        """Return just role when no company."""
        title = build_job_title_update(role="Senior Developer", company=None)
        assert title == "Senior Developer"

    def test_returns_none_when_no_role(self) -> None:
        """Return None when no role available."""
        title = build_job_title_update(role=None, company="Google")
        assert title is None

    def test_returns_none_when_both_empty(self) -> None:
        """Return None when both empty."""
        title = build_job_title_update(role=None, company=None)
        assert title is None


class TestGetContactsForSync:
    """Tests for querying contacts that need sync."""

    def test_returns_contacts_with_enrichment(
        self, mock_db: sqlite3.Connection
    ) -> None:
        """Return contacts that have company or role data."""
        contacts = get_contacts_for_sync(mock_db)
        # Should return c1 (has company+role) and c2 (has role only)
        ids = [c["id"] for c in contacts]
        assert "c1" in ids
        assert "c2" in ids
        assert "c3" not in ids  # No enrichment data

    def test_returns_required_fields(self, mock_db: sqlite3.Connection) -> None:
        """Each contact dict has required fields."""
        contacts = get_contacts_for_sync(mock_db)
        for contact in contacts:
            assert "id" in contact
            assert "company" in contact
            assert "role" in contact
            assert "existing_description" in contact


class TestSyncBackMode:
    """Tests for sync back mode enum."""

    def test_has_all_modes(self) -> None:
        """Verify all sync modes are defined."""
        assert SyncBackMode.NOTES.value == "notes"
        assert SyncBackMode.DESCRIPTION.value == "description"
        assert SyncBackMode.JOB_TITLE.value == "job_title"


class TestSyncAsNotes:
    """Tests for syncing enrichment as notes."""

    def test_creates_note_for_each_contact(self, mock_db: sqlite3.Connection) -> None:
        """Create a note for each contact with enrichment."""
        mock_client = MagicMock()
        mock_client.create_note.return_value = {"id": "note-1"}

        stats = sync_as_notes(mock_db, mock_client)

        # Should create notes for c1 and c2 (c3 has no enrichment)
        assert mock_client.create_note.call_count == 2
        assert stats["created"] == 2
        assert stats["skipped"] == 0

    def test_skips_contacts_without_enrichment(
        self, mock_db: sqlite3.Connection
    ) -> None:
        """Skip contacts that have no company/role."""
        # Add contact with no enrichment
        cursor = mock_db.cursor()
        cursor.execute("""
            INSERT INTO contacts (id, first_name, last_name, company, role, full_data)
            VALUES ('c4', 'No', 'Data', NULL, NULL, '{}')
        """)
        mock_db.commit()

        mock_client = MagicMock()
        mock_client.create_note.return_value = {"id": "note-1"}

        stats = sync_as_notes(mock_db, mock_client)

        # c3 and c4 have no enrichment, should still only create 2 notes
        assert stats["created"] == 2

    def test_handles_api_errors(self, mock_db: sqlite3.Connection) -> None:
        """Track errors when API calls fail."""
        mock_client = MagicMock()
        mock_client.create_note.side_effect = Exception("API Error")

        stats = sync_as_notes(mock_db, mock_client)

        assert stats["errors"] == 2
        assert stats["created"] == 0


class TestSyncAsDescription:
    """Tests for syncing enrichment to description field."""

    def test_updates_description_for_each_contact(
        self, mock_db: sqlite3.Connection
    ) -> None:
        """Update description for each contact with enrichment."""
        mock_client = MagicMock()
        mock_client.update_contact.return_value = {"id": "c1"}

        stats = sync_as_description(mock_db, mock_client)

        assert mock_client.update_contact.call_count == 2
        assert stats["updated"] == 2

    def test_preserves_existing_description(self, mock_db: sqlite3.Connection) -> None:
        """Append to existing description rather than overwrite."""
        mock_client = MagicMock()
        mock_client.update_contact.return_value = {"id": "c2"}

        sync_as_description(mock_db, mock_client)

        # Find the call for c2 which has existing description
        calls = mock_client.update_contact.call_args_list
        c2_call = next(c for c in calls if c[0][0].contact_id == "c2")
        update_obj = c2_call[0][0]
        desc = update_obj.changes.get("description", "")
        assert "Existing description" in desc

    def test_handles_api_errors(self, mock_db: sqlite3.Connection) -> None:
        """Track errors when API calls fail."""
        mock_client = MagicMock()
        mock_client.update_contact.side_effect = Exception("API Error")

        stats = sync_as_description(mock_db, mock_client)

        assert stats["errors"] == 2
        assert stats["updated"] == 0


class TestSyncAsJobTitle:
    """Tests for syncing reformatted job title."""

    def test_updates_job_title_for_each_contact(
        self, mock_db: sqlite3.Connection
    ) -> None:
        """Update job_title for each contact with enrichment."""
        mock_client = MagicMock()
        mock_client.update_contact.return_value = {"id": "c1"}

        stats = sync_as_job_title(mock_db, mock_client)

        assert mock_client.update_contact.call_count == 2
        assert stats["updated"] == 2

    def test_formats_as_role_pipe_company(self, mock_db: sqlite3.Connection) -> None:
        """Job title should be formatted as 'Role | Company'."""
        mock_client = MagicMock()
        mock_client.update_contact.return_value = {"id": "c1"}

        sync_as_job_title(mock_db, mock_client)

        # Find call for c1 which has both role and company
        calls = mock_client.update_contact.call_args_list
        c1_call = next(c for c in calls if c[0][0].contact_id == "c1")
        update_obj = c1_call[0][0]
        job_title = update_obj.changes.get("job_title", "")
        assert job_title == "Engineer | Google"

    def test_handles_role_only(self, mock_db: sqlite3.Connection) -> None:
        """Handle contacts with role but no company."""
        mock_client = MagicMock()
        mock_client.update_contact.return_value = {"id": "c2"}

        sync_as_job_title(mock_db, mock_client)

        # Find call for c2 which has role only
        calls = mock_client.update_contact.call_args_list
        c2_call = next(c for c in calls if c[0][0].contact_id == "c2")
        update_obj = c2_call[0][0]
        job_title = update_obj.changes.get("job_title", "")
        assert job_title == "Senior Developer"

    def test_handles_api_errors(self, mock_db: sqlite3.Connection) -> None:
        """Track errors when API calls fail."""
        mock_client = MagicMock()
        mock_client.update_contact.side_effect = Exception("API Error")

        stats = sync_as_job_title(mock_db, mock_client)

        assert stats["errors"] == 2
        assert stats["updated"] == 0


class TestSyncBackCLI:
    """Tests for CLI argument parsing and mode selection."""

    def test_run_sync_dispatches_to_notes(self, mock_db: sqlite3.Connection) -> None:
        """Run sync with notes mode calls sync_as_notes."""
        from dex_python.sync_back import run_sync

        mock_client = MagicMock()
        mock_client.create_note.return_value = {"id": "note-1"}

        stats = run_sync(mock_db, mock_client, SyncBackMode.NOTES)

        assert mock_client.create_note.call_count == 2
        assert "created" in stats

    def test_run_sync_dispatches_to_description(
        self, mock_db: sqlite3.Connection
    ) -> None:
        """Run sync with description mode calls sync_as_description."""
        from dex_python.sync_back import run_sync

        mock_client = MagicMock()
        mock_client.update_contact.return_value = {"id": "c1"}

        stats = run_sync(mock_db, mock_client, SyncBackMode.DESCRIPTION)

        assert mock_client.update_contact.call_count == 2
        assert "updated" in stats

    def test_run_sync_dispatches_to_job_title(
        self, mock_db: sqlite3.Connection
    ) -> None:
        """Run sync with job_title mode calls sync_as_job_title."""
        from dex_python.sync_back import run_sync

        mock_client = MagicMock()
        mock_client.update_contact.return_value = {"id": "c1"}

        stats = run_sync(mock_db, mock_client, SyncBackMode.JOB_TITLE)

        assert mock_client.update_contact.call_count == 2
        assert "updated" in stats
