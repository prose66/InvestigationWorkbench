from pathlib import Path
from typing import Optional

import typer

from cli import commands

app = typer.Typer(add_completion=False)


@app.command()
def main(
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


if __name__ == "__main__":
    app()
