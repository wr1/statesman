"""CLI entry point for statesman."""

import typer
from statesman.core.base import Statesman

app = typer.Typer()


@app.command()
def check(
    workdir: str = typer.Option(..., "--workdir", "-w", help="Working directory"),
    config: str = typer.Option(..., "--config", "-c", help="Config file path"),
):
    """Check states in a workflow."""
    statesman = Statesman(workdir, config)
    typer.echo("State check completed.")


if __name__ == "__main__":
    app()
