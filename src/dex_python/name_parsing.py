"""Name parsing helpers for contact name normalization."""

import json
from typing import Any

# Fields returned by name parsing functions
NAME_FIELD_KEYS = (
    "name_given",
    "name_surname",
    "name_parsed",
    "name_parse_type",
    "name_middle",
    "name_prefix",
    "name_suffix",
    "name_nickname",
)


def parse_name(full_name: str) -> dict[str, Any]:
    """Parse a name string into components.

    Args:
        full_name: Full name string like "Ada Lovelace".

    Returns:
        Dict with name_given, name_surname, name_parsed, etc.
    """
    if not full_name:
        return {key: None for key in NAME_FIELD_KEYS}

    parts = full_name.strip().split()
    given = parts[0] if parts else ""
    surname = " ".join(parts[1:]) if len(parts) > 1 else ""

    parsed_data = {"raw": full_name.strip()}

    return {
        "name_given": given or None,
        "name_surname": surname or None,
        "name_parsed": json.dumps(parsed_data),
        "name_parse_type": "simple",
        "name_middle": None,
        "name_prefix": None,
        "name_suffix": None,
        "name_nickname": None,
    }


def parse_contact_name(contact: dict[str, Any]) -> dict[str, Any]:
    """Parse name from contact data, preferring full_name.

    Args:
        contact: Contact dict with first_name, last_name, or full_name.

    Returns:
        Dict with parsed name components.
    """
    full_name = contact.get("full_name")
    if full_name:
        return parse_name(full_name)

    first = contact.get("first_name", "")
    last = contact.get("last_name", "")
    if first or last:
        combined = f"{first} {last}".strip()
        return parse_name(combined)

    return {key: None for key in NAME_FIELD_KEYS}
