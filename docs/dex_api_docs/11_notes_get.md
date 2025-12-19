# Fetch all Notes

## GET all notes

Fetch all notes

```
GET https://api.getdex.com/api/rest/timeline_items?limit=2&offset=0
```

### Path Parameters

**limit** `string`

**offset** `string`

### 200: OK Array of timeline item objects

```json
{
    "timeline_items": [
        {
            "id": "7a581ccc-440c-4659-a17b-8409ed8b4af3",
            "note": "first note",
            "event_time": "2023-05-19T01:03:27.083+00:00",
            "contacts": [
                {
                    "contact_id": "75b7bc73-7be0-41a6-960a-183555c80976"
                }
            ]
        },
        {
            "id": "6fc50cea-e00a-49f8-b5a1-3f6dbbcd1b4a",
            "note": "first note",
            "event_time": "2023-05-19T01:03:27.083+00:00",
            "contacts": []
        }
    ],
    "pagination": {
        "total": {
            "count": 19
        }
    }
}
```

## GET notes by Contact ID

Fetch notes by contact ID

```
GET https://api.getdex.com/api/rest/timeline_items/contacts/:contactId
```

### Path Parameters

**contactID** `string` **required**
