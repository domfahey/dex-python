"""Pytest fixtures for Dex client tests."""

import pytest

from src.dex_import import Settings


@pytest.fixture
def settings() -> Settings:
    """Create test settings."""
    return Settings(
        dex_api_key="test-api-key",
        dex_base_url="https://api.getdex.com/api/rest",
    )
