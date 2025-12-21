# Name Parsing (probablepeople)

This guide explains how Dex Python parses contact names with
[`probablepeople`](https://github.com/datamade/probablepeople) and stores the
results in SQLite.

## Overview

During sync, Dex Python uses probablepeople to extract structured name
components (given, middle, surname, prefix, suffix, nickname). Parsed data is
stored alongside the raw contact data so you can normalize names or improve
deduplication safely.

Parsing is best-effort. All fields are optional and may be null.

## Where parsing runs

- `main.py` (full sync) parses names for every contact.
- `sync_with_integrity.py` (incremental sync) parses names for added/updated
  contacts.

To backfill name parsing in an existing database, re-run either sync script.

## Database schema

Parsed fields are stored on the `contacts` table:

- `name_parse_type` (TEXT): parse classification returned by probablepeople.
- `name_parsed` (JSON): raw parse payload (stored as JSON string).
- `name_given` (TEXT)
- `name_middle` (TEXT)
- `name_surname` (TEXT)
- `name_prefix` (TEXT)
- `name_suffix` (TEXT)
- `name_nickname` (TEXT)

The JSON payload contains:

- `raw`: the raw name string used for parsing.
- `parse_type`: probablepeople parse type (if available).
- `tokens`: tokenized parse output (if available).
- `components`: normalized component map (if available).
- `error`: parse error message (if an error occurred).

## Best practices

- Treat parsed values as hints, not ground truth.
- Keep the original `first_name`/`last_name` untouched; store derived values in
  the parsing columns only.
- Expect failures or noisy output for non-person names or international formats.
- Handle nulls in downstream logic; `name_parsed` may contain an `error` field.

## Example queries

Inspect parsed results:

```sql
SELECT id, name_given, name_surname, name_parse_type
FROM contacts
WHERE name_given IS NOT NULL
LIMIT 10;
```

Find parse errors:

```sql
SELECT id, name_parsed
FROM contacts
WHERE name_parsed LIKE '%"error"%';
```

## Installation notes

`probablepeople` depends on native extensions (`python-crfsuite`), so your
system may need build tools (e.g., Xcode Command Line Tools on macOS or build
essentials on Linux). Install dependencies with:

```bash
uv sync --all-extras --dev
```
