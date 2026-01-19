import typer

from cli import commands

app = typer.Typer(add_completion=False)


@app.command()
def main(case_id: str, run_id: str) -> None:
    count = commands.ingest_run(case_id, run_id)
    typer.echo(f"Ingested {count} events for run {run_id}")


if __name__ == "__main__":
    app()
