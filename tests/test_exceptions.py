"""Tests for custom exceptions."""

import pytest
from pytest_httpx import HTTPXMock

from src.dex_import import DexClient, Settings
from src.dex_import.exceptions import (
    AuthenticationError,
    ContactNotFoundError,
    DexAPIError,
    NoteNotFoundError,
    RateLimitError,
    ReminderNotFoundError,
    ValidationError,
)


class TestDexAPIError:
    """Test suite for base DexAPIError."""

    def test_base_error_with_message(self) -> None:
        """Test creating base error with message."""
        error = DexAPIError("Something went wrong")
        assert str(error) == "Something went wrong"
        assert error.status_code is None

    def test_base_error_with_status_code(self) -> None:
        """Test creating base error with status code."""
        error = DexAPIError("Server error", status_code=500)
        assert error.status_code == 500

    def test_base_error_with_response_data(self) -> None:
        """Test creating base error with response data."""
        error = DexAPIError(
            "Bad request",
            status_code=400,
            response_data={"error": "Invalid field"},
        )
        assert error.response_data == {"error": "Invalid field"}


class TestAuthenticationError:
    """Test suite for AuthenticationError."""

    def test_authentication_error(self) -> None:
        """Test authentication error."""
        error = AuthenticationError("Invalid API key")
        assert isinstance(error, DexAPIError)
        assert str(error) == "Invalid API key"


class TestNotFoundErrors:
    """Test suite for NotFound errors."""

    def test_contact_not_found(self) -> None:
        """Test ContactNotFoundError."""
        error = ContactNotFoundError("contact-123")
        assert isinstance(error, DexAPIError)
        assert "contact-123" in str(error)

    def test_reminder_not_found(self) -> None:
        """Test ReminderNotFoundError."""
        error = ReminderNotFoundError("reminder-456")
        assert isinstance(error, DexAPIError)
        assert "reminder-456" in str(error)

    def test_note_not_found(self) -> None:
        """Test NoteNotFoundError."""
        error = NoteNotFoundError("note-789")
        assert isinstance(error, DexAPIError)
        assert "note-789" in str(error)


class TestRateLimitError:
    """Test suite for RateLimitError."""

    def test_rate_limit_error(self) -> None:
        """Test rate limit error."""
        error = RateLimitError("Too many requests")
        assert isinstance(error, DexAPIError)

    def test_rate_limit_with_retry_after(self) -> None:
        """Test rate limit error with retry-after."""
        error = RateLimitError("Too many requests", retry_after=60)
        assert error.retry_after == 60


class TestValidationError:
    """Test suite for ValidationError."""

    def test_validation_error(self) -> None:
        """Test validation error."""
        error = ValidationError("Invalid email format")
        assert isinstance(error, DexAPIError)


class TestClientRaisesExceptions:
    """Test that client raises appropriate exceptions."""

    def test_401_raises_authentication_error(
        self, settings: Settings, httpx_mock: HTTPXMock
    ) -> None:
        """Test 401 response raises AuthenticationError."""
        httpx_mock.add_response(
            url="https://api.getdex.com/api/rest/contacts?limit=100&offset=0",
            status_code=401,
            json={"error": "Invalid API key"},
        )

        with pytest.raises(AuthenticationError):
            with DexClient(settings) as client:
                client.get_contacts()

    def test_404_contact_raises_not_found(
        self, settings: Settings, httpx_mock: HTTPXMock
    ) -> None:
        """Test 404 on contact raises ContactNotFoundError."""
        httpx_mock.add_response(
            url="https://api.getdex.com/api/rest/contacts/invalid-id",
            status_code=404,
            json={"error": "Contact not found"},
        )

        with pytest.raises(ContactNotFoundError):
            with DexClient(settings) as client:
                client.get_contact("invalid-id")

    def test_429_raises_rate_limit_error(
        self, settings: Settings, httpx_mock: HTTPXMock
    ) -> None:
        """Test 429 response raises RateLimitError."""
        httpx_mock.add_response(
            url="https://api.getdex.com/api/rest/contacts?limit=100&offset=0",
            status_code=429,
            json={"error": "Rate limit exceeded"},
        )

        with pytest.raises(RateLimitError):
            with DexClient(settings) as client:
                client.get_contacts()

    def test_400_raises_validation_error(
        self, settings: Settings, httpx_mock: HTTPXMock
    ) -> None:
        """Test 400 response raises ValidationError."""
        httpx_mock.add_response(
            url="https://api.getdex.com/api/rest/contacts",
            method="POST",
            status_code=400,
            json={"error": "Invalid request body"},
        )

        with pytest.raises(ValidationError):
            with DexClient(settings) as client:
                from src.dex_import import ContactCreate

                client.create_contact(ContactCreate(first_name="Test"))

    def test_500_raises_dex_api_error(
        self, settings: Settings, httpx_mock: HTTPXMock
    ) -> None:
        """Test 500 response raises DexAPIError."""
        httpx_mock.add_response(
            url="https://api.getdex.com/api/rest/contacts?limit=100&offset=0",
            status_code=500,
            json={"error": "Internal server error"},
        )

        with pytest.raises(DexAPIError):
            with DexClient(settings) as client:
                client.get_contacts()
