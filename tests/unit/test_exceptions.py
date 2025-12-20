"""Tests for custom exceptions."""

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

