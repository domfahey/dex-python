# Implementation Plan: Full Dex API SDK

## Current State

### Implemented Endpoints (15/15)
| Endpoint | Method | Status | Notes |
|----------|--------|--------|-------|
| `/contacts` | GET | ✅ | Pagination supported |
| `/contacts/{id}` | GET | ✅ | Returns single contact |
| `/search/contacts?email=` | GET | ✅ | Search by email |
| `/contacts` | POST | ✅ | Uses ContactCreate model |
| `/contacts/{id}` | PUT | ✅ | Uses ContactUpdate model |
| `/contacts/{id}` | DELETE | ✅ | Basic implementation |
| `/reminders` | GET | ✅ | Pagination supported |
| `/reminders` | POST | ✅ | Uses ReminderCreate model |
| `/reminders/{id}` | PUT | ⚠️ | Uses raw dict, needs model |
| `/reminders/{id}` | DELETE | ✅ | Basic implementation |
| `/timeline_items` | GET | ✅ | Pagination supported |
| `/timeline_items/contacts/{id}` | GET | ✅ | Notes by contact |
| `/timeline_items` | POST | ✅ | Uses NoteCreate model |
| `/timeline_items/{id}` | PUT | ⚠️ | Uses raw dict, needs model |
| `/timeline_items/{id}` | DELETE | ✅ | Basic implementation |

### Gaps to Address
1. **Missing Update Models**: ReminderUpdate, NoteUpdate
2. **No Pagination Wrappers**: Can't access total count
3. **No Custom Exceptions**: Generic httpx errors only
4. **No Async Support**: Sync client only
5. **No Retry Logic**: Fails on transient errors
6. **Limited Test Coverage**: Missing tests for update/delete

---

## Phase 1: Complete Models (TDD)

### 1.1 Add ReminderUpdate Model
**Test First:**
```python
def test_reminder_update_model():
    update = ReminderUpdate(
        reminder_id="123",
        changes={"text": "Updated", "is_complete": True},
    )
    assert update.reminder_id == "123"
```

**Implementation:**
- Add `ReminderUpdate` to `models.py`
- Fields: reminder_id, changes, reminders_contacts, update_contacts
- Match API schema from `09_reminders_put.md`

### 1.2 Add NoteUpdate Model
**Test First:**
```python
def test_note_update_model():
    update = NoteUpdate(
        note_id="123",
        changes={"note": "Updated text"},
    )
    assert update.note_id == "123"
```

**Implementation:**
- Add `NoteUpdate` to `models.py`
- Fields: note_id, changes, timeline_items_contacts, update_contacts
- Match API schema from `13_notes_put.md`

### 1.3 Add Pagination Response Models
**Test First:**
```python
def test_paginated_response():
    response = PaginatedContacts(
        contacts=[...],
        total=100,
    )
    assert response.total == 100
```

**Implementation:**
- Add `PaginatedContacts`, `PaginatedReminders`, `PaginatedNotes`
- Include total count from API pagination response

---

## Phase 2: Update Client Methods (TDD)

### 2.1 Refactor update_reminder
**Test First:**
```python
def test_update_reminder_with_model(settings, httpx_mock):
    update = ReminderUpdate(reminder_id="123", changes={"text": "New"})
    # ... mock and test
```

**Implementation:**
- Change signature to accept `ReminderUpdate` model
- Use `model_dump(exclude_none=True)`

### 2.2 Refactor update_note
**Test First:**
```python
def test_update_note_with_model(settings, httpx_mock):
    update = NoteUpdate(note_id="123", changes={"note": "New"})
    # ... mock and test
```

**Implementation:**
- Change signature to accept `NoteUpdate` model
- Use `model_dump(exclude_none=True)`

### 2.3 Add Paginated Response Methods
**Test First:**
```python
def test_get_contacts_paginated():
    result = client.get_contacts_paginated(limit=10)
    assert result.total == 100
    assert len(result.contacts) == 10
```

**Implementation:**
- Add `get_contacts_paginated()` returning `PaginatedContacts`
- Add `get_reminders_paginated()` returning `PaginatedReminders`
- Add `get_notes_paginated()` returning `PaginatedNotes`

---

## Phase 3: Error Handling (TDD)

### 3.1 Custom Exceptions
**Test First:**
```python
def test_not_found_raises_exception(httpx_mock):
    httpx_mock.add_response(status_code=404)
    with pytest.raises(ContactNotFoundError):
        client.get_contact("invalid-id")
```

**Implementation:**
- Create `exceptions.py` with:
  - `DexAPIError` (base)
  - `ContactNotFoundError`
  - `ReminderNotFoundError`
  - `NoteNotFoundError`
  - `AuthenticationError`
  - `RateLimitError`
  - `ValidationError`

### 3.2 Error Response Parsing
- Parse API error messages
- Include request details in exceptions
- Preserve original httpx exception as cause

---

## Phase 4: Async Client (TDD)

### 4.1 AsyncDexClient
**Test First:**
```python
@pytest.mark.asyncio
async def test_async_get_contacts(httpx_mock):
    async with AsyncDexClient() as client:
        contacts = await client.get_contacts()
    assert len(contacts) == 2
```

**Implementation:**
- Create `AsyncDexClient` using `httpx.AsyncClient`
- Mirror all sync methods with async versions
- Share models between sync/async clients

---

## Phase 5: Reliability (TDD)

### 5.1 Retry Logic
**Test First:**
```python
def test_retry_on_transient_error(httpx_mock):
    httpx_mock.add_response(status_code=503)
    httpx_mock.add_response(json={"contacts": []})
    contacts = client.get_contacts()  # Should succeed on retry
```

**Implementation:**
- Add retry decorator with exponential backoff
- Retry on 429, 500, 502, 503, 504
- Configurable max retries and delay

### 5.2 Request Timeout Configuration
- Add configurable timeouts per operation
- Default: 30s for reads, 60s for writes

---

## Phase 6: Documentation & Polish

### 6.1 Update API Docs
- Document all models with examples
- Document all client methods
- Add usage examples for common workflows

### 6.2 Update CLAUDE.md
- Add new commands
- Document new features

### 6.3 Add Type Stubs
- Ensure full mypy --strict compliance
- Export all types in `__init__.py`

---

## Implementation Order

1. **Phase 1.1**: ReminderUpdate model + tests
2. **Phase 1.2**: NoteUpdate model + tests
3. **Phase 2.1**: Refactor update_reminder + tests
4. **Phase 2.2**: Refactor update_note + tests
5. **Phase 3.1**: Custom exceptions + tests
6. **Phase 1.3**: Pagination models + tests
7. **Phase 2.3**: Paginated methods + tests
8. **Phase 4.1**: Async client + tests
9. **Phase 5.1**: Retry logic + tests
10. **Phase 6**: Documentation

---

## Success Criteria

- [ ] All 15 API endpoints fully supported with typed models
- [ ] 100% test coverage for client methods
- [ ] Integration tests pass for all endpoints
- [ ] mypy --strict passes with no errors
- [ ] ruff check passes with no errors
- [ ] Async client available
- [ ] Custom exceptions for all error cases
- [ ] Retry logic for transient failures
- [ ] Full API documentation
