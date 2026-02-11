# Copilot Instructions — Investigation Workbench

This is a local, case-scoped incident investigation workbench for human-led security investigations.

## Architecture
- **Backend**: FastAPI (`api/`) with SQLite per case
- **Frontend**: React/Next.js (`web/`)
- **CLI**: Typer (`cli/`) for data pipeline (ingest, normalize, export)
- **Storage**: SQLite at `cases/<case_id>/case.sqlite`

## Key rules
- Timestamps in UTC
- Raw data is append-only
- Every event must retain `run_id`, source system, time window
- Unknown fields go to `raw_json`
- No cloud dependencies, distributed systems, or message queues
- Python: snake_case, PascalCase classes, Ruff for linting
- The guiding question: does this help a human investigator understand scope, timeline, and impact?
