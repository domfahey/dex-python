# Dex Python SDK: Missing Endpoints Implementation Plan

## Objective
Implement all remaining SDK endpoints listed in `docs/api.md` that are currently not implemented, while keeping parity between:
- `DexClient`
- `AsyncDexClient`

## Scope
The following documented endpoints are currently missing from implementation:
- Contacts: bulk update/delete, count, search, filter, by-emails, merge
- Reminders: single get by ID, recurring list
- Notes/Timeline: `/timeline` CRUD/read coverage and metadata endpoints
- Custom Fields: create/update/delete/reorder/batch update
- Groups: list/get/create/update/delete/count/contacts endpoints/add/remove endpoints
- Search: groups/timeline/reminders/tags/views
- Tags: list/get/create/update/delete/count/contact-counts
- Users: current user

---

## Principles
1. Keep synchronous and asynchronous methods in lockstep.
2. Preserve existing behavior and legacy paths already used by the SDK (notably `/v1/custom-fields`).
3. Prefer existing request payload/model handling where available.
4. Use explicit request methods and avoid breaking existing method names.
5. Add unit tests for each new method and payload shape.

---

## Phase 1: Contract and naming
- Review endpoint routes in `docs/api.md` and choose method names consistent with existing style.
- Decide conflict handling:
  - `get_contact_by_email` currently hits `/search/contacts` with `email`; keep as-is.
  - Add a separate `search_contacts(...)` for broader `/contacts/search` usage.
- Decide how to expose timeline routes:
  - Keep existing `/timeline_items` methods for backward compatibility.
  - Add docs-aligned `/timeline` methods as new APIs.

---

## Phase 2: Contacts API
Implement in both clients:

### Contact listing/searching/management
- `update_contacts_bulk(payload: dict[str, Any])` -> `PUT /contacts`
- `delete_contacts_bulk(payload: dict[str, Any])` -> `DELETE /contacts`
- `count_contacts()` -> `GET /contacts/count`
- `search_contacts(params: dict[str, Any])` -> `GET /contacts/search`
- `filter_contacts(payload: dict[str, Any])` -> `POST /contacts/filter`
- `find_contacts_by_emails(payload: dict[str, Any] | list[str])` -> `POST /contacts/by-emails`
- `merge_contacts(payload: dict[str, Any])` -> `POST /contacts/merge`

### Notes
- Reuse existing `_request` and `_request_with_retry` paths.
- Return type: existing pattern (`dict[str, Any]` / `list[dict[str, Any]]`) unless a stable model is introduced.

---

## Phase 3: Reminders API
Add in both clients:
- `get_reminder(reminder_id: str)` -> `GET /reminders/{reminderId}`
- `get_recurring_reminders()` -> `GET /reminders/recurring`

---

## Phase 4: Custom Fields API
Add in both clients:
- `create_custom_field(payload: dict[str, Any])` -> `POST /v1/custom-fields`
- `update_custom_field(custom_field_id: str, payload: dict[str, Any])` -> `PUT /v1/custom-fields/{customFieldId}`
- `delete_custom_field(custom_field_id: str)` -> `DELETE /v1/custom-fields/{customFieldId}`
- `reorder_custom_fields(payload: dict[str, Any])` -> `PUT /v1/custom-fields/reorder`
- `batch_update_custom_fields_contacts(payload: dict[str, Any])` -> `POST /v1/custom-fields/batch-update-contacts`

---

## Phase 5: Groups API
Add in both clients:
- `get_groups()` -> `GET /groups`
- `get_group(group_id: str)` -> `GET /groups/{groupId}`
- `create_group(payload)` -> `POST /groups`
- `update_group(group_id, payload)` -> `PUT /groups/{groupId}`
- `delete_group(group_id)` -> `DELETE /groups/{groupId}`
- `count_groups()` -> `GET /groups/count`
- `get_group_contacts(group_id)` -> `GET /groups/{groupId}/contacts`
- `add_group_contacts(group_id, payload)` -> `PUT /groups/{groupId}/contacts`
- `remove_group_contacts(group_id, payload)` -> `POST /groups/{groupId}/contacts`
- `get_group_contact_counts()` -> `GET /groups/contact-counts`

---

## Phase 6: Search API
Add in both clients:
- `search_groups(params: dict[str, Any])` -> `GET /search/groups`
- `search_timeline(params: dict[str, Any])` -> `GET /search/timeline`
- `search_reminders(params: dict[str, Any])` -> `GET /search/reminders`
- `search_tags(params: dict[str, Any])` -> `GET /search/tags`
- `search_views(params: dict[str, Any])` -> `GET /search/views`

---

## Phase 7: Tags API
Add in both clients:
- `get_tags()` -> `GET /tags`
- `get_tag(tag_id: str)` -> `GET /tags/{tagId}`
- `create_tag(payload)` -> `POST /tags`
- `update_tag(tag_id: str, payload)` -> `PUT /tags/{tagId}`
- `delete_tag(tag_id: str)` -> `DELETE /tags/{tagId}`
- `count_tags()` -> `GET /tags/count`
- `get_tag_contact_counts()` -> `GET /tags/contact-counts`

---

## Phase 8: Timeline API (docs-aligned)
Add in both clients, while preserving existing `/timeline_items` methods:
- `get_timeline(limit=100, offset=0)` -> `GET /timeline`
- `get_timeline_note(note_id)` -> `GET /timeline/{noteId}`
- `count_timeline()` -> `GET /timeline/count`
- `get_timeline_note_types()` -> `GET /timeline/note-types`

### Fallback strategy
If API compatibility issues appear for `/timeline/{noteId}`, add optional fallback to `/timeline_items/{noteId}` only if needed.

---

## Phase 9: Users API
Add in both clients:
- `get_current_user()` -> `GET /users/me`

---

## Phase 10: Validation, tests, and docs
- Add unit tests in `tests/unit/test_clients.py` for each new sync and async method:
  - correct HTTP method
  - URL path
  - query params or body
  - success/error mapping
- Update `docs/api.md` implementation notes to reflect full coverage.
- Ensure exported names in `src/dex_python/__init__.py` for any new request/response models.

---

## Risks / follow-up
- Timeline route inconsistency (`/timeline` vs `/timeline_items`) must be validated against live API behavior.
- Some generic routes may require request payload shapes not yet modeled; start with dict-based payloads if needed.
- Keep this rollout incremental and backwards compatible.
