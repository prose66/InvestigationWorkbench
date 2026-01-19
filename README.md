# Investigation Workbench (Local Prototype)

This repo is a minimal, local-only investigation workbench for incident response cases. It ingests Splunk/Kusto query exports in a unified schema, stores canonical events in SQLite, and provides a Streamlit UI for timeline and entity analysis. Raw artifacts remain append-only; the database is derived and rebuildable.

## What This Tool Does

- Collects query-run artifacts per case with provenance (run ID, query name, time window).
- Normalizes and deduplicates events into a canonical SQLite store.
- Provides analyst-friendly exploration: timeline, filters, and entity pivots.
- Exports a shareable timeline view to CSV or Parquet.

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

## Notes

- SQLite is the default datastore; Parquet export requires `pyarrow` if you select `--format parquet`.
- Event timestamps are stored as UTC ISO 8601 strings with `Z` suffix.
