# Fetch all Reminders

## GET all reminders

Fetch all reminders

```
GET https://api.getdex.com/api/rest/reminders
```

### Path Parameters

**limit** `string`

**offset** `string`

### 200:OK Response Body

```json
{
    "reminders": [
        {
            "id": "178bcd37-a845-4afe-81fe-10d1b577918e",
            "body": "sample reminder",
            "is_complete": false,
            "due_at_time": null,
            "due_at_date": "2023-02-02",
            "contact_ids": []
        },
        {
            "id": "6d89a6b1-d980-4ce9-bcd8-f8ed80e4c9ad",
            "body": "adding sample reminder",
            "is_complete": false,
            "due_at_time": null,
            "due_at_date": "2023-06-01",
            "contact_ids": [
                {
                    "contact_id": "2a6102bc-972b-46da-8d3d-4eea17a757ce"
                },
                {
                    "contact_id": "75b7bc73-7be0-41a6-960a-183555c80976"
                }
            ]
        }
    ],
    "total": {
        "aggregate": {
            "count": 2
        }
    }
}
```
