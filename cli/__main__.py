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
    source: str = typer.Option(..., help="splunk or kusto"),
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
def ingest_run(case_id: str, run_id: str) -> None:
    count = commands.ingest_run(case_id, run_id)
    typer.echo(f"Ingested {count} events for run {run_id}")


@app.command("ingest-all")
def ingest_all(case_id: str) -> None:
    run_ids = commands.ingest_all(case_id)
    typer.echo(f"Ingested runs: {', '.join(run_ids) if run_ids else 'none'}")


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
