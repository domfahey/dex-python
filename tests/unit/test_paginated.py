"""Tests for paginated response methods."""

from pytest_httpx import HTTPXMock

from dex_python import DexClient, Settings
from dex_python.models import PaginatedContacts, PaginatedNotes, PaginatedReminders


class TestPaginatedContacts:
    """Test suite for paginated contacts response."""

    def test_get_contacts_paginated(
        self, settings: Settings, httpx_mock: HTTPXMock
    ) -> None:
        """Test fetching paginated contacts with metadata."""
        httpx_mock.add_response(
            url="https://api.getdex.com/api/rest/contacts?limit=10&offset=0",
            json={
                "contacts": [{"id": "1", "first_name": "John"}],
                "pagination": {"total": {"count": 100}},
            },
        )

        with DexClient(settings) as client:
            result = client.get_contacts_paginated(limit=10, offset=0)

        assert isinstance(result, PaginatedContacts)
        assert len(result.contacts) == 1
        assert result.total == 100
        assert result.limit == 10
        assert result.offset == 0
        assert result.has_more is True

    def test_get_contacts_paginated_no_more(
        self, settings: Settings, httpx_mock: HTTPXMock
    ) -> None:
        """Test has_more is False when all results fetched."""
        httpx_mock.add_response(
            url="https://api.getdex.com/api/rest/contacts?limit=10&offset=0",
            json={
                "contacts": [{"id": "1"}],
                "pagination": {"total": {"count": 1}},
            },
        )

        with DexClient(settings) as client:
            result = client.get_contacts_paginated(limit=10, offset=0)

        assert result.has_more is False


class TestPaginatedReminders:
    """Test suite for paginated reminders response."""

    def test_get_reminders_paginated(
        self, settings: Settings, httpx_mock: HTTPXMock
    ) -> None:
        """Test fetching paginated reminders with metadata."""
        httpx_mock.add_response(
            url="https://api.getdex.com/api/rest/reminders?limit=10&offset=0",
            json={
                "reminders": [{"id": "1", "body": "Test"}],
                "total": {"aggregate": {"count": 50}},
            },
        )

        with DexClient(settings) as client:
            result = client.get_reminders_paginated(limit=10, offset=0)

        assert isinstance(result, PaginatedReminders)
        assert len(result.reminders) == 1
        assert result.total == 50
        assert result.has_more is True


class TestPaginatedNotes:
    """Test suite for paginated notes response."""

    def test_get_notes_paginated(
        self, settings: Settings, httpx_mock: HTTPXMock
    ) -> None:
        """Test fetching paginated notes with metadata."""
        httpx_mock.add_response(
            url="https://api.getdex.com/api/rest/timeline_items?limit=10&offset=0",
            json={
                "timeline_items": [{"id": "1", "note": "Test note"}],
                "pagination": {"total": {"count": 25}},
            },
        )

        with DexClient(settings) as client:
            result = client.get_notes_paginated(limit=10, offset=0)

        assert isinstance(result, PaginatedNotes)
        assert len(result.notes) == 1
        assert result.total == 25
        assert result.has_more is True
