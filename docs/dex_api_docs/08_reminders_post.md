# Create a Reminder

## POST a reminder

Creates a new reminder

```
POST https://api.getdex.com/api/rest/reminders
```

### 201: Created Request Body

```json
{
    "reminder": {
        "title": "sample title",
        "text": "adding sample reminder",
        "is_complete": false,
        "due_at_date": "2023-06-01",
        "reminders_contacts": {"data": [
                {"email": "75b7bc73-7be0-41a6-960a-183555c80976"}, 
                {"contact_id": "2a6102bc-972b-46da-8d3d-4eea17a757ce"}
            ]
        }
    }
}
```
