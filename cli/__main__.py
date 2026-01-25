from pathlib import Path
from typing import Optional

import typer

from cli import commands

app = typer.Typer(add_completion=False)


@app.command("init-case")
def init_case(case_id: str, title: Optional[str] = None) -> None:
    commands.init_case(case_id, title)
    typer.echo(f"Initialized case {case_id}")


@app.command("add-run")
def add_run(
    case_id: str,
    source: str = typer.Option(..., help="Source system name (splunk, kusto, firewall, etc.)"),
    query_name: str = typer.Option(...),
    query_text: Optional[str] = typer.Option(None),
    time_start: Optional[str] = typer.Option(None),
    time_end: Optional[str] = typer.Option(None),
    file: Path = typer.Option(..., exists=True, dir_okay=False, readable=True),
    executed_at: Optional[str] = typer.Option(None),
) -> None:
    run_id = commands.add_run(
        case_id=case_id,
        source=source,
        query_name=query_name,
        query_text=query_text,
        time_start=time_start,
        time_end=time_end,
        file_path=file,
        executed_at=executed_at,
    )
    typer.echo(f"Added run {run_id}")


@app.command("ingest-run")
def ingest_run(
    case_id: str,
    run_id: str,
    skip_errors: bool = typer.Option(False, "--skip-errors", help="Skip malformed rows"),
    lenient: bool = typer.Option(False, "--lenient", help="Only require event_ts and event_type"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed output"),
) -> None:
    """Ingest events from a specific query run."""
    result = commands.ingest_run(case_id, run_id, skip_errors=skip_errors, lenient=lenient)
    for line in commands.print_ingest_report(result, verbose=verbose):
        typer.echo(line)


@app.command("ingest-all")
def ingest_all(
    case_id: str,
    skip_errors: bool = typer.Option(False, "--skip-errors", help="Skip malformed rows"),
    lenient: bool = typer.Option(False, "--lenient", help="Only require event_ts and event_type"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed output"),
) -> None:
    """Ingest all pending query runs for a case."""
    results = commands.ingest_all(case_id, skip_errors=skip_errors, lenient=lenient)
    if not results:
        typer.echo("No pending runs to ingest")
        return
    for result in results:
        for line in commands.print_ingest_report(result, verbose=verbose):
            typer.echo(line)
    total = sum(r.events_ingested for r in results)
    skipped = sum(r.events_skipped for r in results)
    typer.echo(f"\nTotal: {total} events ingested, {skipped} skipped")


@app.command("preview")
def preview(
    case_id: str,
    source: str = typer.Option(..., "--source", help="Source system name"),
    file: Path = typer.Option(..., "--file", exists=True, dir_okay=False, readable=True),
    limit: int = typer.Option(5, "--limit", help="Number of rows to preview"),
) -> None:
    """Preview how a file would be ingested without committing."""
    result = commands.preview(case_id, source, file, limit=limit)
    for line in commands.print_preview(result):
        typer.echo(line)


@app.command("export-timeline")
def export_timeline(
    case_id: str,
    fmt: str = typer.Option("csv", help="csv or parquet"),
    output: Optional[Path] = typer.Option(None, dir_okay=False),
) -> None:
    path = commands.export_timeline(case_id, fmt, output)
    typer.echo(f"Exported {path}")


if __name__ == "__main__":
    app()
