import typer

from cli import commands

app = typer.Typer(add_completion=False)


@app.command()
def main(
    case_id: str,
    skip_errors: bool = typer.Option(False, "--skip-errors", help="Skip malformed rows instead of aborting"),
    lenient: bool = typer.Option(False, "--lenient", help="Only require event_ts and event_type"),
) -> None:
    """Ingest all pending query runs for a case."""
    results = commands.ingest_all(case_id, skip_errors=skip_errors, lenient=lenient)
    if not results:
        typer.echo("No pending runs to ingest")
        return
    
    total_ingested = sum(r.events_ingested for r in results)
    total_skipped = sum(r.events_skipped for r in results)
    
    typer.echo(f"Ingested {len(results)} runs ({total_ingested} events)")
    if total_skipped:
        typer.echo(f"Skipped {total_skipped} rows with errors", err=True)
    for result in results:
        status = "✓" if result.success else "⚠"
        typer.echo(f"  {status} {result.run_id}: {result.events_ingested} events")
        if result.events_skipped:
            typer.echo(f"    → {result.events_skipped} errors logged")


if __name__ == "__main__":
    app()
