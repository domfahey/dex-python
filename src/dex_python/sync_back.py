"""Sync enriched data back to Dex API."""

import json
import sqlite3
from datetime import UTC, datetime
from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .client import DexClient

from .models import ContactUpdate, NoteCreate


class SyncBackMode(Enum):
    """Available modes for syncing enrichment data back to Dex."""

    NOTES = "notes"
    DESCRIPTION = "description"
    JOB_TITLE = "job_title"


def build_enrichment_note(company: str | None, role: str | None) -> str | None:
    """Build note text for enrichment data.

    Args:
        company: Extracted company name.
        role: Extracted role/position.

    Returns:
        Formatted note text, or None if no data to add.
    """
    if not company and not role:
        return None

    parts = ["[Enriched] Job title parsed:"]
    if role:
        parts.append(f"Role: {role}")
    if company:
        parts.append(f"Company: {company}")

    return "\n".join(parts)


def build_description_update(
    company: str | None,
    role: str | None,
    existing_description: str | None,
) -> str | None:
    """Build updated description with enrichment data.

    Args:
        company: Extracted company name.
        role: Extracted role/position.
        existing_description: Current description from Dex.

    Returns:
        Updated description text, or None if no enrichment to add.
    """
    if not company and not role:
        return None

    enrichment_parts = []
    if role:
        enrichment_parts.append(f"Role: {role}")
    if company:
        enrichment_parts.append(f"Company: {company}")

    enrichment_text = "[Enriched] " + " | ".join(enrichment_parts)

    if existing_description:
        return f"{existing_description}\n\n{enrichment_text}"
    return enrichment_text


def build_job_title_update(role: str | None, company: str | None) -> str | None:
    """Build reformatted job title as 'Role | Company'.

    Args:
        role: Extracted role/position.
        company: Extracted company name.

    Returns:
        Reformatted job title, or None if no role available.
    """
    if not role:
        return None

    if company:
        return f"{role} | {company}"
    return role


def get_contacts_for_sync(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    """Get contacts that have enrichment data to sync.

    Args:
        conn: SQLite database connection.

    Returns:
        List of contact dicts with enrichment data.
    """
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, company, role, full_data
        FROM contacts
        WHERE company IS NOT NULL OR role IS NOT NULL
    """)

    contacts = []
    for row in cursor.fetchall():
        contact_id, company, role, full_data_json = row

        # Parse existing description from full_data
        existing_description = None
        if full_data_json:
            try:
                full_data = json.loads(full_data_json)
                existing_description = full_data.get("description")
            except (json.JSONDecodeError, TypeError):
                pass

        contacts.append(
            {
                "id": contact_id,
                "company": company,
                "role": role,
                "existing_description": existing_description,
            }
        )

    return contacts


def sync_as_notes(
    conn: sqlite3.Connection,
    client: "DexClient",
    progress_callback: Any = None,
) -> dict[str, int]:
    """Sync enrichment data as notes on each contact.

    Args:
        conn: SQLite database connection.
        client: Dex API client.
        progress_callback: Optional callback(current, total, stats) for progress.

    Returns:
        Stats dict with created, skipped, errors counts.
    """
    contacts = get_contacts_for_sync(conn)
    stats = {"created": 0, "skipped": 0, "errors": 0}
    total = len(contacts)

    for i, contact in enumerate(contacts):
        note_text = build_enrichment_note(contact["company"], contact["role"])
        if not note_text:
            stats["skipped"] += 1
            continue

        try:
            note = NoteCreate.with_contacts(
                note=note_text,
                contact_ids=[contact["id"]],
                event_time=datetime.now(UTC).isoformat(),
            )
            client.create_note(note)
            stats["created"] += 1
        except Exception:
            stats["errors"] += 1

        if progress_callback and (i + 1) % 100 == 0:
            progress_callback(i + 1, total, stats)

    return stats


def sync_as_description(
    conn: sqlite3.Connection, client: "DexClient"
) -> dict[str, int]:
    """Sync enrichment data to contact description field.

    Args:
        conn: SQLite database connection.
        client: Dex API client.

    Returns:
        Stats dict with updated, skipped, errors counts.
    """
    contacts = get_contacts_for_sync(conn)
    stats = {"updated": 0, "skipped": 0, "errors": 0}

    for contact in contacts:
        new_description = build_description_update(
            contact["company"],
            contact["role"],
            contact["existing_description"],
        )
        if not new_description:
            stats["skipped"] += 1
            continue

        try:
            update = ContactUpdate(
                contactId=contact["id"],
                changes={"description": new_description},
            )
            client.update_contact(update)
            stats["updated"] += 1
        except Exception:
            stats["errors"] += 1

    return stats


def sync_as_job_title(conn: sqlite3.Connection, client: "DexClient") -> dict[str, int]:
    """Sync enrichment data as reformatted job title.

    Args:
        conn: SQLite database connection.
        client: Dex API client.

    Returns:
        Stats dict with updated, skipped, errors counts.
    """
    contacts = get_contacts_for_sync(conn)
    stats = {"updated": 0, "skipped": 0, "errors": 0}

    for contact in contacts:
        new_title = build_job_title_update(contact["role"], contact["company"])
        if not new_title:
            stats["skipped"] += 1
            continue

        try:
            update = ContactUpdate(
                contactId=contact["id"],
                changes={"job_title": new_title},
            )
            client.update_contact(update)
            stats["updated"] += 1
        except Exception:
            stats["errors"] += 1

    return stats


def run_sync(
    conn: sqlite3.Connection, client: "DexClient", mode: SyncBackMode
) -> dict[str, int]:
    """Run sync in the specified mode.

    Args:
        conn: SQLite database connection.
        client: Dex API client.
        mode: Sync mode to use.

    Returns:
        Stats dict from the sync operation.
    """
    if mode == SyncBackMode.NOTES:
        return sync_as_notes(conn, client)
    elif mode == SyncBackMode.DESCRIPTION:
        return sync_as_description(conn, client)
    elif mode == SyncBackMode.JOB_TITLE:
        return sync_as_job_title(conn, client)
    else:
        raise ValueError(f"Unknown sync mode: {mode}")
