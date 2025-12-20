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
      "contact_id": "contact-123",
      "phone_number": "555-0100",
      "label": "Work"  
    }
  ],
  "update_contact_emails": true,
  "contact_emails": [
    {
      "contact_id": "contact-123",
      "email": "user@example.com"
    }
  ],
  "contactId": "contact-123",
  "changes": {
      "first_name": "Example",
      "last_name": "Contact",
      "job_title": null,
      "description": null,
      "education": null,
      "image_url": "https://example.com/avatar-1.jpg",
      "linkedin": null,
      "facebook": "example_user",
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
