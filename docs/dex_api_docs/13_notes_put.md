# Update a Note

## PUT for updating a note

Updates an existing note by its ID

```
PUT https://api.getdex.com/api/rest/timeline_items/{timelineItemId}
```

### Path Parameters

**timelineItemId** `string` **required**

The ID of the timeline_item to be updated

### Request Body

```json
{
    "changes": {
        "note": "",
        "custom_emoji": "",
        "event_time": "2023-05-19T01:03:27.083Z",
        "meeting_type_id": "4e826a0b-d58f-43bf-90d4-7a0d53c88b9f"
    },
    "timeline_items_contacts": [
        {
            "timeline_item_id": "7a581ccc-440c-4659-a17b-8409ed8b4af3",
            "contact_id": "75b7bc73-7be0-41a6-960a-183555c80976"
        }
    ],
    "update_contacts": true
}
```
