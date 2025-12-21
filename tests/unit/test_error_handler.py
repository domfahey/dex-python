"""Tests for the shared error handling module."""

import httpx
import pytest

from dex_python.error_handler import handle_error_response
from dex_python.exceptions import (
    AuthenticationError,
    ContactNotFoundError,
    DexAPIError,
    NoteNotFoundError,
    RateLimitError,
    ReminderNotFoundError,
    ValidationError,
)


class TestHandleErrorResponse:
    """Tests for the handle_error_response function."""

    def test_401_raises_authentication_error(self) -> None:
        """Test that 401 status raises AuthenticationError."""
        response = httpx.Response(
            status_code=401,
            json={"error": "Unauthorized"},
        )
        with pytest.raises(AuthenticationError) as exc_info:
            handle_error_response(response, "/contacts")
        assert exc_info.value.status_code == 401
        assert "Invalid API key" in str(exc_info.value)

    def test_429_raises_rate_limit_error(self) -> None:
        """Test that 429 status raises RateLimitError."""
        response = httpx.Response(
            status_code=429,
            headers={"Retry-After": "60"},
            json={"error": "Too many requests"},
        )
        with pytest.raises(RateLimitError) as exc_info:
            handle_error_response(response, "/contacts")
        assert exc_info.value.retry_after == 60

    def test_429_without_retry_after_header(self) -> None:
        """Test that 429 without Retry-After header works."""
        response = httpx.Response(
            status_code=429,
            json={"error": "Too many requests"},
        )
        with pytest.raises(RateLimitError) as exc_info:
            handle_error_response(response, "/contacts")
        assert exc_info.value.retry_after is None

    def test_400_raises_validation_error(self) -> None:
        """Test that 400 status raises ValidationError."""
        response = httpx.Response(
            status_code=400,
            json={"error": "Invalid input"},
        )
        with pytest.raises(ValidationError) as exc_info:
            handle_error_response(response, "/contacts")
        assert exc_info.value.status_code == 400
        assert "Invalid input" in str(exc_info.value)

    def test_400_without_error_message(self) -> None:
        """Test that 400 without error message uses default."""
        response = httpx.Response(
            status_code=400,
            json={},
        )
        with pytest.raises(ValidationError) as exc_info:
            handle_error_response(response, "/contacts")
        assert "Validation error" in str(exc_info.value)

    def test_404_contacts_raises_contact_not_found(self) -> None:
        """Test that 404 on /contacts endpoint raises ContactNotFoundError."""
        response = httpx.Response(
            status_code=404,
            json={"error": "Not found"},
        )
        with pytest.raises(ContactNotFoundError) as exc_info:
            handle_error_response(response, "/contacts/abc123")
        assert exc_info.value.contact_id == "abc123"

    def test_404_reminders_raises_reminder_not_found(self) -> None:
        """Test that 404 on /reminders endpoint raises ReminderNotFoundError."""
        response = httpx.Response(
            status_code=404,
            json={"error": "Not found"},
        )
        with pytest.raises(ReminderNotFoundError) as exc_info:
            handle_error_response(response, "/reminders/xyz789")
        assert exc_info.value.reminder_id == "xyz789"

    def test_404_timeline_items_raises_note_not_found(self) -> None:
        """Test that 404 on /timeline_items endpoint raises NoteNotFoundError."""
        response = httpx.Response(
            status_code=404,
            json={"error": "Not found"},
        )
        with pytest.raises(NoteNotFoundError) as exc_info:
            handle_error_response(response, "/timeline_items/note456")
        assert exc_info.value.note_id == "note456"

    def test_404_other_endpoint_raises_generic_error(self) -> None:
        """Test that 404 on other endpoints raises generic DexAPIError."""
        response = httpx.Response(
            status_code=404,
            json={"error": "Not found"},
        )
        with pytest.raises(DexAPIError) as exc_info:
            handle_error_response(response, "/some/other/endpoint")
        assert exc_info.value.status_code == 404
        assert "Not found" in str(exc_info.value)

    def test_500_raises_generic_api_error(self) -> None:
        """Test that 500 status raises generic DexAPIError."""
        response = httpx.Response(
            status_code=500,
            json={"error": "Internal server error"},
        )
        with pytest.raises(DexAPIError) as exc_info:
            handle_error_response(response, "/contacts")
        assert exc_info.value.status_code == 500
        assert "Internal server error" in str(exc_info.value)

    def test_500_without_error_message_uses_default(self) -> None:
        """Test that 500 without error message uses default."""
        response = httpx.Response(
            status_code=500,
            json={},
        )
        with pytest.raises(DexAPIError) as exc_info:
            handle_error_response(response, "/contacts")
        assert "API error: 500" in str(exc_info.value)

    def test_handles_invalid_json_response(self) -> None:
        """Test that invalid JSON is handled gracefully."""
        response = httpx.Response(
            status_code=500,
            content=b"Not JSON",
        )
        with pytest.raises(DexAPIError) as exc_info:
            handle_error_response(response, "/contacts")
        assert exc_info.value.status_code == 500

    def test_response_data_included_in_exception(self) -> None:
        """Test that response data is included in exceptions."""
        response_data = {"error": "Custom error", "details": "More info"}
        response = httpx.Response(
            status_code=500,
            json=response_data,
        )
        with pytest.raises(DexAPIError) as exc_info:
            handle_error_response(response, "/contacts")
        assert exc_info.value.response_data == response_data
