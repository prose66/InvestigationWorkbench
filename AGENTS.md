# Repository Guidelines

This repository is currently an empty workspace. The guidance below defines the expected layout and contribution standards until the project structure and tooling are established. Update sections once real paths, commands, and frameworks exist.

## Project Structure & Module Organization

- `src/`: primary application or library code (create if not present).
- `tests/` or `__tests__/`: automated tests aligned with modules.
- `assets/`: static files such as images, fixtures, or sample data.
- `scripts/`: developer utilities (build, release, lint helpers).
- `docs/`: architecture notes and decision records.

Example: `src/auth/session.ts` with tests in `tests/auth/session.test.ts`.

## Build, Test, and Development Commands

Define canonical commands in the root `README.md` once the stack is chosen. Common patterns:

- `npm run dev` or `make dev`: start local development server or watcher.
- `npm test` or `make test`: run the full test suite.
- `npm run build` or `make build`: produce production artifacts.

If environment variables are required, document them in `.env.example`.

## Coding Style & Naming Conventions

- Indentation: 2 spaces for JS/TS, 4 spaces for Python; follow the language norms you adopt.
- Naming: `camelCase` for variables/functions, `PascalCase` for types/classes, `kebab-case` for files.
- Formatting: standardize with a single formatter (e.g., Prettier, Black, gofmt).
- Linting: enforce with a linter (e.g., ESLint, Ruff, golangci-lint).

## Testing Guidelines

- Keep tests close to source structure and name as `<module>.test.<ext>` or `<module>_test.<ext>`.
- Prefer fast unit tests; add integration tests as needed.
- Track coverage targets in CI once a framework is selected.

## Commit & Pull Request Guidelines

- No Git history is present yet; use conventional, descriptive messages such as `feat: add session store`.
- Each PR should include:
  - a short summary of changes,
  - linked issue or rationale,
  - screenshots or logs for UI or behavior changes.

## Configuration & Security Tips

- Store secrets in environment variables; never commit `.env` files.
- Add `.gitignore` entries for build output, caches, and editor files.

# Agent Instructions

## Project Purpose
This repository implements a **local, case-scoped incident investigation workbench**.

It is designed to support **human-led investigations** by:
- ingesting *selected* SIEM query results (e.g., Splunk, Kusto) into a local datastore
- normalizing core event fields for correlation and timelines
- preserving full provenance and raw evidence
- providing an analyst-friendly UI for exploration and reasoning

This project is **not** a full SIEM, **not** an alerting system, and **not** intended to ingest all telemetry by default.

---

## Core Design Principles
- **Case-first**: The primary unit of work is a case, not an index or tenant.
- **Working set, not warehouse**: Only investigation-relevant data is stored locally.
- **Provenance is mandatory**: Every event must be traceable to its source query.
- **Local-first**: No cloud dependencies; everything runs locally.
- **Human-in-the-loop**: The system assists analysts; it does not auto-decide.

---

## Architectural Invariants (Do Not Violate)
- Each case lives under `cases/<case_id>/`
- Raw query outputs are **append-only** and never mutated
- Normalized data is **derived** and must be reconstructible from raw data + metadata
- Every event must retain:
  - `run_id`
  - source (splunk, kusto, etc.)
  - time window of collection
- Timestamps are stored and queried in **UTC**
- SQLite is the canonical store for:
  - case metadata
  - query provenance
  - normalized events
- DuckDB/Parquet may be used **optionally** for large datasets, but must not replace SQLite for case metadata

---

## Data Handling Rules
- Do not delete or overwrite raw evidence files
- Do not silently drop events on ingest
- Schema drift is tolerated:
  - unknown fields may live only in `raw_json`
  - normalized columns remain stable
- Deduplication must be explainable and reversible
- The database file may be regenerated from raw data if needed

---

## Technology Choices
Preferred (unless there is a strong reason otherwise):
- Python 3.11+
- SQLite (sqlite3 or SQLAlchemy)
- DuckDB + Parquet (optional, for large datasets)
- Typer or Click for CLI tooling
- Streamlit for the primary UI
- Altair / Vega-Lite for visualizations

Avoid introducing:
- distributed systems
- message queues
- cloud-managed databases
- opaque binary formats without justification

---

## User Experience Intent
The UX should prioritize:
- fast timelines
- easy pivots by host/user/ip/hash
- clear visibility into data coverage and gaps
- easy drill-down from summary → raw evidence

The UI should feel like an **investigation workbench**, not a dashboard or SOC console.

---

## AI Usage Constraints
- AI-generated queries or analysis must be:
  - inspectable
  - editable
  - explicitly executed by the user
- No autonomous data modification
- No background actions without user intent
- AI outputs should preserve analyst trust and explainability

---

## Non-Goals (Explicit)
- Alerting or detection engineering
- Long-term log retention
- Multi-tenant RBAC
- Cloud ingestion pipelines
- Replacing enterprise SIEMs

---

## Guiding Question for All Changes
> Does this make it easier for a human investigator to understand scope, timeline, and impact across disparate log sources for a single case?

If the answer is no, reconsider the change.
