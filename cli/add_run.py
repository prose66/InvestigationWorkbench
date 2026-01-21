from pathlib import Path
from typing import Optional

import typer

from cli import commands

app = typer.Typer(add_completion=False)


@app.command()
def main(
    case_id: str,
    source: str = typer.Option(..., help="Source system (splunk, kusto, okta, aws, etc.)"),
    query_name: str = typer.Option(..., help="Human-readable query name"),
    query_text: Optional[str] = typer.Option(None, help="Optional query text"),
    time_start: Optional[str] = typer.Option(None, help="Query time range start (ISO8601)"),
    time_end: Optional[str] = typer.Option(None, help="Query time range end (ISO8601)"),
    file: Path = typer.Option(..., exists=True, dir_okay=False, readable=True, help="Path to export file"),
    executed_at: Optional[str] = typer.Option(None, help="When the query was executed (ISO8601)"),
    allow_duplicate: bool = typer.Option(False, "--allow-duplicate", help="Allow adding duplicate files"),
) -> None:
    """Add a query run export to a case."""
    try:
        run_id = commands.add_run(
            case_id=case_id,
            source=source,
            query_name=query_name,
            query_text=query_text,
            time_start=time_start,
            time_end=time_end,
            file_path=file,
            executed_at=executed_at,
            allow_duplicate=allow_duplicate,
        )
        typer.echo(f"Added run {run_id}")
    except ValueError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
