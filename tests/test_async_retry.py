"""Tests for async client retry logic."""

import pytest
from pytest_httpx import HTTPXMock

from src.dex_import import Settings
from src.dex_import.async_client import AsyncDexClient
from src.dex_import.exceptions import AuthenticationError, DexAPIError


class TestAsyncRetryLogic:
    """Test suite for async retry behavior."""

    @pytest.mark.asyncio
    async def test_retry_on_503(
        self, settings: Settings, httpx_mock: HTTPXMock
    ) -> None:
        """Test retry on 503 Service Unavailable."""
        httpx_mock.add_response(
            url="https://api.getdex.com/api/rest/contacts?limit=100&offset=0",
            status_code=503,
        )
        httpx_mock.add_response(
            url="https://api.getdex.com/api/rest/contacts?limit=100&offset=0",
            json={"contacts": [{"id": "1"}]},
        )

        async with AsyncDexClient(settings, max_retries=2, retry_delay=0.01) as client:
            contacts = await client.get_contacts()

        assert len(contacts) == 1

    @pytest.mark.asyncio
    async def test_retry_on_429(
        self, settings: Settings, httpx_mock: HTTPXMock
    ) -> None:
        """Test retry on 429 Too Many Requests."""
        httpx_mock.add_response(
            url="https://api.getdex.com/api/rest/contacts?limit=100&offset=0",
            status_code=429,
        )
        httpx_mock.add_response(
            url="https://api.getdex.com/api/rest/contacts?limit=100&offset=0",
            json={"contacts": [{"id": "2"}]},
        )

        async with AsyncDexClient(settings, max_retries=2, retry_delay=0.01) as client:
            contacts = await client.get_contacts()

        assert len(contacts) == 1

    @pytest.mark.asyncio
    async def test_max_retries_exceeded(
        self, settings: Settings, httpx_mock: HTTPXMock
    ) -> None:
        """Test that error is raised after max retries exceeded."""
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
            async with AsyncDexClient(
                settings, max_retries=2, retry_delay=0.01
            ) as client:
                await client.get_contacts()

    @pytest.mark.asyncio
    async def test_no_retry_on_401(
        self, settings: Settings, httpx_mock: HTTPXMock
    ) -> None:
        """Test that 401 errors are not retried."""
        httpx_mock.add_response(
            url="https://api.getdex.com/api/rest/contacts?limit=100&offset=0",
            status_code=401,
            json={"error": "Unauthorized"},
        )

        with pytest.raises(AuthenticationError):
            async with AsyncDexClient(
                settings, max_retries=3, retry_delay=0.01
            ) as client:
                await client.get_contacts()

    @pytest.mark.asyncio
    async def test_default_no_retries(
        self, settings: Settings, httpx_mock: HTTPXMock
    ) -> None:
        """Test that default client has no retries."""
        httpx_mock.add_response(
            url="https://api.getdex.com/api/rest/contacts?limit=100&offset=0",
            status_code=503,
        )

        with pytest.raises(DexAPIError):
            async with AsyncDexClient(settings) as client:
                await client.get_contacts()
