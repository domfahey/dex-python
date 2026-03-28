"""Tests for error handling in client modules.

Tests _handle_error() method and exception behaviors.
"""

import pytest
from pytest_httpx import HTTPXMock

from dex_python import DexClient, Settings
from dex_python.async_client import AsyncDexClient
from dex_python.exceptions import (
    AuthenticationError,
    ContactNotFoundError,
    DexAPIError,
    NoteNotFoundError,
    RateLimitError,
    ReminderNotFoundError,
    ValidationError,
)

class TestSyncClientErrorHandling:
    """Test DexClient._handle_error() method."""

    def test_401_includes_response_data(
        self, settings: Settings, httpx_mock: HTTPXMock
    ) -> None:
        """AuthenticationError should include response_data."""
        httpx_mock.add_response(
            url="https://api.getdex.com/api/rest/contacts?limit=100&offset=0",
            status_code=401,
            json={"error": "Invalid API key", "details": "Key expired"},
        )

        with DexClient(settings) as client:
            with pytest.raises(AuthenticationError) as exc_info:
                client.get_contacts()

        assert exc_info.value.status_code == 401
        assert exc_info.value.response_data == {
            "error": "Invalid API key",
            "details": "Key expired",
        }

    def test_400_extracts_error_message(
        self, settings: Settings, httpx_mock: HTTPXMock
    ) -> None:
        """ValidationError should extract error message from response."""
        httpx_mock.add_response(
            url="https://api.getdex.com/api/rest/contacts",
            method="POST",
            status_code=400,
            json={"error": "first_name is required"},
        )

        from dex_python import ContactCreate

        with DexClient(settings) as client:
            with pytest.raises(ValidationError) as exc_info:
                client.create_contact(ContactCreate())

        assert "first_name is required" in str(exc_info.value)

    def test_400_default_message(
        self, settings: Settings, httpx_mock: HTTPXMock
    ) -> None:
        """ValidationError should use default message when error key missing."""
        httpx_mock.add_response(
            url="https://api.getdex.com/api/rest/contacts",
            method="POST",
            status_code=400,
            json={"details": "some details"},  # No "error" key
        )

        from dex_python import ContactCreate

        with DexClient(settings) as client:
            with pytest.raises(ValidationError) as exc_info:
                client.create_contact(ContactCreate())

        assert "Validation error" in str(exc_info.value)

    def test_429_extracts_retry_after_header(
        self, settings: Settings, httpx_mock: HTTPXMock
    ) -> None:
        """RateLimitError should extract Retry-After header."""
        httpx_mock.add_response(
            url="https://api.getdex.com/api/rest/contacts?limit=100&offset=0",
            status_code=429,
            headers={"Retry-After": "120"},
            json={"error": "Rate limit exceeded"},
        )

        with DexClient(settings) as client:
            with pytest.raises(RateLimitError) as exc_info:
                client.get_contacts()

        assert exc_info.value.retry_after == 120

    def test_429_without_retry_after_header(
        self, settings: Settings, httpx_mock: HTTPXMock
    ) -> None:
        """RateLimitError should handle missing Retry-After header."""
        httpx_mock.add_response(
            url="https://api.getdex.com/api/rest/contacts?limit=100&offset=0",
            status_code=429,
            json={"error": "Rate limit exceeded"},
        )

        with DexClient(settings) as client:
            with pytest.raises(RateLimitError) as exc_info:
                client.get_contacts()

        assert exc_info.value.retry_after is None

    def test_404_contact_extracts_id(
        self, settings: Settings, httpx_mock: HTTPXMock
    ) -> None:
        """ContactNotFoundError should extract contact_id from endpoint."""
        httpx_mock.add_response(
            url="https://api.getdex.com/api/rest/contacts/contact-abc-123",
            status_code=404,
            json={"error": "Not found"},
        )

        with DexClient(settings) as client:
            with pytest.raises(ContactNotFoundError) as exc_info:
                client.get_contact("contact-abc-123")

        assert exc_info.value.contact_id == "contact-abc-123"

    def test_404_reminder_extracts_id(
        self, settings: Settings, httpx_mock: HTTPXMock
    ) -> None:
        """ReminderNotFoundError should extract reminder_id from endpoint."""
        httpx_mock.add_response(
            url="https://api.getdex.com/api/rest/reminders/reminder-xyz",
            method="DELETE",
            status_code=404,
            json={"error": "Not found"},
        )

        with DexClient(settings) as client:
            with pytest.raises(ReminderNotFoundError) as exc_info:
                client.delete_reminder("reminder-xyz")

        assert exc_info.value.reminder_id == "reminder-xyz"

    def test_404_note_extracts_id(
        self, settings: Settings, httpx_mock: HTTPXMock
    ) -> None:
        """NoteNotFoundError should extract note_id from endpoint."""
        httpx_mock.add_response(
            url="https://api.getdex.com/api/rest/timeline_items/note-999",
            method="DELETE",
            status_code=404,
            json={"error": "Not found"},
        )

        with DexClient(settings) as client:
            with pytest.raises(NoteNotFoundError) as exc_info:
                client.delete_note("note-999")

        assert exc_info.value.note_id == "note-999"

    def test_404_generic_endpoint(
        self, settings: Settings, httpx_mock: HTTPXMock
    ) -> None:
        """404 on non-resource endpoint should raise generic DexAPIError."""
        httpx_mock.add_response(
            url="https://api.getdex.com/api/rest/search/contacts?email=test%40test.com",
            status_code=404,
            json={"error": "Route not found"},
        )

        with DexClient(settings) as client:
            with pytest.raises(DexAPIError) as exc_info:
                client.get_contact_by_email("test@test.com")

        assert exc_info.value.status_code == 404
        # Should NOT be ContactNotFoundError
        assert not isinstance(exc_info.value, ContactNotFoundError)

    def test_500_includes_error_message(
        self, settings: Settings, httpx_mock: HTTPXMock
    ) -> None:
        """DexAPIError should include error message from response."""
        httpx_mock.add_response(
            url="https://api.getdex.com/api/rest/contacts?limit=100&offset=0",
            status_code=500,
            json={"error": "Database connection failed"},
        )

        with DexClient(settings) as client:
            with pytest.raises(DexAPIError) as exc_info:
                client.get_contacts()

        assert "Database connection failed" in str(exc_info.value)
        assert exc_info.value.status_code == 500

    def test_500_default_message(
        self, settings: Settings, httpx_mock: HTTPXMock
    ) -> None:
        """DexAPIError should use default message when error key missing."""
        httpx_mock.add_response(
            url="https://api.getdex.com/api/rest/contacts?limit=100&offset=0",
            status_code=500,
            json={"details": "Internal error"},
        )

        with DexClient(settings) as client:
            with pytest.raises(DexAPIError) as exc_info:
                client.get_contacts()

        assert "API error: 500" in str(exc_info.value)

    def test_malformed_json_response(
        self, settings: Settings, httpx_mock: HTTPXMock
    ) -> None:
        """Error handler should handle malformed JSON gracefully."""
        httpx_mock.add_response(
            url="https://api.getdex.com/api/rest/contacts?limit=100&offset=0",
            status_code=500,
            content=b"Internal Server Error",  # Not JSON
        )

        with DexClient(settings) as client:
            with pytest.raises(DexAPIError) as exc_info:
                client.get_contacts()

        assert exc_info.value.status_code == 500
        # response_data should be empty dict when JSON parsing fails
        assert exc_info.value.response_data == {}

    def test_empty_json_response(
        self, settings: Settings, httpx_mock: HTTPXMock
    ) -> None:
        """Error handler should handle empty JSON response."""
        httpx_mock.add_response(
            url="https://api.getdex.com/api/rest/contacts?limit=100&offset=0",
            status_code=502,
            json={},
        )

        with DexClient(settings) as client:
            with pytest.raises(DexAPIError) as exc_info:
                client.get_contacts()

        assert exc_info.value.status_code == 502

    def test_404_with_nested_path(
        self, settings: Settings, httpx_mock: HTTPXMock
    ) -> None:
        """404 extraction should work with nested paths."""
        httpx_mock.add_response(
            url="https://api.getdex.com/api/rest/timeline_items/contacts/contact-123",
            status_code=404,
            json={"error": "Not found"},
        )

        with DexClient(settings) as client:
            with pytest.raises(DexAPIError):
                client.get_notes_by_contact("contact-123")


@pytest.mark.asyncio
class TestAsyncClientErrorHandling:
    """Test AsyncDexClient._handle_error() method."""

    async def test_401_includes_response_data(
        self, settings: Settings, httpx_mock: HTTPXMock
    ) -> None:
        """AuthenticationError should include response_data."""
        httpx_mock.add_response(
            url="https://api.getdex.com/api/rest/contacts?limit=100&offset=0",
            status_code=401,
            json={"error": "Invalid API key"},
        )

        async with AsyncDexClient(settings) as client:
            with pytest.raises(AuthenticationError) as exc_info:
                await client.get_contacts()

        assert exc_info.value.response_data == {"error": "Invalid API key"}

    async def test_429_extracts_retry_after(
        self, settings: Settings, httpx_mock: HTTPXMock
    ) -> None:
        """RateLimitError should extract Retry-After header."""
        httpx_mock.add_response(
            url="https://api.getdex.com/api/rest/contacts?limit=100&offset=0",
            status_code=429,
            headers={"Retry-After": "30"},
            json={"error": "Rate limited"},
        )

        async with AsyncDexClient(settings) as client:
            with pytest.raises(RateLimitError) as exc_info:
                await client.get_contacts()

        assert exc_info.value.retry_after == 30

    async def test_malformed_json_response(
        self, settings: Settings, httpx_mock: HTTPXMock
    ) -> None:
        """Error handler should handle malformed JSON gracefully."""
        httpx_mock.add_response(
            url="https://api.getdex.com/api/rest/contacts?limit=100&offset=0",
            status_code=500,
            content=b"Gateway Timeout",
        )

        async with AsyncDexClient(settings) as client:
            with pytest.raises(DexAPIError) as exc_info:
                await client.get_contacts()

        assert exc_info.value.response_data == {}


class TestExceptionHierarchy:
    """Test exception hierarchy and attributes."""

    def test_all_exceptions_inherit_from_dex_api_error(self) -> None:
        """All custom exceptions should inherit from DexAPIError."""
        assert issubclass(AuthenticationError, DexAPIError)
        assert issubclass(ValidationError, DexAPIError)
        assert issubclass(RateLimitError, DexAPIError)
        assert issubclass(ContactNotFoundError, DexAPIError)
        assert issubclass(ReminderNotFoundError, DexAPIError)
        assert issubclass(NoteNotFoundError, DexAPIError)

    def test_dex_api_error_attributes(self) -> None:
        """DexAPIError should have status_code and response_data attributes."""
        error = DexAPIError("Test error", status_code=500, response_data={"key": "val"})
        assert error.status_code == 500
        assert error.response_data == {"key": "val"}
        assert str(error) == "Test error"

    def test_dex_api_error_default_attributes(self) -> None:
        """DexAPIError should handle None attributes."""
        error = DexAPIError("Test error")
        assert error.status_code is None
        assert error.response_data is None

    def test_contact_not_found_has_contact_id(self) -> None:
        """ContactNotFoundError should have contact_id attribute."""
        error = ContactNotFoundError("abc-123")
        assert error.contact_id == "abc-123"
        assert error.status_code == 404
        assert "abc-123" in str(error)

    def test_reminder_not_found_has_reminder_id(self) -> None:
        """ReminderNotFoundError should have reminder_id attribute."""
        error = ReminderNotFoundError("rem-456")
        assert error.reminder_id == "rem-456"
        assert error.status_code == 404
        assert "rem-456" in str(error)

    def test_note_not_found_has_note_id(self) -> None:
        """NoteNotFoundError should have note_id attribute."""
        error = NoteNotFoundError("note-789")
        assert error.note_id == "note-789"
        assert error.status_code == 404
        assert "note-789" in str(error)

    def test_rate_limit_error_has_retry_after(self) -> None:
        """RateLimitError should have retry_after attribute."""
        error = RateLimitError("Rate limited", retry_after=60)
        assert error.retry_after == 60
        assert error.status_code == 429

    def test_rate_limit_error_none_retry_after(self) -> None:
        """RateLimitError should handle None retry_after."""
        error = RateLimitError("Rate limited")
        assert error.retry_after is None


class TestErrorStatusCodes:
    """Test various HTTP status codes are handled correctly."""

    @pytest.mark.parametrize(
        "status_code,expected_exception",
        [
            (400, ValidationError),
            (401, AuthenticationError),
            (429, RateLimitError),
            (500, DexAPIError),
            (502, DexAPIError),
            (503, DexAPIError),
            (504, DexAPIError),
        ],
    )
    def test_status_code_to_exception_mapping(
        self,
        settings: Settings,
        httpx_mock: HTTPXMock,
        status_code: int,
        expected_exception: type[Exception],
    ) -> None:
        """Test correct exception is raised for each status code."""
        httpx_mock.add_response(
            url="https://api.getdex.com/api/rest/contacts?limit=100&offset=0",
            status_code=status_code,
            json={"error": "Test error"},
        )

        with DexClient(settings) as client:
            with pytest.raises(expected_exception):
                client.get_contacts()
