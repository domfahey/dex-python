# Deduplicate Notes

This script deduplicates and deletes notes based on content.

## Script

```python
import os, requests
from collections import defaultdict

# ─── CONFIG ──────────────────────────────────────────────────────────────
BASE_URL = "https://api.getdex.com/api/rest"
API_KEY  = "YOUR_API_KEY" # Add your API Key
HEADERS  = {
    "Content-Type": "application/json",
    "x-hasura-dex-api-key": API_KEY,
}

# ─── HELPERS ─────────────────────────────────────────────────────────────
def fetch_all_notes(limit: int = 200):
    """Yield every note object in the account."""
    offset = 0
    while True:
        r = requests.get(
            f"{BASE_URL}/timeline_items",
            params={"limit": limit, "offset": offset},
            headers=HEADERS,
            timeout=30,
        )
        r.raise_for_status()
        batch = r.json().get("timeline_items", [])
        if not batch:
            break
        yield from batch
        if len(batch) < limit:
            break
        offset += limit

def detect_duplicates(notes):
    """Return {normalized_text: [note_objs]} where len(list) > 1."""
    buckets = defaultdict(list)
    for n in notes:
        key = (n.get("note") or "").strip().lower()
        if key:
            buckets[key].append(n)
    return {k: v for k, v in buckets.items() if len(v) > 1}

def delete_note(note_id):
    print(note_id)
    r = requests.delete(
        f"{BASE_URL}/timeline_items/{note_id}",
        headers=HEADERS,
        timeout=15,
    )
    return r.ok, r.text

# Note: when ready to delete, replace False with True
delete = False 
notes = list(fetch_all_notes())
dupes = detect_duplicates(notes)

if not dupes:
    print("No duplicates found.")

print(f"Found {len(dupes)} duplicate group(s)\n")
for text, items in dupes.items():
    preview = (text[:80] + "…") if len(text) > 80 else text
    print("─" * 60)
    print(f'"{preview}"')
    for idx, itm in enumerate(items):
        print(f"  [{idx}] id={itm['id']}  time={itm['event_time']}")
    if delete:
        for itm in items[1:]:                                   # keep first
            ok, msg = delete_note(itm["id"])
            status = "✓ deleted" if ok else f"✗ error: {msg}"
            print(f"    ↳ {status} ({itm['id']})")
print("\nDone.")
```
