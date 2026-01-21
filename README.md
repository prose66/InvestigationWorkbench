# Investigation Workbench

> A local, case-scoped investigation tool for incident response analysts

[![Version](https://img.shields.io/badge/version-0.2.0-blue.svg)](VERSION)
[![Python](https://img.shields.io/badge/python-3.9+-green.svg)](requirements.txt)
[![License](https://img.shields.io/badge/license-MIT-lightgrey.svg)](LICENSE)

Investigation Workbench helps security analysts correlate events from multiple SIEM sources (Splunk, Kusto, CloudTrail, Okta, etc.) into a unified timeline for a single investigation case. All data stays local — no cloud dependencies.

---

## Table of Contents

- [Features](#features)
- [Screenshots](#screenshots)
- [Quick Start](#quick-start)
- [Usage Guide](#usage-guide)
- [CLI Reference](#cli-reference)
- [UI Pages](#ui-pages)
- [Project Structure](#project-structure)
- [Development](#development)

---

## Features

### 🔍 Investigation-Focused Design
- **Case-first workflow** — each investigation is an isolated workspace
- **Full provenance** — every event traces back to its source query
- **Raw data preserved** — append-only storage, database is rebuildable

### 📥 Flexible Ingestion
- **Multi-source support** — Splunk, Kusto/Sentinel, AWS CloudTrail, Okta, generic NDJSON/CSV
- **Auto field mapping** — source-specific mappers normalize timestamps and field names
- **Fault-tolerant** — `--skip-errors` mode logs bad rows without aborting
- **Duplicate detection** — warns if you add the same export twice

### 📊 Visual Analysis
- **Timeline Explorer** — filterable event timeline with time-based charts
- **Swimlane View** — activity lanes by host, user, IP, or event type
- **Entity Graph** — interactive network visualization of relationships
- **Entity Comparison** — side-by-side diff of two entities
- **Gap Detection** — highlights time periods with missing data

### 🔖 Analyst Workflow
- **Bookmarks** — save interesting events with notes
- **Timeline Markers** — annotate key moments in the investigation
- **Entity Notes & Aliases** — track known-good/bad entities
- **Global Search** — find events by keyword across all sources
- **CSV Export** — download filtered results from any view

---

## Screenshots

<!-- Add screenshots to docs/screenshots/ and uncomment these -->
<!--
### Case Overview
![Overview](docs/screenshots/overview.png)

### Timeline Explorer
![Timeline](docs/screenshots/timeline.png)

### Entity Graph
![Graph](docs/screenshots/entity-graph.png)

### Swimlane View
![Swimlane](docs/screenshots/swimlane.png)
-->

*Screenshots coming soon — run `make dev` to see the UI*

---

## Quick Start

### Option 1: Using Make (Recommended)

```bash
# Clone and enter the repo
git clone https://github.com/prose66/InvestigationWorkbench.git
cd InvestigationWorkbench

# Install dependencies and start
make install
make dev
```

### Option 2: Manual Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app/main.py
```

The app opens at `http://localhost:8501` with a preloaded demo case.

---

## Usage Guide

### Creating a New Case

```bash
# Initialize case workspace
python -m cli.init_case mycase --title "Phishing Investigation 2026-01"
```

This creates:
```
cases/mycase/
├── case.sqlite      # Event database
├── raw/             # Original exports (append-only)
├── exports/         # Generated reports
└── notes.md         # Investigation notes
```

### Adding Data

```bash
# Add a Splunk export
python -m cli.add_run mycase \
  --source splunk \
  --query-name "Failed logins last 24h" \
  --time-start 2026-01-19T00:00:00Z \
  --time-end 2026-01-20T00:00:00Z \
  --file ~/Downloads/splunk_export.ndjson

# Add a Kusto/Sentinel export
python -m cli.add_run mycase \
  --source kusto \
  --query-name "SigninLogs anomalies" \
  --time-start 2026-01-19T00:00:00Z \
  --time-end 2026-01-20T00:00:00Z \
  --file ~/Downloads/sentinel_results.csv
```

### Ingesting Events

```bash
# Ingest all pending runs
python -m cli.ingest_all mycase

# Or ingest a specific run
python -m cli.ingest_run mycase <run_id>

# Lenient mode (skip bad rows, log errors)
python -m cli.ingest_all mycase --lenient
```

### Launching the UI

```bash
make dev
# or
streamlit run app/main.py
```

Select your case from the sidebar dropdown.

---

## CLI Reference

| Command | Description |
|---------|-------------|
| `python -m cli.init_case <id>` | Create new case workspace |
| `python -m cli.add_run <id> --source <src> --file <path>` | Register query export |
| `python -m cli.ingest_run <id> <run_id>` | Ingest single run |
| `python -m cli.ingest_all <id>` | Ingest all pending runs |
| `python -m cli.export_timeline <id>` | Export events to CSV/Parquet |

### Common Flags

| Flag | Description |
|------|-------------|
| `--source` | Source system: `splunk`, `kusto`, `cloudtrail`, `okta`, `generic` |
| `--skip-errors` | Continue on parse errors (logs to `*_errors.ndjson`) |
| `--lenient` | Alias for `--skip-errors` |
| `--allow-duplicate` | Skip duplicate file hash check |
| `--format csv\|parquet` | Export format (default: csv) |

---

## UI Pages

### 📋 Case Overview
High-level stats: event counts, source distribution, time coverage, query run provenance.

### 📅 Timeline Explorer
- Filter by time range, source, event type, host, user, IP
- Click events to see full details and raw JSON
- Bookmark events, view provenance
- Export filtered results to CSV
- **Gap detection** shows data coverage blind spots

### 🏊 Swimlane Timeline
Lane-based visualization grouped by:
- Host
- User  
- Event Type
- Source System

Click any bar to drill down to those events.

### 🕸️ Entity Graph
Interactive network graph showing relationships between:
- Hosts ↔ Users ↔ IPs ↔ Processes ↔ File Hashes

Node size = event count. Edge thickness = co-occurrence strength.
Double-click to navigate to entity details.

### 🔬 Entity Comparison
Side-by-side analysis of two entities:
- Activity metrics and time ranges
- Event type overlap (common vs unique)
- Timeline comparison chart
- Outcome distribution

### 🔖 Bookmarks
Manage saved events with labels and analyst notes.

### 🔍 Search
Global keyword search across all event messages.

---

## Project Structure

```
├── app/                    # Streamlit UI
│   ├── main.py             # App entry point
│   ├── state.py            # Session state management
│   ├── services/           # Data access layer
│   │   ├── db.py           # SQLite helpers
│   │   ├── entities.py     # Entity queries
│   │   ├── graph.py        # Entity graph builder
│   │   ├── gaps.py         # Coverage gap detection
│   │   └── ...
│   └── views/              # UI pages
│       ├── overview.py
│       ├── timeline.py
│       ├── swimlane.py
│       ├── entity_graph.py
│       ├── entity_diff.py
│       └── ...
├── cli/                    # Command-line tools
│   ├── commands.py         # Typer CLI definitions
│   ├── ingest.py           # Event parsing/normalization
│   ├── mappers/            # Source-specific field mappers
│   │   ├── splunk.py
│   │   ├── kusto.py
│   │   ├── cloudtrail.py
│   │   └── okta.py
│   └── schema.sql          # Database schema
├── cases/                  # Case workspaces (gitignored except demo)
├── sample_data/            # Example exports for testing
├── schemas/                # Unified event schema docs
├── tests/                  # Smoke tests
├── Makefile                # Dev shortcuts
└── requirements.txt        # Python dependencies
```

---

## Development

### Make Commands

| Command | Description |
|---------|-------------|
| `make install` | Create venv and install dependencies |
| `make dev` | Run Streamlit development server |
| `make test` | Run pytest |
| `make lint` | Run ruff linter |
| `make format` | Auto-format code |
| `make clean` | Remove cache files |

### Adding a New Source Mapper

1. Create `cli/mappers/mysource.py`:
```python
from .base import BaseMapper

class MySourceMapper(BaseMapper):
    source_name = "mysource"
    
    def map_fields(self, row: dict) -> dict:
        return {
            "event_ts": row.get("timestamp"),
            "event_type": row.get("action"),
            "message": row.get("description"),
            # ... map other fields
        }
```

2. Register in `cli/mappers/__init__.py`

### Running Tests

```bash
make test
# or
pytest tests/ -v
```

---

## Notes

- All timestamps stored as **UTC ISO 8601** with `Z` suffix
- SQLite is the canonical datastore; Parquet export requires `pyarrow`
- Raw exports are **never modified** — delete `case.sqlite` and re-ingest to rebuild

---

## License

MIT
