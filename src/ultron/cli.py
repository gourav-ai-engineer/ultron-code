"""Command-line entry point for ULTRON CODE."""

import typer

app = typer.Typer(help="ULTRON CODE development orchestrator")


@app.command()
def status() -> None:
    """Show the initial orchestrator status."""
    typer.echo("ULTRON CODE v0.1.0")
    typer.echo("Mode: dry-run")
    typer.echo("Status: initialized")


if __name__ == "__main__":
    app()
