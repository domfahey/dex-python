# Dex Contact Deduplication Plan

This document describes the current duplicate detection pipeline and follow-up
ideas for the local SQLite workflow.

## Status
Current implementation focuses on email/phone/name matches plus fuzzy name
matching. Items in Future Enhancements are not implemented yet.

## 1. Data Normalization (Current)
- Emails: case-insensitive matching via `lower(email)` in SQL.
- Names: trimmed and lowercased for deterministic name + title matches.
- Phones: raw matching only (no normalization yet).
- URLs/social handles: not matched (future).

## 2. Detection Levels (Current)

### Level 1: Deterministic
- Shared email (case-insensitive).
- Shared phone (raw string match).

### Level 2: Rule-Based
- First name + last name + job title (case-insensitive, trimmed; requires all
  fields).

### Level 3: Fuzzy Name
- Jaro-Winkler similarity on `first_name last_name`.
- Blocking by `metaphone(last_name)` (fallback to first two letters).
- Threshold is configurable per script.

## 3. Thresholds Used in Scripts
- `analyze_duplicates.py`: `threshold=0.95` for reporting.
- `flag_duplicates.py`: `threshold=0.98` for grouping.
- `resolve_duplicates.py`: `threshold=0.98` for auto-merge candidates.

## 4. Resolution Strategy
- Build a graph of match edges and cluster with connected components.
- Merge clusters in SQLite; emails/phones are de-duplicated by value.

## 5. Workflow
1. Sync contacts to SQLite (`main.py` or `sync_with_integrity.py`) in the
   `output/` directory by default (override with `DEX_DATA_DIR`).
2. Generate a report (`analyze_duplicates.py`).
3. Flag candidate groups (`flag_duplicates.py`).
4. Review and choose primaries (`review_duplicates.py`).
5. Merge confirmed groups (`resolve_duplicates.py`).

## 6. Future Enhancements
- Phone normalization (strip non-digits, handle country codes).
- LinkedIn / website matching and name+domain heuristics.
- Weighted scoring and confidence thresholds for auto-merge vs review.
