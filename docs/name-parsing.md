# Name Parsing

This guide explains how Dex Python parses contact names and stores the results
in SQLite.

## Overview

During sync, Dex Python uses a lightweight parser that splits names into given
and surname parts. Parsed data is stored alongside the raw contact data so you
can normalize names or improve deduplication safely.

Parsing is best-effort. All fields are optional and may be null.

## Where parsing runs

- `scripts/main.py` (full sync) parses names for every contact.
- `scripts/sync_with_integrity.py` (incremental sync) parses names for added/updated
  contacts.

To backfill name parsing in an existing database, re-run either sync script.

## Database schema

Parsed fields are stored on the `contacts` table. The full sync schema includes:

- `name_parse_type` (TEXT): parse classification (currently `simple`).
- `name_parsed` (JSON): raw parse payload (stored as JSON string).
- `name_given` (TEXT)
- `name_middle` (TEXT)
- `name_surname` (TEXT)
- `name_prefix` (TEXT)
- `name_suffix` (TEXT)
- `name_nickname` (TEXT)

The incremental sync currently stores:

- `name_given` (TEXT)
- `name_surname` (TEXT)
- `name_parsed` (JSON)

The JSON payload contains:

- `raw`: the raw name string used for parsing.

## Best practices

- Treat parsed values as hints, not ground truth.
- Keep the original `first_name`/`last_name` untouched; store derived values in
  the parsing columns only.
- Expect noisy output for non-person names or international formats.
- Handle nulls in downstream logic.

## Example queries

Inspect parsed results:

```sql
SELECT id, name_given, name_surname
FROM contacts
WHERE name_given IS NOT NULL
LIMIT 10;
```

Find contacts with missing parsed values:

```sql
SELECT id, first_name, last_name
FROM contacts
WHERE name_parsed IS NULL;
```

## Installation notes

`probablepeople` is included as a dependency for planned richer parsing. It
depends on native extensions (`python-crfsuite`), so your system may need build
tools (e.g., Xcode Command Line Tools on macOS or build essentials on Linux).
Install dependencies with:

```bash
uv sync --all-extras --dev
```
