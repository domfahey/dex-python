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

- [ ] **Unified CLI:** Consolidate `sync_with_integrity.py`, `flag_duplicates.py`, and `review_duplicates.py` into a single `dex-python` CLI app using Typer.
- [ ] **Database Migrations:** Replace ad-hoc `ALTER TABLE` checks with a formal migration tool (e.g., Alembic) to manage `dex_contacts.db` schema evolution.
- [ ] **Advanced Normalization:**
    - [ ] Phone numbers: Use `phonenumbers` lib for E.164 parsing/formatting.
    - [ ] Social URLs: Normalize `linkedin.com/in/foo/` vs `linkedin.com/in/foo` vs `foo`.
- [ ] **Performance:** Add SQL indexes on `emails.email`, `phones.phone_number`, and `contacts.duplicate_group_id`.
- [ ] **Pydantic Hardening:** Model nested response fields, exclude path IDs from update payloads, accept `datetime` inputs with JSON serialization, relax `changes` typing, avoid strict datetime parsing on response models, and consider `extra="forbid"` on request models.

## Mid Term (Usability and Tooling)

- [ ] **Bi-Directional Sync:** Implement the logic to push resolved merges (primary ID + combined fields) back to the Dex API via `PUT` or `POST /merge`.
- [ ] **Undo/Snapshot:** Create database snapshots before major operations (like bulk merging) to allow easy rollback.
- [ ] **CI/CD:** Add GitHub Actions workflow to run `make check` on push.
- [ ] **Structured Logging:** Add JSON file logging for sync history and error auditing.

## Documentation & Onboarding

- [x] **Getting Started Guide:** Add install, config, and verification quick start docs.
- [ ] **Alternate Install Paths:** Document `pipx`/`pip`, Poetry, and Conda install options alongside `uv`.
- [x] **Health Check:** Add a minimal setup verification flow (first API call) with expected output.
- [ ] **Troubleshooting Guide:** Cover common errors (401, 429, `.env` loading) with remedies.
- [ ] **First Tasks Examples:** Provide create/update/delete and pagination examples, plus an async snippet.
- [x] **Configuration Tips:** Explain environment variables, base URL overrides, and retry guidance.
- [ ] **SQLite Workflow Tips:** Add example queries against `output/dex_contacts.db` and a safe dedupe checklist.
- [x] **Name Parsing Guide:** Document probablepeople fields, best practices, and example queries.

## Data Enrichment (LinkedIn)

~64% of contacts are missing LinkedIn URLs. Approaches to find them:

- [ ] **LinkedIn Search URL Generator:** Generate pre-filled LinkedIn search URLs from name + company to speed up manual lookup.
- [ ] **Third-Party Enrichment APIs:** Integrate with Apollo.io (free tier), Clearbit, People Data Labs, or Proxycurl for bulk enrichment.
- [ ] **Google Search API:** Use Google Custom Search (`"name" site:linkedin.com/in`) to find profiles programmatically.
- [ ] **Email Domain → Company Matching:** Extract company from work email domains, then search LinkedIn by name + company.

## Contact Enrichment (General)

- [ ] **Company Enrichment:** Derive company from email domain; enrich with industry, size, HQ location, and website.
- [ ] **Title Normalization:** Standardize titles to a controlled taxonomy (e.g., VP Eng -> VP Engineering).
- [ ] **Seniority Inference:** Infer seniority from title keywords and organization size.
- [ ] **Location Enrichment:** Parse city/state/country from free-text fields; optionally geocode.
- [ ] **Address Parsing Library:** Evaluate `usaddress` for structured US address parsing.
- [ ] **Census Geocoding API:** Evaluate the free U.S. Census geocoder to standardize and geocode US addresses.
- [ ] **Timezone Inference:** Infer timezone from location fields to power reminders.
- [ ] **Phone Enrichment:** Normalize to E.164, infer country from locale/address, validate with carrier lookups.
- [x] **Name Parsing:** Split full names into components and store structured output in SQLite.
- [ ] **Phonetic Keys:** Add phonetic keys for improved name matching.
- [x] **Name Parsing Library:** Integrate `probablepeople` for structured name parsing and normalization.
- [ ] **Social Handle Discovery:** Infer likely GitHub/Twitter/LinkedIn handles from name + company patterns.
- [ ] **Company Logos:** Fetch and cache company logos for UI display.
- [ ] **Relationship Signals:** Parse notes for "met at", "introduced by", "works with" to build network edges.
- [ ] **Last-Activity Signals:** Compute last touch based on latest note/reminder.
- [ ] **Email Validity:** Run syntax + MX checks (no sending).
- [ ] **Personalization Tokens:** Derive nicknames and pronoun hints from notes/signatures.
- [ ] **Lifecycle Stage Classification:** Classify contacts (lead/customer/partner) based on tags and notes.

## Long Term (Scale and Productization)

- [ ] **Weighted Scoring:** Replace hard thresholds with a weighted scoring system for auto-merges (e.g., Email match = 100pts, Name match = 50pts, same Company = 20pts).
- [ ] **Multi-Tenancy:** Support multiple configuration profiles (different API keys/DBs) for managing multiple Dex accounts.
- [ ] **Data Export:** Built-in export to CSV/Parquet for external analysis in Excel or Pandas.

## Data Intelligence & AI (Experimental)

- [ ] **Level 4 Deduplication:** Use local LLMs (e.g., via Ollama) to resolve ambiguous duplicates (e.g., "Bill Gates" vs "William H. Gates").
- [ ] **Smart Formatting:** Auto-correct name capitalization (ALL CAPS to Title Case) and standardize address formats.
- [ ] **Entity Extraction:** Parse unstructured text in `notes` to identify and extract new phone numbers or emails automatically.
- [ ] **Network Graph:** Generate visual graphs (using `networkx` + Graphviz/Mermaid) to visualize connection clusters.
