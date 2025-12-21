"""Tests for retry logic."""

import pytest
from pytest_httpx import HTTPXMock

from dex_python import DexClient, Settings
from dex_python.exceptions import DexAPIError


def capture_sleep(monkeypatch: pytest.MonkeyPatch) -> list[float]:
    delays: list[float] = []

    def fake_sleep(delay: float) -> None:
        delays.append(delay)

    monkeypatch.setattr("dex_python.client.time.sleep", fake_sleep)
    return delays


class TestRetryLogic:
    """Test suite for retry behavior."""

    def test_retry_on_503(
        self, settings: Settings, httpx_mock: HTTPXMock, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test retry on 503 Service Unavailable."""
        delays = capture_sleep(monkeypatch)
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
        assert delays == [0.01]
        assert len(httpx_mock.get_requests()) == 2

    def test_retry_on_500(
        self, settings: Settings, httpx_mock: HTTPXMock, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test retry on 500 Internal Server Error."""
        delays = capture_sleep(monkeypatch)
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
        assert delays == [0.01]
        assert len(httpx_mock.get_requests()) == 2

    def test_retry_on_429(
        self, settings: Settings, httpx_mock: HTTPXMock, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test retry on 429 Too Many Requests."""
        delays = capture_sleep(monkeypatch)
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
        assert delays == [0.01]
        assert len(httpx_mock.get_requests()) == 2

    def test_max_retries_exceeded(
        self, settings: Settings, httpx_mock: HTTPXMock, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that error is raised after max retries exceeded."""
        delays = capture_sleep(monkeypatch)
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

        assert delays == [0.01, 0.02]
        assert len(httpx_mock.get_requests()) == 3

    def test_no_retry_on_400(
        self, settings: Settings, httpx_mock: HTTPXMock, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that 400 errors are not retried."""
        delays = capture_sleep(monkeypatch)
        httpx_mock.add_response(
            url="https://api.getdex.com/api/rest/contacts",
            method="POST",
            status_code=400,
            json={"error": "Bad request"},
        )

        from dex_python import ContactCreate
        from dex_python.exceptions import ValidationError

        with pytest.raises(ValidationError):
            with DexClient(settings, max_retries=3, retry_delay=0.01) as client:
                client.create_contact(ContactCreate(first_name="Test"))

        assert delays == []
        assert len(httpx_mock.get_requests()) == 1

    def test_no_retry_on_401(
        self, settings: Settings, httpx_mock: HTTPXMock, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that 401 errors are not retried."""
        delays = capture_sleep(monkeypatch)
        httpx_mock.add_response(
            url="https://api.getdex.com/api/rest/contacts?limit=100&offset=0",
            status_code=401,
            json={"error": "Unauthorized"},
        )

        from dex_python.exceptions import AuthenticationError

        with pytest.raises(AuthenticationError):
            with DexClient(settings, max_retries=3, retry_delay=0.01) as client:
                client.get_contacts()

        assert delays == []
        assert len(httpx_mock.get_requests()) == 1

    def test_default_no_retries(
        self, settings: Settings, httpx_mock: HTTPXMock, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that default client has no retries."""
        delays = capture_sleep(monkeypatch)
        httpx_mock.add_response(
            url="https://api.getdex.com/api/rest/contacts?limit=100&offset=0",
            status_code=503,
        )

        with pytest.raises(DexAPIError):
            with DexClient(settings) as client:
                client.get_contacts()

        assert delays == []
        assert len(httpx_mock.get_requests()) == 1
