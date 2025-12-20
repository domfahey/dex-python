# Update Contacts

## PUT for updating a contact

Updates an existing contact by its ID

```
PUT https://api.getdex.com/api/rest/contacts/{contactId}
```

### Path Parameters

**contactId** `string` **required**

The ID of the contact to be updated

### Request Body

```json
{
  "update_contact_phone_numbers": true,
  "contact_phone_numbers": [
    {
      "contact_id": "8df02237-532e-4307-a611-1ddab4307690",
      "phone_number": "9660077249",
      "label": "Work"  
    }
  ],
  "update_contact_emails": true,
  "contact_emails": [
    {
      "contact_id": "8df02237-532e-4307-a611-1ddab4307690",
      "email": "user@example.com"
    }
  ],
  "contactId": "8df02237-532e-4307-a611-1ddab4307690",
  "changes": {
      "first_name": "Kavya",
      "last_name": "Shankar",
      "job_title": null,
      "description": null,
      "education": null,
      "image_url": "https://storage.googleapis.com/dex-staging.appspot.com/contacts/prh1HWo44ibdMHUGZ3Xsa7XpnEZ2/9915d5ff-3f57-469a-892d-6ff01279bf85/avatar.jpeg",
      "linkedin": null,
      "facebook": "kavyashankar",
      "twitter": null,
      "instagram": null,
      "telegram": null,
      "last_seen_at": null,
      "next_reminder_at": null,
      "website": null
  }
}
```

You can use the variable `update_contact_phone_numbers` in the API to decide whether you want to update the phone numbers associated with the contact or not.

You can use the variable `update_contact_emails` in the API to decide whether you want to update the emails associated with the contact or not.
