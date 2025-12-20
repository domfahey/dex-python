# Create a Contact

## POST a contact

Creates a new contact

```
POST https://api.getdex.com/api/rest/contacts
```

### 201: Created Request Body

```json
{
    "contact": {
            "first_name": "",
            "last_name": "",
            "job_title": null,
            "description": null,
            "contact_emails": {"data": {"email": "user@example.com"}},
            "contact_phone_numbers": {"data": {"phone_number": "555-0100", "label": "Work"}},
            "education": null,
            "image_url": "https://example.com/avatar-1.jpg",
            "linkedin": null,
            "twitter": null,
            "instagram": null,
            "telegram": null,
            "birthday_year": null,
            "last_seen_at": null,
            "next_reminder_at": null,
            "website": null
    }
}
```
