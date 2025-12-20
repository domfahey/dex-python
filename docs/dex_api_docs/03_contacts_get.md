# Fetch Contacts

The Contacts feature is the cornerstone of the Dex application. This section provides detailed instructions on how to fetch contacts using either their email address or unique ID.

## GET contacts

Fetch a list of contacts.

```
GET https://api.getdex.com/api/rest/contacts?limit=2&offset=0
```

### Path Parameters

**limit** `string`

Set a limit of possible records for the result (Default:10)

**offset** `string`

Set an offset of records, util for pagination (Default:0)

### 200: OK Response body

```json
{
    "contacts": [
        {
            "id": "contact-123",
            "first_name": "Example",
            "last_name": "Contact",
            "job_title": null,
            "description": null,
            "emails": [],
            "phones": [],
            "education": null,
            "image_url": "https://example.com/avatar-1.jpg",
            "linkedin": null,
            "facebook": "example_user",
            "twitter": null,
            "instagram": null,
            "telegram": null,
            "birthday_current_year": null,
            "last_seen_at": null,
            "next_reminder_at": null
        },
        {
            "id": "contact-456",
            "first_name": "Sample",
            "last_name": "Person",
            "job_title": null,
            "description": null,
            "emails": [],
            "phones": [],
            "education": null,
            "image_url": "https://example.com/avatar-2.jpg",
            "linkedin": null,
            "facebook": "sample_user",
            "twitter": null,
            "instagram": null,
            "telegram": null,
            "birthday_current_year": null,
            "last_seen_at": null,
            "next_reminder_at": null
        }
    ],
    "pagination": {
        "total": {
            "count": 2682
        }
    }
}
```

## GET a contact by ID

Pass a contact id and fetches the full contact information.

```
GET https://api.getdex.com/api/rest/contacts/{contactId}
```

### 200: OK Response body

```json
{
    "contacts": [
        {
            "id": "contact-123",
            "first_name": "Example",
            "last_name": "Contact",
            "job_title": null,
            "description": null,
            "emails": [],
            "phones": [],
            "education": null,
            "image_url": "https://example.com/avatar-1.jpg",
            "linkedin": null,
            "facebook": "example_user",
            "twitter": null,
            "instagram": null,
            "telegram": null,
            "birthday_current_year": null,
            "last_seen_at": null,
            "next_reminder_at": null
        }
    ]
}
```

## GET a contact by email address

Fetches a contact matching with the email provided.

```
GET https://api.getdex.com/api/rest/search/contacts?email=user@example.com
```

### Path Parameters

**email** `string` **required**

Email address of the contact

### 200: OK Response body

```json
{
    "search_contacts_by_exact_email": [
        {
            "id": "contact-123",
            "first_name": "Example",
            "last_name": "Contact",
            "job_title": null,
            "description": null,
            "emails": [
                {
                    "email": "user@example.com"
                }
            ],
            "phones": [
                {
                    "phone_number": "555-0100"
                }
            ],
            "education": null,
            "image_url": "https://example.com/avatar-1.jpg",
            "linkedin": null,
            "facebook": "example_user",
            "twitter": null,
            "instagram": null,
            "telegram": null,
            "birthday_current_year": null,
            "last_seen_at": null,
            "next_reminder_at": null
        }
    ]
}
```
