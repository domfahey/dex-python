"""Pytest fixtures for Dex client tests."""

from typing import Literal

import pytest

from dex_python import Settings

ClientKind = Literal["sync", "async"]


@pytest.fixture
def settings() -> Settings:
    """Create test settings."""
    return Settings(
        dex_api_key="test-api-key",
        dex_base_url="https://api.getdex.com/api/rest",
    )


@pytest.fixture(params=["sync", "async"])
def client_kind(request: pytest.FixtureRequest) -> ClientKind:
    """Parametrize tests for both sync and async clients."""
    return request.param  # type: ignore[no-any-return]
