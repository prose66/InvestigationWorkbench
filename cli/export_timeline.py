from pathlib import Path
from typing import Optional

import typer

from cli import commands

app = typer.Typer(add_completion=False)


@app.command()
def main(
    case_id: str,
    fmt: str = typer.Option("csv", help="csv or parquet"),
    output: Optional[Path] = typer.Option(None, dir_okay=False),
) -> None:
    path = commands.export_timeline(case_id, fmt, output)
    typer.echo(f"Exported {path}")


if __name__ == "__main__":
    app()
