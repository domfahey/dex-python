"""Integration tests that hit the live Dex API."""

import os
import uuid

import pytest

from dex_python import ContactCreate, DexClient


def _live_tests_enabled() -> bool:
    """Gate integration tests behind explicit opt-in.

    This avoids accidental writes against live data stores in normal test runs.
    """
    enabled = os.getenv("DEX_RUN_LIVE_TESTS", "").strip().lower() in {
        "1",
        "true",
        "yes",
    }
    return bool(os.getenv("DEX_API_KEY")) and enabled


pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        not _live_tests_enabled(),
        reason="Set DEX_RUN_LIVE_TESTS=1 and DEX_API_KEY to run live integration tests",
    ),
]


@pytest.fixture
def live_client() -> DexClient:
    """Create a client configured for live API."""
    return DexClient()


class TestLiveAPI:
    """Integration tests against live Dex API."""

    def test_get_contacts_returns_list(self, live_client: DexClient) -> None:
        """Verify we can fetch contacts from live API."""
        with live_client as client:
            contacts = client.get_contacts(limit=5)

        assert isinstance(contacts, list)

    def test_client_authenticates_successfully(self, live_client: DexClient) -> None:
        """Verify API key authentication works."""
        with live_client as client:
            contacts = client.get_contacts(limit=1)
            assert contacts is not None

    def test_create_and_delete_contact(self, live_client: DexClient) -> None:
        """Test full contact lifecycle."""
        suffix = uuid.uuid4().hex[:8]
        contact_id: str | None = None

        with live_client as client:
            try:
                new_contact = ContactCreate(
                    first_name="IntegrationTest",
                    last_name=f"ToDelete-{suffix}",
                )
                result = client.create_contact(new_contact)
                contact_id = result["id"]
                assert contact_id is not None
            finally:
                if contact_id:
                    delete_result = client.delete_contact(contact_id)
                    assert delete_result["id"] == contact_id

    def test_get_reminders(self, live_client: DexClient) -> None:
        """Verify we can fetch reminders."""
        with live_client as client:
            reminders = client.get_reminders(limit=5)
            assert isinstance(reminders, list)

    def test_get_notes(self, live_client: DexClient) -> None:
        """Verify we can fetch notes."""
        with live_client as client:
            notes = client.get_notes(limit=5)
            assert isinstance(notes, list)
