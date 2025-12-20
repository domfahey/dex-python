"""Contract tests for sync and async Dex clients."""

from __future__ import annotations

import inspect
import json
from contextlib import asynccontextmanager
from typing import AsyncIterator, Literal

import pytest
from pytest_httpx import HTTPXMock

from src.dex_import import (
    ContactCreate,
    ContactUpdate,
    DexClient,
    NoteUpdate,
    ReminderUpdate,
    Settings,
)
from src.dex_import.async_client import AsyncDexClient
from src.dex_import.exceptions import (
    AuthenticationError,
    ContactNotFoundError,
    DexAPIError,
    RateLimitError,
    ValidationError,
)

ClientKind = Literal["sync", "async"]

pytestmark = pytest.mark.asyncio


@pytest.fixture(params=["sync", "async"])
def client_kind(request: pytest.FixtureRequest) -> ClientKind:
    return request.param


@asynccontextmanager
async def client_context(
    client_kind: ClientKind, settings: Settings
) -> AsyncIterator[DexClient | AsyncDexClient]:
    if client_kind == "sync":
        with DexClient(settings) as client:
            yield client
    else:
        async with AsyncDexClient(settings) as client:
            yield client


async def maybe_await(value: object) -> object:
    if inspect.isawaitable(value):
        return await value
    return value


def build_url(settings: Settings, path: str, params: str | None = None) -> str:
    if params:
        return f"{settings.dex_base_url}{path}?{params}"
    return f"{settings.dex_base_url}{path}"


def get_single_request(httpx_mock: HTTPXMock) -> object:
    requests = httpx_mock.get_requests()
    assert len(requests) == 1
    return requests[0]


async def test_client_uses_correct_headers(
    client_kind: ClientKind, settings: Settings
) -> None:
    async with client_context(client_kind, settings) as client:
        headers = client._client.headers
        assert headers["content-type"] == "application/json"
        assert headers["x-hasura-dex-api-key"] == "test-api-key"


async def test_get_contacts(
    client_kind: ClientKind, settings: Settings, httpx_mock: HTTPXMock
) -> None:
    mock_response = {
        "contacts": [
            {"id": "1", "first_name": "John", "last_name": "Doe"},
            {"id": "2", "first_name": "Jane", "last_name": "Smith"},
        ],
        "pagination": {"total": {"count": 2}},
    }
    httpx_mock.add_response(
        url=build_url(settings, "/contacts", "limit=100&offset=0"),
        json=mock_response,
    )

    async with client_context(client_kind, settings) as client:
        contacts = await maybe_await(client.get_contacts())

    assert len(contacts) == 2
    assert contacts[0]["first_name"] == "John"


async def test_get_contact_by_id(
    client_kind: ClientKind, settings: Settings, httpx_mock: HTTPXMock
) -> None:
    mock_response = {
        "contacts": [
            {
                "id": "123",
                "first_name": "John",
                "emails": [{"email": "john@example.com"}],
            }
        ]
    }
    httpx_mock.add_response(
        url=build_url(settings, "/contacts/123"),
        json=mock_response,
    )

    async with client_context(client_kind, settings) as client:
        contact = await maybe_await(client.get_contact("123"))

    assert contact["id"] == "123"
    assert contact["emails"][0]["email"] == "john@example.com"


async def test_get_contact_by_email(
    client_kind: ClientKind, settings: Settings, httpx_mock: HTTPXMock
) -> None:
    mock_response = {
        "search_contacts_by_exact_email": [
            {
                "id": "456",
                "first_name": "Jane",
                "emails": [{"email": "jane@example.com"}],
            }
        ]
    }
    httpx_mock.add_response(
        url=build_url(settings, "/search/contacts", "email=jane%40example.com"),
        json=mock_response,
    )

    async with client_context(client_kind, settings) as client:
        contact = await maybe_await(client.get_contact_by_email("jane@example.com"))

    assert contact is not None
    assert contact["id"] == "456"


async def test_create_contact_sends_expected_body(
    client_kind: ClientKind, settings: Settings, httpx_mock: HTTPXMock
) -> None:
    new_contact = ContactCreate(first_name="Alice", last_name="Wonder")
    mock_response = {
        "insert_contacts_one": {
            "id": "789",
            "first_name": "Alice",
            "last_name": "Wonder",
        }
    }
    httpx_mock.add_response(
        url=build_url(settings, "/contacts"),
        method="POST",
        json=mock_response,
    )

    async with client_context(client_kind, settings) as client:
        result = await maybe_await(client.create_contact(new_contact))

    request = get_single_request(httpx_mock)
    assert request.method == "POST"
    assert str(request.url) == build_url(settings, "/contacts")
    assert json.loads(request.content) == {
        "contact": new_contact.model_dump(exclude_none=True)
    }
    assert result["id"] == "789"


async def test_update_contact_sends_expected_body(
    client_kind: ClientKind, settings: Settings, httpx_mock: HTTPXMock
) -> None:
    update = ContactUpdate(contact_id="contact-123", changes={"first_name": "New"})
    mock_response = {"update_contacts_by_pk": {"id": "contact-123"}}
    httpx_mock.add_response(
        url=build_url(settings, "/contacts/contact-123"),
        method="PUT",
        json=mock_response,
    )

    async with client_context(client_kind, settings) as client:
        result = await maybe_await(client.update_contact(update))

    request = get_single_request(httpx_mock)
    assert request.method == "PUT"
    assert str(request.url) == build_url(settings, "/contacts/contact-123")
    assert json.loads(request.content) == update.model_dump(
        exclude_none=True, by_alias=True
    )
    assert result["id"] == "contact-123"


async def test_update_reminder_sends_expected_body(
    client_kind: ClientKind, settings: Settings, httpx_mock: HTTPXMock
) -> None:
    update = ReminderUpdate(
        reminder_id="reminder-123",
        changes={"text": "Updated text", "is_complete": True},
    )
    mock_response = {"update_reminders_by_pk": {"id": "reminder-123"}}
    httpx_mock.add_response(
        url=build_url(settings, "/reminders/reminder-123"),
        method="PUT",
        json=mock_response,
    )

    async with client_context(client_kind, settings) as client:
        result = await maybe_await(client.update_reminder(update))

    request = get_single_request(httpx_mock)
    assert request.method == "PUT"
    assert str(request.url) == build_url(settings, "/reminders/reminder-123")
    assert json.loads(request.content) == update.model_dump(exclude_none=True)
    assert result["id"] == "reminder-123"


async def test_update_note_sends_expected_body(
    client_kind: ClientKind, settings: Settings, httpx_mock: HTTPXMock
) -> None:
    update = NoteUpdate(note_id="note-456", changes={"note": "Updated note"})
    mock_response = {"update_timeline_items_by_pk": {"id": "note-456"}}
    httpx_mock.add_response(
        url=build_url(settings, "/timeline_items/note-456"),
        method="PUT",
        json=mock_response,
    )

    async with client_context(client_kind, settings) as client:
        result = await maybe_await(client.update_note(update))

    request = get_single_request(httpx_mock)
    assert request.method == "PUT"
    assert str(request.url) == build_url(settings, "/timeline_items/note-456")
    assert json.loads(request.content) == update.model_dump(exclude_none=True)
    assert result["id"] == "note-456"


async def test_delete_contact(
    client_kind: ClientKind, settings: Settings, httpx_mock: HTTPXMock
) -> None:
    httpx_mock.add_response(
        url=build_url(settings, "/contacts/123"),
        method="DELETE",
        json={"delete_contacts_by_pk": {"id": "123"}},
    )

    async with client_context(client_kind, settings) as client:
        result = await maybe_await(client.delete_contact("123"))

    request = get_single_request(httpx_mock)
    assert request.method == "DELETE"
    assert str(request.url) == build_url(settings, "/contacts/123")
    assert result["id"] == "123"


async def test_context_manager_closes_client(
    client_kind: ClientKind, settings: Settings
) -> None:
    client_ref: DexClient | AsyncDexClient
    async with client_context(client_kind, settings) as client:
        client_ref = client
    assert client_ref._client.is_closed


async def test_401_raises_authentication_error(
    client_kind: ClientKind, settings: Settings, httpx_mock: HTTPXMock
) -> None:
    httpx_mock.add_response(
        url=build_url(settings, "/contacts", "limit=100&offset=0"),
        status_code=401,
        json={"error": "Invalid API key"},
    )

    async with client_context(client_kind, settings) as client:
        with pytest.raises(AuthenticationError):
            await maybe_await(client.get_contacts())


async def test_404_raises_contact_not_found(
    client_kind: ClientKind, settings: Settings, httpx_mock: HTTPXMock
) -> None:
    httpx_mock.add_response(
        url=build_url(settings, "/contacts/invalid-id"),
        status_code=404,
        json={"error": "Contact not found"},
    )

    async with client_context(client_kind, settings) as client:
        with pytest.raises(ContactNotFoundError):
            await maybe_await(client.get_contact("invalid-id"))


@pytest.mark.parametrize(
    "status_code, error_json, expected_exception",
    [
        (429, {"error": "Rate limit exceeded"}, RateLimitError),
        (500, {"error": "Internal server error"}, DexAPIError),
    ],
)
async def test_get_contacts_error_mapping(
    client_kind: ClientKind,
    settings: Settings,
    httpx_mock: HTTPXMock,
    status_code: int,
    error_json: dict[str, str],
    expected_exception: type[Exception],
) -> None:
    httpx_mock.add_response(
        url=build_url(settings, "/contacts", "limit=100&offset=0"),
        status_code=status_code,
        json=error_json,
    )

    async with client_context(client_kind, settings) as client:
        with pytest.raises(expected_exception):
            await maybe_await(client.get_contacts())


async def test_400_raises_validation_error(
    client_kind: ClientKind, settings: Settings, httpx_mock: HTTPXMock
) -> None:
    httpx_mock.add_response(
        url=build_url(settings, "/contacts"),
        method="POST",
        status_code=400,
        json={"error": "Invalid request body"},
    )

    async with client_context(client_kind, settings) as client:
        with pytest.raises(ValidationError):
            await maybe_await(client.create_contact(ContactCreate(first_name="Test")))
