# Investigation Workbench

## Project Purpose
A **local, case-scoped incident investigation workbench** for human-led security investigations.

**What it does:**
- Ingests SIEM query results (Splunk, Kusto, CloudTrail, Okta) into local SQLite
- Normalizes events for correlation and timeline analysis
- Preserves full provenance and raw evidence
- Provides analyst UI for exploration and reasoning

**What it is NOT:** a full SIEM, alerting system, or bulk telemetry store.

---

## Project Structure

```
app/                    # Streamlit web UI
  main.py               # Entry point, case selector, page router
  state.py              # Session state management
  services/             # Data access layer (db, entities, graph, search, etc.)
  views/                # UI pages (timeline, entity_graph, bookmarks, etc.)

cli/                    # Typer CLI for data pipeline
  __main__.py           # CLI entry point
  commands.py           # init-case, add-run, ingest-all, export-timeline
  ingest.py             # Event parsing and normalization
  schema.sql            # SQLite schema (14 tables)
  mappers/              # Source-specific field mappers
    splunk.py, kusto.py, cloudtrail.py, okta.py, generic.py

cases/                  # Case workspaces (gitignored except demo)
  <case_id>/
    case.sqlite         # SQLite database
    raw/                # Append-only raw exports by source
    exports/            # Generated reports
    notes.md            # Investigation notes

sample_data/            # Example exports for testing
tests/                  # Smoke tests
```

---

## Commands

```bash
# Run the web UI
make run                          # or: streamlit run app/main.py

# CLI commands
python -m cli init-case <case_id>                    # Create new case
python -m cli add-run <case_id> --source splunk --file export.ndjson
python -m cli ingest-all <case_id>                   # Ingest all pending runs
python -m cli export-timeline <case_id> --fmt csv    # Export to CSV/Parquet

# Development
make test                         # Run tests
make lint                         # Run ruff linter
```

---

## Code Style

- **Python 3.9+**, 4-space indentation
- **Formatting/Linting:** Ruff
- **Naming:** `snake_case` for functions/variables, `PascalCase` for classes
- **Stack:** Streamlit (UI), Typer (CLI), SQLite (storage), Altair (charts)

---

## Design Principles
- **Case-first**: The primary unit of work is a case, not an index or tenant.
- **Working set, not warehouse**: Only investigation-relevant data is stored locally.
- **Provenance is mandatory**: Every event must be traceable to its source query.
- **Local-first**: No cloud dependencies; everything runs locally.
- **Human-in-the-loop**: The system assists analysts; it does not auto-decide.

---

## Architectural Invariants

**Do not violate:**
- Cases live under `cases/<case_id>/`
- Raw query outputs are **append-only** - never mutate or delete
- Normalized data must be reconstructible from raw + metadata
- Every event retains: `run_id`, source system, time window
- Timestamps stored in **UTC**
- SQLite is canonical for case metadata, provenance, and events
- Never silently drop events on ingest
- Schema drift OK: unknown fields go to `raw_json`, normalized columns stay stable

**Avoid introducing:** distributed systems, message queues, cloud databases, opaque binary formats

---

## UX Priorities
- Fast timelines with easy pivots by host/user/ip/hash
- Clear visibility into data coverage and gaps
- Drill-down from summary to raw evidence
- Feel like an **investigation workbench**, not a SOC dashboard

---

## Non-Goals
- Alerting or detection engineering
- Long-term log retention
- Multi-tenant RBAC
- Cloud ingestion pipelines
- Replacing enterprise SIEMs

---

## Guiding Principle
> Does this make it easier for a human investigator to understand scope, timeline, and impact across disparate log sources for a single case?

If no, reconsider the change.
