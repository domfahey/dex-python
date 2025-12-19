# Create a Note

## POST a note

Creates a new note

```
POST https://api.getdex.com/api/rest/timeline_items
```

### 201:Created Request Body

```json
{
    "timeline_event": {
        "note": "write your note here...",
        "event_time": "2023-05-19T01:03:27.083Z",
        "meeting_type": "note",
        "timeline_items_contacts": {
            "data": [{"contact_id" : "75b7bc73-7be0-41a6-960a-183555c80976"}]
        }
    }
}
```
