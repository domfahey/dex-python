"""Tests for retry logic."""

import pytest
from pytest_httpx import HTTPXMock

from src.dex_import import DexClient, Settings
from src.dex_import.exceptions import DexAPIError


class TestRetryLogic:
    """Test suite for retry behavior."""

    def test_retry_on_503(self, settings: Settings, httpx_mock: HTTPXMock) -> None:
        """Test retry on 503 Service Unavailable."""
        # First request fails with 503, second succeeds
        httpx_mock.add_response(
            url="https://api.getdex.com/api/rest/contacts?limit=100&offset=0",
            status_code=503,
        )
        httpx_mock.add_response(
            url="https://api.getdex.com/api/rest/contacts?limit=100&offset=0",
            json={"contacts": [{"id": "1"}]},
        )

        with DexClient(settings, max_retries=2, retry_delay=0.01) as client:
            contacts = client.get_contacts()

        assert len(contacts) == 1

    def test_retry_on_500(self, settings: Settings, httpx_mock: HTTPXMock) -> None:
        """Test retry on 500 Internal Server Error."""
        httpx_mock.add_response(
            url="https://api.getdex.com/api/rest/contacts?limit=100&offset=0",
            status_code=500,
        )
        httpx_mock.add_response(
            url="https://api.getdex.com/api/rest/contacts?limit=100&offset=0",
            json={"contacts": []},
        )

        with DexClient(settings, max_retries=2, retry_delay=0.01) as client:
            contacts = client.get_contacts()

        assert contacts == []

    def test_retry_on_429(self, settings: Settings, httpx_mock: HTTPXMock) -> None:
        """Test retry on 429 Too Many Requests."""
        httpx_mock.add_response(
            url="https://api.getdex.com/api/rest/contacts?limit=100&offset=0",
            status_code=429,
        )
        httpx_mock.add_response(
            url="https://api.getdex.com/api/rest/contacts?limit=100&offset=0",
            json={"contacts": [{"id": "2"}]},
        )

        with DexClient(settings, max_retries=2, retry_delay=0.01) as client:
            contacts = client.get_contacts()

        assert len(contacts) == 1

    def test_max_retries_exceeded(
        self, settings: Settings, httpx_mock: HTTPXMock
    ) -> None:
        """Test that error is raised after max retries exceeded."""
        # All requests fail with 503
        httpx_mock.add_response(
            url="https://api.getdex.com/api/rest/contacts?limit=100&offset=0",
            status_code=503,
        )
        httpx_mock.add_response(
            url="https://api.getdex.com/api/rest/contacts?limit=100&offset=0",
            status_code=503,
        )
        httpx_mock.add_response(
            url="https://api.getdex.com/api/rest/contacts?limit=100&offset=0",
            status_code=503,
        )

        with pytest.raises(DexAPIError):
            with DexClient(settings, max_retries=2, retry_delay=0.01) as client:
                client.get_contacts()

    def test_no_retry_on_400(self, settings: Settings, httpx_mock: HTTPXMock) -> None:
        """Test that 400 errors are not retried."""
        httpx_mock.add_response(
            url="https://api.getdex.com/api/rest/contacts",
            method="POST",
            status_code=400,
            json={"error": "Bad request"},
        )

        from src.dex_import import ContactCreate
        from src.dex_import.exceptions import ValidationError

        with pytest.raises(ValidationError):
            with DexClient(settings, max_retries=3, retry_delay=0.01) as client:
                client.create_contact(ContactCreate(first_name="Test"))

    def test_no_retry_on_401(self, settings: Settings, httpx_mock: HTTPXMock) -> None:
        """Test that 401 errors are not retried."""
        httpx_mock.add_response(
            url="https://api.getdex.com/api/rest/contacts?limit=100&offset=0",
            status_code=401,
            json={"error": "Unauthorized"},
        )

        from src.dex_import.exceptions import AuthenticationError

        with pytest.raises(AuthenticationError):
            with DexClient(settings, max_retries=3, retry_delay=0.01) as client:
                client.get_contacts()

    def test_default_no_retries(
        self, settings: Settings, httpx_mock: HTTPXMock
    ) -> None:
        """Test that default client has no retries."""
        httpx_mock.add_response(
            url="https://api.getdex.com/api/rest/contacts?limit=100&offset=0",
            status_code=503,
        )

        with pytest.raises(DexAPIError):
            with DexClient(settings) as client:
                client.get_contacts()
