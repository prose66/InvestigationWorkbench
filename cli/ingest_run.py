import typer

from cli import commands

app = typer.Typer(add_completion=False)


@app.command()
def main(
    case_id: str,
    run_id: str,
    skip_errors: bool = typer.Option(False, "--skip-errors", help="Skip malformed rows instead of aborting"),
    lenient: bool = typer.Option(False, "--lenient", help="Only require event_ts and event_type"),
) -> None:
    """Ingest events from a single query run."""
    result = commands.ingest_run(case_id, run_id, skip_errors=skip_errors, lenient=lenient)
    typer.echo(f"Ingested {result.events_ingested} events for run {run_id}")
    if result.events_skipped:
        typer.echo(f"Skipped {result.events_skipped} rows with errors", err=True)
        typer.echo(f"Errors logged to: cases/{case_id}/raw/.../{{run_id}}_errors.ndjson", err=True)


if __name__ == "__main__":
    app()
