"""Tests for name parsing helpers."""

import json

from dex_python.name_parsing import NAME_FIELD_KEYS, parse_contact_name, parse_name


def test_parse_name_simple() -> None:
    """Parse a basic first/last name into components."""
    result = parse_name("Ada Lovelace")

    assert result["name_given"] == "Ada"
    assert result["name_surname"] == "Lovelace"

    parsed = json.loads(result["name_parsed"])
    assert parsed["raw"] == "Ada Lovelace"


def test_parse_contact_name_prefers_full_name() -> None:
    """Prefer full_name when present."""
    result = parse_contact_name(
        {"full_name": "Grace Hopper", "first_name": "Grace", "last_name": "H."}
    )

    parsed = json.loads(result["name_parsed"])
    assert parsed["raw"] == "Grace Hopper"


def test_parse_contact_name_handles_missing() -> None:
    """Return null fields when no name is available."""
    result = parse_contact_name({})

    assert all(result[key] is None for key in NAME_FIELD_KEYS)
