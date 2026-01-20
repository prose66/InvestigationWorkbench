# Investigation Workbench (Local Prototype)

This repo is a minimal, local-only investigation workbench for incident response cases. It ingests query exports in a unified schema, stores canonical events in SQLite, and provides a Streamlit UI for timeline, entity, and swimlane analysis. Raw artifacts remain append-only; the database is derived and rebuildable.

## What This Tool Does

- Collects query-run artifacts per case with provenance (run ID, query name, time window).
- Normalizes and deduplicates events into a canonical SQLite store with extended, optional fields.
- Provides analyst-friendly exploration: timeline, swimlane view, filters, and entity pivots.
- Preserves unknown tool-specific fields in `extras_json` and `event_fields` for sparse data.
- Exports a shareable timeline view to CSV or Parquet.

## Demo Data Included

This repo includes a prebuilt demo case in `cases/demo/` and synthetic exports in `sample_data/`.
You can run the UI immediately after installing dependencies without ingesting anything.

## Quickstart

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

python -m cli.init_case demo --title "Demo Case"
python -m cli.add_run demo --source splunk --query-name "Splunk Demo" --time-start 2024-07-01T12:00:00Z --time-end 2024-07-01T12:15:00Z --file sample_data/splunk.ndjson
python -m cli.add_run demo --source kusto --query-name "Kusto Demo" --time-start 2024-07-01T12:00:00Z --time-end 2024-07-01T12:15:00Z --file sample_data/kusto.ndjson
python -m cli.ingest_all demo

streamlit run app/main.py
```

## Using Your Own Data

1) Create a case workspace:
```bash
python -m cli.init_case <case_id> --title "Case Title"
```

2) Add query exports (NDJSON or CSV) with unified fields:
```bash
python -m cli.add_run <case_id> --source splunk --query-name "My Query" --time-start 2024-07-01T00:00:00Z --time-end 2024-07-02T00:00:00Z --file /path/to/export.ndjson
```

3) Ingest into SQLite:
```bash
python -m cli.ingest_all <case_id>
```

4) Launch the UI:
```bash
streamlit run app/main.py
```

## Repository Layout

- `cases/<case_id>/`: per-case workspace and SQLite datastore.
- `cli/`: ingestion and export utilities.
- `app/`: Streamlit UI.
- `schemas/`: unified schema documentation.
- `sample_data/`: small demo exports.
- `tests/`: smoke tests.

## CLI Commands

- `python -m cli.init_case <case_id>`: create case folders and initialize SQLite.
- `python -m cli.add_run <case_id> --source splunk|kusto --query-name ... --file <path>`: register a query run and copy raw data.
- `python -m cli.ingest_run <case_id> <run_id>`: parse and ingest a single run.
- `python -m cli.ingest_all <case_id>`: ingest all pending runs.
- `python -m cli.export_timeline <case_id> --format csv|parquet`: export ordered events.

## Streamlit UI Features

- Case Overview: counts, time coverage, and query run provenance.
- Timeline Explorer: filters by time/source/event_type/entities with provenance drill-down.
- Swimlane Timeline: lane-by-lane activity view with click-to-filter.
- Entity Page: first/last seen, related entities, interesting events, notes/tags, and coverage.

## Notes

- SQLite is the default datastore; Parquet export requires `pyarrow` if you select `--format parquet`.
- Event timestamps are stored as UTC ISO 8601 strings with `Z` suffix.
