# Roadmap

This document captures potential improvements for the Dex Import client and
local deduplication workflow. Items are grouped by priority and scope.

## Goals

- Keep the client stable and predictable as the API evolves.
- Make sync + dedup workflows safe, repeatable, and auditable.
- Improve developer ergonomics (tests, docs, CI, packaging).

## Completed / In Place

- **Robust Data Sync:**
    - [x] Async client with automatic retries for rate limits (429) and server errors (50x).
    - [x] Integrity checks using SHA-256 content hashing to detect changes.
    - [x] Client-side "incremental" sync (skips database writes for unchanged records).
    - [x] Concurrency control (semaphores) for efficient batch fetching.
- **Deduplication Engine:**
    - [x] Level 1: Exact matching (Email, Phone).
    - [x] Level 2: Composite matching (Name + Job Title).
    - [x] Level 3: Fuzzy matching (Jaro-Winkler similarity with Phonetic blocking).
    - [x] Graph-based clustering (`networkx`) to group transitive duplicates.
- **Tooling & UX:**
    - [x] Interactive TUI (`review_duplicates.py`) for labeling/resolving duplicates.
    - [x] Markdown reporting (`analyze_duplicates.py`) for duplicate auditing.
    - [x] Comprehensive test suite refactored into unit/integration structures.
    - [x] Makefiles for linting, formatting, and type checking.

## Near Term (Stability and Correctness)

- [ ] **Unified CLI:** Consolidate `sync_with_integrity.py`, `flag_duplicates.py`, and `review_duplicates.py` into a single `dex-import` CLI app using Typer.
- [ ] **Database Migrations:** Replace ad-hoc `ALTER TABLE` checks with a formal migration tool (e.g., Alembic) to manage `dex_contacts.db` schema evolution.
- [ ] **Advanced Normalization:**
    - [ ] Phone numbers: Use `phonenumbers` lib for E.164 parsing/formatting.
    - [ ] Social URLs: Normalize `linkedin.com/in/foo/` vs `linkedin.com/in/foo` vs `foo`.
- [ ] **Performance:** Add SQL indexes on `emails.email`, `phones.phone_number`, and `contacts.duplicate_group_id`.

## Mid Term (Usability and Tooling)

- [ ] **Bi-Directional Sync:** Implement the logic to push resolved merges (primary ID + combined fields) back to the Dex API via `PUT` or `POST /merge`.
- [ ] **Undo/Snapshot:** Create database snapshots before major operations (like bulk merging) to allow easy rollback.
- [ ] **CI/CD:** Add GitHub Actions workflow to run `make check` on push.
- [ ] **Structured Logging:** Add JSON file logging for sync history and error auditing.

## Data Enrichment (LinkedIn)

~64% of contacts are missing LinkedIn URLs. Approaches to find them:

- [ ] **LinkedIn Search URL Generator:** Generate pre-filled LinkedIn search URLs from name + company to speed up manual lookup.
- [ ] **Third-Party Enrichment APIs:** Integrate with Apollo.io (free tier), Clearbit, People Data Labs, or Proxycurl for bulk enrichment.
- [ ] **Google Search API:** Use Google Custom Search (`"name" site:linkedin.com/in`) to find profiles programmatically.
- [ ] **Email Domain → Company Matching:** Extract company from work email domains, then search LinkedIn by name + company.

## Long Term (Scale and Productization)

- [ ] **Weighted Scoring:** Replace hard thresholds with a weighted scoring system for auto-merges (e.g., Email match = 100pts, Name match = 50pts, same Company = 20pts).
- [ ] **Multi-Tenancy:** Support multiple configuration profiles (different API keys/DBs) for managing multiple Dex accounts.
- [ ] **Data Export:** Built-in export to CSV/Parquet for external analysis in Excel or Pandas.

## Data Intelligence & AI (Experimental)

- [ ] **Level 4 Deduplication:** Use local LLMs (e.g., via Ollama) to resolve ambiguous duplicates (e.g., "Bill Gates" vs "William H. Gates").
- [ ] **Smart Formatting:** Auto-correct name capitalization (ALL CAPS to Title Case) and standardize address formats.
- [ ] **Entity Extraction:** Parse unstructured text in `notes` to identify and extract new phone numbers or emails automatically.
- [ ] **Network Graph:** Generate visual graphs (using `networkx` + Graphviz/Mermaid) to visualize connection clusters.
