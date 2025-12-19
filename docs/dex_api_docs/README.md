# Dex API Documentation

Complete API documentation for the Dex platform, downloaded from [getdex.com](https://getdex.com/docs/api-reference/authentication).

## Base URL

```
https://api.getdex.com/api/rest
```

## Authentication

All API requests require the following headers:

- `Content-Type: application/json`
- `x-hasura-dex-api-key: your-api-key`

You can find your API Key on the API page within your Dex account. **Do not share your API key!**

## Documentation Structure

### Getting Started

1. [Authentication](01_authentication.md) - API authentication and authorization setup
2. [Deduplicate Notes](02_deduplicate_notes.md) - Sample script for deduplicating notes

### Contacts API

3. [GET Fetch Contacts](03_contacts_get.md) - Retrieve contacts by ID, email, or list all
4. [POST Create a Contact](04_contacts_post.md) - Create a new contact
5. [PUT Update Contacts](05_contacts_put.md) - Update existing contact information
6. [DELETE Delete Contact](06_contacts_delete.md) - Delete a contact by ID

### Reminders API

7. [GET Fetch all Reminders](07_reminders_get.md) - Retrieve all reminders
8. [POST Create a Reminder](08_reminders_post.md) - Create a new reminder
9. [PUT Update a Reminder](09_reminders_put.md) - Update existing reminder
10. [DELETE Delete a Reminder](10_reminders_delete.md) - Delete a reminder by ID

### Notes API

11. [GET Fetch all Notes](11_notes_get.md) - Retrieve all notes or notes by contact ID
12. [POST Create a Note](12_notes_post.md) - Create a new note
13. [PUT Update a Note](13_notes_put.md) - Update existing note
14. [DELETE Delete a Note](14_notes_delete.md) - Delete a note by ID

## API Endpoints Summary

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/contacts` | Fetch list of contacts |
| GET | `/contacts/{contactId}` | Fetch contact by ID |
| GET | `/search/contacts?email={email}` | Fetch contact by email |
| POST | `/contacts` | Create a new contact |
| PUT | `/contacts/{contactId}` | Update a contact |
| DELETE | `/contacts/{contactId}` | Delete a contact |
| GET | `/reminders` | Fetch all reminders |
| POST | `/reminders` | Create a new reminder |
| PUT | `/reminders/{reminderId}` | Update a reminder |
| DELETE | `/reminders/{reminderId}` | Delete a reminder |
| GET | `/timeline_items` | Fetch all notes |
| GET | `/timeline_items/contacts/:contactId` | Fetch notes by contact ID |
| POST | `/timeline_items` | Create a new note |
| PUT | `/timeline_items/{timelineItemId}` | Update a note |
| DELETE | `/timeline_items/{timelineItemId}` | Delete a note |

## Common Parameters

### Pagination

Most GET endpoints support pagination with the following query parameters:

- `limit` (string) - Set a limit of possible records for the result (Default: 10)
- `offset` (string) - Set an offset of records, useful for pagination (Default: 0)

## Response Format

All responses are in JSON format. Successful responses typically include:

- **Contacts**: `contacts` array with contact objects
- **Reminders**: `reminders` array with reminder objects
- **Notes**: `timeline_items` array with note objects
- **Pagination**: `pagination` or `total` object with count information

## Documentation Generated

This documentation was downloaded and converted to Markdown format on December 19, 2025.

For the most up-to-date information, please visit the official [Dex API documentation](https://getdex.com/docs/api-reference/authentication).
