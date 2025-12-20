"""Shared test helpers and utilities."""

from __future__ import annotations

import inspect
from contextlib import asynccontextmanager
from typing import AsyncIterator, Literal

from pytest_httpx import HTTPXMock

from src.dex_import import DexClient, Settings
from src.dex_import.async_client import AsyncDexClient

ClientKind = Literal["sync", "async"]


@asynccontextmanager
async def client_context(
    client_kind: ClientKind, settings: Settings
) -> AsyncIterator[DexClient | AsyncDexClient]:
    """Provide a client context manager based on kind."""
    if client_kind == "sync":
        with DexClient(settings) as client:
            yield client
    else:
        async with AsyncDexClient(settings) as client:
            yield client


async def maybe_await(value: object) -> object:
    """Await value if it is awaitable, otherwise return it."""
    if inspect.isawaitable(value):
        return await value
    return value


def build_url(settings: Settings, path: str, params: str | None = None) -> str:
    """Helper to build full API URLs."""
    if params:
        return f"{settings.dex_base_url}{path}?{params}"
    return f"{settings.dex_base_url}{path}"


def get_single_request(httpx_mock: HTTPXMock) -> object:
    """Assert and retrieve a single request from the mock."""
    requests = httpx_mock.get_requests()
    assert len(requests) == 1
    return requests[0]
