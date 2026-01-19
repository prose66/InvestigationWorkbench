import typer

from cli import commands

app = typer.Typer(add_completion=False)


@app.command()
def main(case_id: str) -> None:
    run_ids = commands.ingest_all(case_id)
    typer.echo(f"Ingested runs: {', '.join(run_ids) if run_ids else 'none'}")


if __name__ == "__main__":
    app()
