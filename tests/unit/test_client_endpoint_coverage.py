"""Contract tests for newly implemented endpoint surface."""

from __future__ import annotations

import json

import pytest
from pytest_httpx import HTTPXMock

from dex_python import Settings
from tests.helpers import (
    ClientKind,
    build_url,
    client_context,
    get_single_request,
    maybe_await,
)

pytestmark = pytest.mark.asyncio


async def test_update_contacts_bulk_calls_bulk_contacts_endpoint(
    client_kind: ClientKind, settings: Settings, httpx_mock: HTTPXMock
) -> None:
    payload = {"where": {"id": {"_in": ["c1", "c2"]}}}
    mock_response = {"data": [{"id": "c1"}, {"id": "c2"}]}
    httpx_mock.add_response(
        url=build_url(settings, "/contacts"),
        method="PUT",
        json=mock_response,
    )

    async with client_context(client_kind, settings) as client:
        result = await maybe_await(client.update_contacts_bulk(payload))

    request = get_single_request(httpx_mock)
    assert request.method == "PUT"
    assert str(request.url) == build_url(settings, "/contacts")
    assert json.loads(request.content) == payload
    assert result == mock_response


async def test_delete_contacts_bulk_calls_bulk_contacts_endpoint(
    client_kind: ClientKind, settings: Settings, httpx_mock: HTTPXMock
) -> None:
    payload = {"where": {"id": {"_in": ["c1"]}}}
    mock_response = {"data": [{"id": "c1"}]}
    httpx_mock.add_response(
        url=build_url(settings, "/contacts"),
        method="DELETE",
        json=mock_response,
    )

    async with client_context(client_kind, settings) as client:
        result = await maybe_await(client.delete_contacts_bulk(payload))

    request = get_single_request(httpx_mock)
    assert request.method == "DELETE"
    assert str(request.url) == build_url(settings, "/contacts")
    assert json.loads(request.content) == payload
    assert result == mock_response


async def test_count_contacts_returns_count(
    client_kind: ClientKind, settings: Settings, httpx_mock: HTTPXMock
) -> None:
    httpx_mock.add_response(
        url=build_url(settings, "/contacts/count"), json={"count": 12}
    )

    async with client_context(client_kind, settings) as client:
        total = await maybe_await(client.count_contacts())

    request = get_single_request(httpx_mock)
    assert request.method == "GET"
    assert str(request.url) == build_url(settings, "/contacts/count")
    assert total == 12


async def test_search_contacts_calls_endpoint(
    client_kind: ClientKind, settings: Settings, httpx_mock: HTTPXMock
) -> None:
    mock_response = {"contacts": [{"id": "c1", "first_name": "Acme"}]}
    httpx_mock.add_response(
        url=build_url(settings, "/contacts/search", "query=acme"),
        json=mock_response,
    )

    async with client_context(client_kind, settings) as client:
        result = await maybe_await(client.search_contacts({"query": "acme"}))

    request = get_single_request(httpx_mock)
    assert request.method == "GET"
    assert str(request.url) == build_url(settings, "/contacts/search", "query=acme")
    assert result == mock_response["contacts"]


async def test_filter_contacts_calls_endpoint(
    client_kind: ClientKind, settings: Settings, httpx_mock: HTTPXMock
) -> None:
    payload = {"where": {"first_name": {"_eq": "Alice"}}}
    mock_response = {"contacts": [{"id": "c2", "first_name": "Alice"}]}
    httpx_mock.add_response(
        url=build_url(settings, "/contacts/filter"),
        method="POST",
        json=mock_response,
    )

    async with client_context(client_kind, settings) as client:
        result = await maybe_await(client.filter_contacts(payload))

    request = get_single_request(httpx_mock)
    assert request.method == "POST"
    assert str(request.url) == build_url(settings, "/contacts/filter")
    assert json.loads(request.content) == payload
    assert result == mock_response["contacts"]


async def test_find_contacts_by_emails_converts_list_body(
    client_kind: ClientKind, settings: Settings, httpx_mock: HTTPXMock
) -> None:
    emails = ["a@example.com", "b@example.com"]
    mock_response = {"contacts": [{"id": "c3"}]}
    httpx_mock.add_response(
        url=build_url(settings, "/contacts/by-emails"),
        method="POST",
        json=mock_response,
    )

    async with client_context(client_kind, settings) as client:
        result = await maybe_await(client.find_contacts_by_emails(emails))

    request = get_single_request(httpx_mock)
    assert request.method == "POST"
    assert str(request.url) == build_url(settings, "/contacts/by-emails")
    assert json.loads(request.content) == {"emails": emails}
    assert result == mock_response["contacts"]


async def test_merge_contacts_calls_endpoint(
    client_kind: ClientKind, settings: Settings, httpx_mock: HTTPXMock
) -> None:
    payload = {"target_contact_id": "c-main", "source_contact_ids": ["c-old"]}
    mock_response = {"merged_contact_id": "c-main"}
    httpx_mock.add_response(
        url=build_url(settings, "/contacts/merge"),
        method="POST",
        json=mock_response,
    )

    async with client_context(client_kind, settings) as client:
        result = await maybe_await(client.merge_contacts(payload))

    request = get_single_request(httpx_mock)
    assert request.method == "POST"
    assert str(request.url) == build_url(settings, "/contacts/merge")
    assert json.loads(request.content) == payload
    assert result == mock_response


async def test_get_reminder_by_id(
    client_kind: ClientKind, settings: Settings, httpx_mock: HTTPXMock
) -> None:
    mock_response = {"reminders": [{"id": "r1", "text": "follow up"}]}
    httpx_mock.add_response(
        url=build_url(settings, "/reminders/r1"), json=mock_response
    )

    async with client_context(client_kind, settings) as client:
        result = await maybe_await(client.get_reminder("r1"))

    request = get_single_request(httpx_mock)
    assert request.method == "GET"
    assert str(request.url) == build_url(settings, "/reminders/r1")
    assert result == mock_response["reminders"][0]


async def test_get_recurring_reminders(
    client_kind: ClientKind, settings: Settings, httpx_mock: HTTPXMock
) -> None:
    mock_response = {"reminders": [{"id": "r-recurring"}]}
    httpx_mock.add_response(
        url=build_url(settings, "/reminders/recurring"), json=mock_response
    )

    async with client_context(client_kind, settings) as client:
        result = await maybe_await(client.get_recurring_reminders())

    request = get_single_request(httpx_mock)
    assert request.method == "GET"
    assert str(request.url) == build_url(settings, "/reminders/recurring")
    assert result == mock_response["reminders"]


async def test_get_timeline_calls_timeline_endpoint(
    client_kind: ClientKind, settings: Settings, httpx_mock: HTTPXMock
) -> None:
    mock_response = {"timeline": [{"id": "n1"}]}
    httpx_mock.add_response(
        url=build_url(settings, "/timeline", "limit=100&offset=0"),
        json=mock_response,
    )

    async with client_context(client_kind, settings) as client:
        result = await maybe_await(client.get_timeline())

    request = get_single_request(httpx_mock)
    assert request.method == "GET"
    assert str(request.url) == build_url(settings, "/timeline", "limit=100&offset=0")
    assert result == mock_response["timeline"]


async def test_get_timeline_note_calls_timeline_item_endpoint(
    client_kind: ClientKind, settings: Settings, httpx_mock: HTTPXMock
) -> None:
    mock_response = {"timeline_item": {"id": "note-1", "note": "updated"}}
    httpx_mock.add_response(
        url=build_url(settings, "/timeline/note-1"),
        json=mock_response,
    )

    async with client_context(client_kind, settings) as client:
        result = await maybe_await(client.get_timeline_note("note-1"))

    request = get_single_request(httpx_mock)
    assert request.method == "GET"
    assert str(request.url) == build_url(settings, "/timeline/note-1")
    assert result == mock_response["timeline_item"]


async def test_count_timeline(
    client_kind: ClientKind, settings: Settings, httpx_mock: HTTPXMock
) -> None:
    mock_response = {"count": 9}
    httpx_mock.add_response(
        url=build_url(settings, "/timeline/count"), json=mock_response
    )

    async with client_context(client_kind, settings) as client:
        total = await maybe_await(client.count_timeline())

    request = get_single_request(httpx_mock)
    assert request.method == "GET"
    assert str(request.url) == build_url(settings, "/timeline/count")
    assert total == 9


async def test_get_timeline_note_types(
    client_kind: ClientKind, settings: Settings, httpx_mock: HTTPXMock
) -> None:
    mock_response = {"note_types": ["note", "call"]}
    httpx_mock.add_response(
        url=build_url(settings, "/timeline/note-types"),
        json=mock_response,
    )

    async with client_context(client_kind, settings) as client:
        result = await maybe_await(client.get_timeline_note_types())

    request = get_single_request(httpx_mock)
    assert request.method == "GET"
    assert str(request.url) == build_url(settings, "/timeline/note-types")
    assert result == mock_response["note_types"]


async def test_groups_list_and_detail(
    client_kind: ClientKind, settings: Settings, httpx_mock: HTTPXMock
) -> None:
    httpx_mock.add_response(
        url=build_url(settings, "/groups"),
        json={"groups": [{"id": "g1", "name": "Sales"}]},
    )
    httpx_mock.add_response(
        url=build_url(settings, "/groups/g1"),
        json={"id": "g1", "name": "Sales"},
    )

    async with client_context(client_kind, settings) as client:
        groups = await maybe_await(client.get_groups())
        group = await maybe_await(client.get_group("g1"))

    requests = httpx_mock.get_requests()
    assert len(requests) == 2
    request_list = requests[0]
    request_get = requests[1]
    assert request_list.method == "GET"
    assert str(request_list.url) == build_url(settings, "/groups")
    assert groups == [{"id": "g1", "name": "Sales"}]

    assert request_get.method == "GET"
    assert str(request_get.url) == build_url(settings, "/groups/g1")
    assert group["id"] == "g1"


async def test_create_group(
    client_kind: ClientKind, settings: Settings, httpx_mock: HTTPXMock
) -> None:
    payload = {"name": "VIP"}
    mock_response = {"id": "g2", "name": "VIP"}
    httpx_mock.add_response(
        url=build_url(settings, "/groups"),
        method="POST",
        json=mock_response,
    )

    async with client_context(client_kind, settings) as client:
        result = await maybe_await(client.create_group(payload))

    request = get_single_request(httpx_mock)
    assert request.method == "POST"
    assert str(request.url) == build_url(settings, "/groups")
    assert json.loads(request.content) == payload
    assert result == mock_response


async def test_update_group(
    client_kind: ClientKind, settings: Settings, httpx_mock: HTTPXMock
) -> None:
    payload = {"name": "VIP Updated"}
    mock_response = {"id": "g1", "name": "VIP Updated"}
    httpx_mock.add_response(
        url=build_url(settings, "/groups/g1"),
        method="PUT",
        json=mock_response,
    )

    async with client_context(client_kind, settings) as client:
        result = await maybe_await(client.update_group("g1", payload))

    request = get_single_request(httpx_mock)
    assert request.method == "PUT"
    assert str(request.url) == build_url(settings, "/groups/g1")
    assert json.loads(request.content) == payload
    assert result == mock_response


async def test_delete_group(
    client_kind: ClientKind, settings: Settings, httpx_mock: HTTPXMock
) -> None:
    mock_response = {"id": "g1", "deleted": True}
    httpx_mock.add_response(
        url=build_url(settings, "/groups/g1"),
        method="DELETE",
        json=mock_response,
    )

    async with client_context(client_kind, settings) as client:
        result = await maybe_await(client.delete_group("g1"))

    request = get_single_request(httpx_mock)
    assert request.method == "DELETE"
    assert str(request.url) == build_url(settings, "/groups/g1")
    assert result == mock_response


async def test_count_groups(
    client_kind: ClientKind, settings: Settings, httpx_mock: HTTPXMock
) -> None:
    httpx_mock.add_response(url=build_url(settings, "/groups/count"), json={"count": 7})

    async with client_context(client_kind, settings) as client:
        total = await maybe_await(client.count_groups())

    request = get_single_request(httpx_mock)
    assert request.method == "GET"
    assert str(request.url) == build_url(settings, "/groups/count")
    assert total == 7


async def test_group_contacts_endpoints(
    client_kind: ClientKind, settings: Settings, httpx_mock: HTTPXMock
) -> None:
    get_response = {"contacts": [{"id": "c1"}, {"id": "c2"}]}
    add_payload = {"contact_ids": ["c3"]}
    remove_payload = {"contact_ids": ["c1"]}

    httpx_mock.add_response(
        url=build_url(settings, "/groups/g1/contacts"),
        json=get_response,
    )
    httpx_mock.add_response(
        url=build_url(settings, "/groups/g1/contacts"),
        method="PUT",
        json={"updated": True},
    )
    httpx_mock.add_response(
        url=build_url(settings, "/groups/g1/contacts"),
        method="POST",
        json={"removed": True},
    )

    async with client_context(client_kind, settings) as client:
        contacts = await maybe_await(client.get_group_contacts("g1"))
        add_result = await maybe_await(client.add_group_contacts("g1", add_payload))
        remove_result = await maybe_await(
            client.remove_group_contacts("g1", remove_payload)
        )

    requests = httpx_mock.get_requests()
    assert len(requests) == 3
    request_get = requests[0]
    assert request_get.method == "GET"
    assert str(request_get.url) == build_url(settings, "/groups/g1/contacts")

    request_put = requests[1]
    assert request_put.method == "PUT"
    assert str(request_put.url) == build_url(settings, "/groups/g1/contacts")
    assert json.loads(request_put.content) == add_payload

    request_post = requests[2]
    assert request_post.method == "POST"
    assert str(request_post.url) == build_url(settings, "/groups/g1/contacts")
    assert json.loads(request_post.content) == remove_payload

    assert contacts == get_response["contacts"]
    assert add_result == {"updated": True}
    assert remove_result == {"removed": True}


async def test_group_contact_counts(
    client_kind: ClientKind, settings: Settings, httpx_mock: HTTPXMock
) -> None:
    mock_response = {"counts": [{"group_id": "g1", "contact_count": 3}]}
    httpx_mock.add_response(
        url=build_url(settings, "/groups/contact-counts"),
        json=mock_response,
    )

    async with client_context(client_kind, settings) as client:
        result = await maybe_await(client.get_group_contact_counts())

    request = get_single_request(httpx_mock)
    assert request.method == "GET"
    assert str(request.url) == build_url(settings, "/groups/contact-counts")
    assert result == mock_response["counts"]


async def test_create_custom_field(
    client_kind: ClientKind, settings: Settings, httpx_mock: HTTPXMock
) -> None:
    payload = {"name": "Industry", "field_type": "text"}
    mock_response = {"id": "cf-1", "name": "Industry"}
    httpx_mock.add_response(
        url=build_url(settings, "/custom-fields"),
        method="POST",
        json=mock_response,
    )

    async with client_context(client_kind, settings) as client:
        result = await maybe_await(client.create_custom_field(payload))

    request = get_single_request(httpx_mock)
    assert request.method == "POST"
    assert str(request.url) == build_url(settings, "/custom-fields")
    assert json.loads(request.content) == payload
    assert result == mock_response


async def test_update_custom_field(
    client_kind: ClientKind, settings: Settings, httpx_mock: HTTPXMock
) -> None:
    payload = {"name": "Industry", "field_type": "select"}
    mock_response = {"id": "cf-1", "name": "Industry", "updated": True}
    httpx_mock.add_response(
        url=build_url(settings, "/custom-fields/cf-1"),
        method="PUT",
        json=mock_response,
    )

    async with client_context(client_kind, settings) as client:
        result = await maybe_await(client.update_custom_field("cf-1", payload))

    request = get_single_request(httpx_mock)
    assert request.method == "PUT"
    assert str(request.url) == build_url(settings, "/custom-fields/cf-1")
    assert json.loads(request.content) == payload
    assert result == mock_response


async def test_delete_custom_field(
    client_kind: ClientKind, settings: Settings, httpx_mock: HTTPXMock
) -> None:
    mock_response = {"id": "cf-1", "deleted": True}
    httpx_mock.add_response(
        url=build_url(settings, "/custom-fields/cf-1"),
        method="DELETE",
        json=mock_response,
    )

    async with client_context(client_kind, settings) as client:
        result = await maybe_await(client.delete_custom_field("cf-1"))

    request = get_single_request(httpx_mock)
    assert request.method == "DELETE"
    assert str(request.url) == build_url(settings, "/custom-fields/cf-1")
    assert result == mock_response


async def test_reorder_custom_fields(
    client_kind: ClientKind, settings: Settings, httpx_mock: HTTPXMock
) -> None:
    payload = {"custom_fields": ["cf-1", "cf-2"]}
    mock_response = {"status": "ok"}
    httpx_mock.add_response(
        url=build_url(settings, "/custom-fields/reorder"),
        method="PUT",
        json=mock_response,
    )

    async with client_context(client_kind, settings) as client:
        result = await maybe_await(client.reorder_custom_fields(payload))

    request = get_single_request(httpx_mock)
    assert request.method == "PUT"
    assert str(request.url) == build_url(settings, "/custom-fields/reorder")
    assert json.loads(request.content) == payload
    assert result == mock_response


async def test_batch_update_custom_fields_contacts(
    client_kind: ClientKind, settings: Settings, httpx_mock: HTTPXMock
) -> None:
    payload = {
        "updates": [{"contact_id": "c1", "custom_field_id": "cf-1", "value": "A"}]
    }
    mock_response = {"updated": 1}
    httpx_mock.add_response(
        url=build_url(settings, "/custom-fields/batch-update-contacts"),
        method="POST",
        json=mock_response,
    )

    async with client_context(client_kind, settings) as client:
        result = await maybe_await(client.batch_update_custom_fields_contacts(payload))

    request = get_single_request(httpx_mock)
    assert request.method == "POST"
    assert str(request.url) == build_url(
        settings, "/custom-fields/batch-update-contacts"
    )
    assert json.loads(request.content) == payload
    assert result == mock_response


async def test_search_groups(
    client_kind: ClientKind, settings: Settings, httpx_mock: HTTPXMock
) -> None:
    mock_response = {"groups": [{"id": "g1"}]}
    httpx_mock.add_response(
        url=build_url(settings, "/search/groups", "query=sales"),
        json=mock_response,
    )

    async with client_context(client_kind, settings) as client:
        groups = await maybe_await(client.search_groups({"query": "sales"}))

    request = get_single_request(httpx_mock)
    assert request.method == "GET"
    assert str(request.url) == build_url(settings, "/search/groups", "query=sales")
    assert groups == mock_response["groups"]


async def test_search_timeline(
    client_kind: ClientKind, settings: Settings, httpx_mock: HTTPXMock
) -> None:
    mock_response = {"timeline": [{"id": "n1"}]}
    httpx_mock.add_response(
        url=build_url(settings, "/search/timeline", "query=meeting"),
        json=mock_response,
    )

    async with client_context(client_kind, settings) as client:
        entries = await maybe_await(client.search_timeline({"query": "meeting"}))

    request = get_single_request(httpx_mock)
    assert request.method == "GET"
    assert str(request.url) == build_url(settings, "/search/timeline", "query=meeting")
    assert entries == mock_response["timeline"]


async def test_search_reminders(
    client_kind: ClientKind, settings: Settings, httpx_mock: HTTPXMock
) -> None:
    mock_response = {"reminders": [{"id": "r1"}]}
    httpx_mock.add_response(
        url=build_url(settings, "/search/reminders", "query=follow"),
        json=mock_response,
    )

    async with client_context(client_kind, settings) as client:
        reminders = await maybe_await(client.search_reminders({"query": "follow"}))

    request = get_single_request(httpx_mock)
    assert request.method == "GET"
    assert str(request.url) == build_url(settings, "/search/reminders", "query=follow")
    assert reminders == mock_response["reminders"]


async def test_search_tags(
    client_kind: ClientKind, settings: Settings, httpx_mock: HTTPXMock
) -> None:
    mock_response = {"tags": [{"id": "tag1"}]}
    httpx_mock.add_response(
        url=build_url(settings, "/search/tags", "query=vip"),
        json=mock_response,
    )

    async with client_context(client_kind, settings) as client:
        tags = await maybe_await(client.search_tags({"query": "vip"}))

    request = get_single_request(httpx_mock)
    assert request.method == "GET"
    assert str(request.url) == build_url(settings, "/search/tags", "query=vip")
    assert tags == mock_response["tags"]


async def test_search_views(
    client_kind: ClientKind, settings: Settings, httpx_mock: HTTPXMock
) -> None:
    mock_response = {"views": [{"id": "v1"}]}
    httpx_mock.add_response(
        url=build_url(settings, "/search/views", "query=active"),
        json=mock_response,
    )

    async with client_context(client_kind, settings) as client:
        views = await maybe_await(client.search_views({"query": "active"}))

    request = get_single_request(httpx_mock)
    assert request.method == "GET"
    assert str(request.url) == build_url(settings, "/search/views", "query=active")
    assert views == mock_response["views"]


async def test_tags_crud_and_counts(
    client_kind: ClientKind, settings: Settings, httpx_mock: HTTPXMock
) -> None:
    httpx_mock.add_response(
        url=build_url(settings, "/tags"), json={"tags": [{"id": "t1"}]}
    )
    httpx_mock.add_response(
        url=build_url(settings, "/tags/t1"), json={"id": "t1", "name": "VIP"}
    )
    httpx_mock.add_response(
        url=build_url(settings, "/tags"),
        method="POST",
        json={"id": "t2", "name": "Lead"},
    )
    httpx_mock.add_response(
        url=build_url(settings, "/tags/t1"),
        method="PUT",
        json={"id": "t1", "name": "VIP Updated"},
    )
    httpx_mock.add_response(
        url=build_url(settings, "/tags/t1"),
        method="DELETE",
        json={"deleted": True},
    )
    httpx_mock.add_response(url=build_url(settings, "/tags/count"), json={"count": 2})
    httpx_mock.add_response(
        url=build_url(settings, "/tags/contact-counts"),
        json={"counts": [{"id": "t1", "contact_count": 5}]},
    )

    async with client_context(client_kind, settings) as client:
        tags = await maybe_await(client.get_tags())
        tag = await maybe_await(client.get_tag("t1"))
        created = await maybe_await(client.create_tag({"name": "Lead"}))
        updated = await maybe_await(client.update_tag("t1", {"name": "VIP Updated"}))
        deleted = await maybe_await(client.delete_tag("t1"))
        total = await maybe_await(client.count_tags())
        counts = await maybe_await(client.get_tag_contact_counts())

    requests = httpx_mock.get_requests()
    assert len(requests) == 7
    request_list = requests[0]
    assert request_list.method == "GET"
    assert str(request_list.url) == build_url(settings, "/tags")

    request_get = requests[1]
    assert request_get.method == "GET"
    assert str(request_get.url) == build_url(settings, "/tags/t1")

    request_post = requests[2]
    assert request_post.method == "POST"
    assert str(request_post.url) == build_url(settings, "/tags")
    assert json.loads(request_post.content) == {"name": "Lead"}

    request_put = requests[3]
    assert request_put.method == "PUT"
    assert str(request_put.url) == build_url(settings, "/tags/t1")
    assert json.loads(request_put.content) == {"name": "VIP Updated"}

    request_delete = requests[4]
    assert request_delete.method == "DELETE"
    assert str(request_delete.url) == build_url(settings, "/tags/t1")

    request_count = requests[5]
    assert request_count.method == "GET"
    assert str(request_count.url) == build_url(settings, "/tags/count")

    request_counts = requests[6]
    assert request_counts.method == "GET"
    assert str(request_counts.url) == build_url(settings, "/tags/contact-counts")

    assert tags == [{"id": "t1"}]
    assert tag == {"id": "t1", "name": "VIP"}
    assert created == {"id": "t2", "name": "Lead"}
    assert updated == {"id": "t1", "name": "VIP Updated"}
    assert deleted == {"deleted": True}
    assert total == 2
    assert counts == [{"id": "t1", "contact_count": 5}]


async def test_get_current_user(
    client_kind: ClientKind, settings: Settings, httpx_mock: HTTPXMock
) -> None:
    mock_response = {"id": "user-1", "email": "me@example.com"}
    httpx_mock.add_response(url=build_url(settings, "/users/me"), json=mock_response)

    async with client_context(client_kind, settings) as client:
        user = await maybe_await(client.get_current_user())

    request = get_single_request(httpx_mock)
    assert request.method == "GET"
    assert str(request.url) == build_url(settings, "/users/me")
    assert user == mock_response
