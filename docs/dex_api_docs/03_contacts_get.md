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
            "id": "8df02237-532e-4307-a611-1ddab4307690",
            "first_name": "Kavya",
            "last_name": "Shankar",
            "job_title": null,
            "description": null,
            "emails": [],
            "phones": [],
            "education": null,
            "image_url": "https://storage.googleapis.com/dex-staging.appspot.com/contacts/prh1HWo44ibdMHUGZ3Xsa7XpnEZ2/9915d5ff-3f57-469a-892d-6ff01279bf85/avatar.jpeg",
            "linkedin": null,
            "facebook": "kavyashankar",
            "twitter": null,
            "instagram": null,
            "telegram": null,
            "birthday_current_year": null,
            "last_seen_at": null,
            "next_reminder_at": null
        },
        {
            "id": "0a95f830-e40d-428b-91d1-b891c0106c28",
            "first_name": "Kay",
            "last_name": "Ag-hee",
            "job_title": null,
            "description": null,
            "emails": [],
            "phones": [],
            "education": null,
            "image_url": "https://storage.googleapis.com/dex-staging.appspot.com/contacts/prh1HWo44ibdMHUGZ3Xsa7XpnEZ2/4ac5772f-f298-409b-b18b-ed35e1f9cd79/avatar.jpeg",
            "linkedin": null,
            "facebook": "phdawl",
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
            "id": "8df02237-532e-4307-a611-1ddab4307690",
            "first_name": "Kavya",
            "last_name": "Shankar",
            "job_title": null,
            "description": null,
            "emails": [],
            "phones": [],
            "education": null,
            "image_url": "https://storage.googleapis.com/dex-staging.appspot.com/contacts/prh1HWo44ibdMHUGZ3Xsa7XpnEZ2/9915d5ff-3f57-469a-892d-6ff01279bf85/avatar.jpeg",
            "linkedin": null,
            "facebook": "kavyashankar",
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
GET https://api.getdex.com/api/rest/search/contacts?email=mikesuper@example.co
```

### Path Parameters

**email** `string` **required**

Email address of the contact

### 200: OK Response body

```json
{
    "search_contacts_by_exact_email": [
        {
            "id": "8df02237-532e-4307-a611-1ddab4307690",
            "first_name": "Kavya",
            "last_name": "Shankar",
            "job_title": null,
            "description": null,
            "emails": [
                {
                    "email": "user@example.com"
                }
            ],
            "phones": [
                {
                    "phone_number": "9660077249"
                }
            ],
            "education": null,
            "image_url": "https://storage.googleapis.com/dex-staging.appspot.com/contacts/prh1HWo44ibdMHUGZ3Xsa7XpnEZ2/9915d5ff-3f57-469a-892d-6ff01279bf85/avatar.jpeg",
            "linkedin": null,
            "facebook": "kavyashankar",
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
