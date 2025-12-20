# Roadmap

This document captures potential improvements for the Dex Import client and
local deduplication workflow. Items are grouped by priority and scope; order is
roughly highest impact first.

## Goals

- Keep the client stable and predictable as the API evolves.
- Make sync + dedup workflows safe, repeatable, and auditable.
- Improve developer ergonomics (tests, docs, CI, packaging).

## Near Term (Stability and Correctness)

- Add schema versioning and migrations for `dex_contacts.db`.
- Preserve dedup metadata on sync updates and document the contract.
- Normalize phone numbers (digits-only, country handling) before comparisons.
- Normalize social handles/URLs (LinkedIn, website) for deterministic matches.
- Add indexes on `emails.email`, `phones.phone_number`, and `contacts` name fields.
- Add retry-aware pagination for all sync scripts (fallback when totals are absent).
- Expand unit tests for normalization, merge edge cases, and SQLite integrity.

## Mid Term (Usability and Tooling)

- Replace single-purpose scripts with a unified CLI (`dex-import`) using Typer.
- Add a dry-run mode for merges and an "undo" snapshot feature.
- Support incremental sync by "updated_since" if/when the API supports it.
- Add structured logging (JSON) and progress summaries for long-running jobs.
- Publish a minimal dashboard report (HTML or Markdown) from duplicate analysis.
- Add CI (lint, type check, unit tests) and optional integration tests via secrets.

## Long Term (Scale and Productization)

- Implement weighted scoring and configurable thresholds for auto-merge.
- Introduce a review queue UI (TUI or lightweight web app).
- Support multi-tenant databases and per-account configuration.
- Package as a library + CLI with versioned releases and changelog automation.
- Add data export/import format (CSV/Parquet) for external analysis.
