"""Tests for the async Dex API client."""

import pytest
from pytest_httpx import HTTPXMock

from src.dex_import import ContactCreate, Settings
from src.dex_import.async_client import AsyncDexClient
from src.dex_import.exceptions import AuthenticationError, ContactNotFoundError


class TestAsyncDexClient:
    """Test suite for AsyncDexClient."""

    @pytest.mark.asyncio
    async def test_client_uses_correct_headers(self, settings: Settings) -> None:
        """Verify client sets required headers."""
        async with AsyncDexClient(settings) as client:
            headers = client._client.headers
            assert headers["content-type"] == "application/json"
            assert headers["x-hasura-dex-api-key"] == "test-api-key"

    @pytest.mark.asyncio
    async def test_get_contacts(
        self, settings: Settings, httpx_mock: HTTPXMock
    ) -> None:
        """Test fetching contacts list."""
        mock_response = {
            "contacts": [
                {"id": "1", "first_name": "John", "last_name": "Doe"},
                {"id": "2", "first_name": "Jane", "last_name": "Smith"},
            ],
            "pagination": {"total": {"count": 2}},
        }
        httpx_mock.add_response(
            url="https://api.getdex.com/api/rest/contacts?limit=100&offset=0",
            json=mock_response,
        )

        async with AsyncDexClient(settings) as client:
            contacts = await client.get_contacts()

        assert len(contacts) == 2
        assert contacts[0]["first_name"] == "John"

    @pytest.mark.asyncio
    async def test_get_contact_by_id(
        self, settings: Settings, httpx_mock: HTTPXMock
    ) -> None:
        """Test fetching a single contact."""
        mock_response = {
            "contacts": [
                {
                    "id": "123",
                    "first_name": "John",
                    "emails": [{"email": "john@example.com"}],
                }
            ]
        }
        httpx_mock.add_response(
            url="https://api.getdex.com/api/rest/contacts/123",
            json=mock_response,
        )

        async with AsyncDexClient(settings) as client:
            contact = await client.get_contact("123")

        assert contact["id"] == "123"

    @pytest.mark.asyncio
    async def test_create_contact(
        self, settings: Settings, httpx_mock: HTTPXMock
    ) -> None:
        """Test creating a new contact."""
        new_contact = ContactCreate(first_name="Alice", last_name="Wonder")
        mock_response = {
            "insert_contacts_one": {
                "id": "789",
                "first_name": "Alice",
                "last_name": "Wonder",
            }
        }

        httpx_mock.add_response(
            url="https://api.getdex.com/api/rest/contacts",
            method="POST",
            json=mock_response,
        )

        async with AsyncDexClient(settings) as client:
            result = await client.create_contact(new_contact)

        assert result["insert_contacts_one"]["id"] == "789"

    @pytest.mark.asyncio
    async def test_delete_contact(
        self, settings: Settings, httpx_mock: HTTPXMock
    ) -> None:
        """Test deleting a contact."""
        httpx_mock.add_response(
            url="https://api.getdex.com/api/rest/contacts/123",
            method="DELETE",
            json={"affected_rows": 1},
        )

        async with AsyncDexClient(settings) as client:
            result = await client.delete_contact("123")

        assert result["affected_rows"] == 1

    @pytest.mark.asyncio
    async def test_401_raises_authentication_error(
        self, settings: Settings, httpx_mock: HTTPXMock
    ) -> None:
        """Test 401 response raises AuthenticationError."""
        httpx_mock.add_response(
            url="https://api.getdex.com/api/rest/contacts?limit=100&offset=0",
            status_code=401,
            json={"error": "Invalid API key"},
        )

        with pytest.raises(AuthenticationError):
            async with AsyncDexClient(settings) as client:
                await client.get_contacts()

    @pytest.mark.asyncio
    async def test_404_raises_contact_not_found(
        self, settings: Settings, httpx_mock: HTTPXMock
    ) -> None:
        """Test 404 on contact raises ContactNotFoundError."""
        httpx_mock.add_response(
            url="https://api.getdex.com/api/rest/contacts/invalid-id",
            status_code=404,
            json={"error": "Contact not found"},
        )

        with pytest.raises(ContactNotFoundError):
            async with AsyncDexClient(settings) as client:
                await client.get_contact("invalid-id")

    @pytest.mark.asyncio
    async def test_context_manager(self, settings: Settings) -> None:
        """Test client works as async context manager."""
        async with AsyncDexClient(settings) as client:
            assert client._client is not None
        assert client._client.is_closed
