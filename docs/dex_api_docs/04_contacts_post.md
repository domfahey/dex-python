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
            "contact_emails": {"data": {"email": "@gmail.com"}},
            "contact_phone_numbers": {"data": {"phone_number": "", "label": "Work"}},
            "education": null,
            "image_url": "https://storage.googleapis.com/dex-staging.appspot.com/contacts/prh1HWo44ibdMHUGZ3Xsa7XpnEZ2/9915d5ff-3f57-469a-892d-6ff01279bf85/avatar.jpeg",
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
