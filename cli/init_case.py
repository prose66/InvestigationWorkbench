from typing import Optional

import typer

from cli import commands

app = typer.Typer(add_completion=False)


@app.command()
def main(case_id: str, title: Optional[str] = None) -> None:
    commands.init_case(case_id, title)
    typer.echo(f"Initialized case {case_id}")


if __name__ == "__main__":
    app()
