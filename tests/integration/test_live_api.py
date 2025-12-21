"""Integration tests that hit the live Dex API."""

import os
import uuid

import pytest

from dex_python import ContactCreate, DexClient

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        not os.getenv("DEX_API_KEY"),
        reason="DEX_API_KEY not set - skipping integration tests",
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
                contact_id = result["insert_contacts_one"]["id"]
                assert contact_id is not None
            finally:
                if contact_id:
                    client.delete_contact(contact_id)

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
