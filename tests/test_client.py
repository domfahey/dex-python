"""Tests for the Dex API client."""

from pytest_httpx import HTTPXMock

from src.dex_import import ContactCreate, DexClient, Settings


class TestDexClient:
    """Test suite for DexClient."""

    def test_client_uses_correct_headers(self, settings: Settings) -> None:
        """Verify client sets required headers."""
        client = DexClient(settings)
        headers = client._client.headers

        assert headers["content-type"] == "application/json"
        assert headers["x-hasura-dex-api-key"] == "test-api-key"
        client.close()

    def test_get_contacts(self, settings: Settings, httpx_mock: HTTPXMock) -> None:
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

        with DexClient(settings) as client:
            contacts = client.get_contacts()

        assert len(contacts) == 2
        assert contacts[0]["first_name"] == "John"

    def test_get_contact_by_id(self, settings: Settings, httpx_mock: HTTPXMock) -> None:
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

        with DexClient(settings) as client:
            contact = client.get_contact("123")

        assert contact["id"] == "123"
        assert contact["emails"][0]["email"] == "john@example.com"

    def test_get_contact_by_email(
        self, settings: Settings, httpx_mock: HTTPXMock
    ) -> None:
        """Test fetching contact by email."""
        mock_response = {
            "search_contacts_by_exact_email": [
                {
                    "id": "456",
                    "first_name": "Jane",
                    "emails": [{"email": "jane@example.com"}],
                }
            ]
        }
        httpx_mock.add_response(
            url="https://api.getdex.com/api/rest/search/contacts?email=jane%40example.com",
            json=mock_response,
        )

        with DexClient(settings) as client:
            contact = client.get_contact_by_email("jane@example.com")

        assert contact is not None
        assert contact["id"] == "456"

    def test_create_contact(self, settings: Settings, httpx_mock: HTTPXMock) -> None:
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

        with DexClient(settings) as client:
            result = client.create_contact(new_contact)

        assert result["insert_contacts_one"]["id"] == "789"
        assert result["insert_contacts_one"]["first_name"] == "Alice"

    def test_create_contact_with_email(
        self, settings: Settings, httpx_mock: HTTPXMock
    ) -> None:
        """Test creating contact with email using factory method."""
        new_contact = ContactCreate.with_email(
            email="bob@example.com",
            first_name="Bob",
            last_name="Builder",
        )
        mock_response = {"insert_contacts_one": {"id": "999", "first_name": "Bob"}}

        httpx_mock.add_response(
            url="https://api.getdex.com/api/rest/contacts",
            method="POST",
            json=mock_response,
        )

        with DexClient(settings) as client:
            result = client.create_contact(new_contact)

        assert result["insert_contacts_one"]["id"] == "999"
        # Verify the contact has correct email structure
        assert new_contact.contact_emails == {"data": {"email": "bob@example.com"}}

    def test_delete_contact(self, settings: Settings, httpx_mock: HTTPXMock) -> None:
        """Test deleting a contact."""
        httpx_mock.add_response(
            url="https://api.getdex.com/api/rest/contacts/123",
            method="DELETE",
            json={"affected_rows": 1},
        )

        with DexClient(settings) as client:
            result = client.delete_contact("123")

        assert result["affected_rows"] == 1

    def test_context_manager(self, settings: Settings) -> None:
        """Test client works as context manager."""
        with DexClient(settings) as client:
            assert client._client is not None
        assert client._client.is_closed


class TestContactCreate:
    """Test suite for ContactCreate model."""

    def test_basic_contact(self) -> None:
        """Test creating basic contact."""
        contact = ContactCreate(first_name="Test", last_name="User")
        assert contact.first_name == "Test"
        assert contact.last_name == "User"
        assert contact.contact_emails is None

    def test_with_email_factory(self) -> None:
        """Test with_email factory method."""
        contact = ContactCreate.with_email(
            email="test@example.com",
            first_name="Test",
        )
        assert contact.first_name == "Test"
        assert contact.contact_emails == {"data": {"email": "test@example.com"}}

    def test_with_phone_factory(self) -> None:
        """Test with_phone factory method."""
        contact = ContactCreate.with_phone(
            phone_number="+1234567890",
            label="Mobile",
            first_name="Test",
        )
        assert contact.first_name == "Test"
        assert contact.contact_phone_numbers == {
            "data": {"phone_number": "+1234567890", "label": "Mobile"}
        }

    def test_model_dump_excludes_none(self) -> None:
        """Test model dump excludes None values."""
        contact = ContactCreate(first_name="Only")
        data = contact.model_dump(exclude_none=True)

        assert "first_name" in data
        assert "last_name" not in data
        assert "contact_emails" not in data
