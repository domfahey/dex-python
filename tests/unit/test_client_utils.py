"""Tests for client_utils module."""

import pytest
from httpx import Response

from dex_python.client_utils import handle_error, should_retry
from dex_python.exceptions import (
    AuthenticationError,
    ContactNotFoundError,
    DexAPIError,
    NoteNotFoundError,
    RateLimitError,
    ReminderNotFoundError,
    ValidationError,
)


class TestShouldRetry:
    """Test should_retry function."""

    def test_retries_429(self) -> None:
        """Should retry rate limit errors."""
        assert should_retry(429) is True

    def test_retries_500(self) -> None:
        """Should retry server errors."""
        assert should_retry(500) is True

    def test_retries_502(self) -> None:
        """Should retry bad gateway."""
        assert should_retry(502) is True

    def test_retries_503(self) -> None:
        """Should retry service unavailable."""
        assert should_retry(503) is True

    def test_retries_504(self) -> None:
        """Should retry gateway timeout."""
        assert should_retry(504) is True

    def test_no_retry_400(self) -> None:
        """Should not retry client errors."""
        assert should_retry(400) is False

    def test_no_retry_401(self) -> None:
        """Should not retry auth errors."""
        assert should_retry(401) is False

    def test_no_retry_404(self) -> None:
        """Should not retry not found."""
        assert should_retry(404) is False


class TestHandleError:
    """Test handle_error function."""

    def test_401_raises_authentication_error(self) -> None:
        """Should raise AuthenticationError for 401."""
        response = Response(401, json={"error": "Unauthorized"})
        with pytest.raises(AuthenticationError, match="Invalid API key"):
            handle_error(response, "/contacts")

    def test_429_raises_rate_limit_error(self) -> None:
        """Should raise RateLimitError for 429."""
        response = Response(429, json={"error": "Too many requests"})
        with pytest.raises(RateLimitError, match="Rate limit exceeded"):
            handle_error(response, "/contacts")

    def test_429_includes_retry_after(self) -> None:
        """Should include retry_after from header."""
        response = Response(
            429, headers={"Retry-After": "60"}, json={"error": "Too many requests"}
        )
        with pytest.raises(RateLimitError) as exc_info:
            handle_error(response, "/contacts")
        assert exc_info.value.retry_after == 60

    def test_400_raises_validation_error(self) -> None:
        """Should raise ValidationError for 400."""
        response = Response(400, json={"error": "Invalid input"})
        with pytest.raises(ValidationError, match="Invalid input"):
            handle_error(response, "/contacts")

    def test_404_contacts_raises_contact_not_found(self) -> None:
        """Should raise ContactNotFoundError for 404 on /contacts."""
        response = Response(404, json={"error": "Not found"})
        with pytest.raises(ContactNotFoundError) as exc_info:
            handle_error(response, "/contacts/abc123")
        assert exc_info.value.contact_id == "abc123"

    def test_404_reminders_raises_reminder_not_found(self) -> None:
        """Should raise ReminderNotFoundError for 404 on /reminders."""
        response = Response(404, json={"error": "Not found"})
        with pytest.raises(ReminderNotFoundError) as exc_info:
            handle_error(response, "/reminders/xyz789")
        assert exc_info.value.reminder_id == "xyz789"

    def test_404_notes_raises_note_not_found(self) -> None:
        """Should raise NoteNotFoundError for 404 on /timeline_items."""
        response = Response(404, json={"error": "Not found"})
        with pytest.raises(NoteNotFoundError) as exc_info:
            handle_error(response, "/timeline_items/note123")
        assert exc_info.value.note_id == "note123"

    def test_404_other_raises_dex_api_error(self) -> None:
        """Should raise DexAPIError for 404 on other endpoints."""
        response = Response(404, json={"error": "Not found"})
        with pytest.raises(DexAPIError, match="Not found"):
            handle_error(response, "/other")

    def test_500_raises_dex_api_error(self) -> None:
        """Should raise DexAPIError for 500."""
        response = Response(500, json={"error": "Server error"})
        with pytest.raises(DexAPIError, match="Server error"):
            handle_error(response, "/contacts")

    def test_handles_non_json_response(self) -> None:
        """Should handle responses without JSON."""
        response = Response(500, text="Server error")
        with pytest.raises(DexAPIError):
            handle_error(response, "/contacts")
