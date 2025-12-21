"""Pytest fixtures for Dex client tests."""

import sys
from pathlib import Path
from typing import Literal

import pytest

# Add scripts directory to path for tests that import from scripts
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

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
