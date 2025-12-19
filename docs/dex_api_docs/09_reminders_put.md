# Update a Reminder

## PUT for updating a reminder

Updates an existing reminder by its ID

```
PUT https://api.getdex.com/api/rest/reminders/{reminderId}
```

### Path Parameters

**reminderID** `string` **required**

The ID of the reminder to be updated

### 200:OK Request Body

```json
{
    "changes": {
        "text": "",
        "is_complete": false,
        "due_at_time": null,
        "due_at_date": "2024-05-17"
    },
    "reminders_contacts": [
        {
            "reminder_id": "374e36cd-74b5-4f6e-9196-65c3e5ee9f08",
            "contact_id": "75b7bc73-7be0-41a6-960a-183555c80976"
        }
    ],
    "update_contacts": false
}
```

You can use the variable `update_contacts` in the API to decide whether if you want to update the contacts associated with the reminder or not.
