"""Command-line entry point for ULTRON CODE."""

from pathlib import Path

import typer

from .models import Phase, Project
from .orchestrator import Orchestrator
from .state import ProjectStateStore

app = typer.Typer(help="ULTRON CODE development orchestrator")


@app.command()
def status() -> None:
    """Show the current orchestrator status."""
    typer.echo("ULTRON CODE v0.2.0")
    typer.echo("Mode: dry-run")
    typer.echo("Status: orchestration engine available")


@app.command()
def init(
    name: str = typer.Option(..., prompt="Project name"),
    goal: str = typer.Option(..., prompt="Project goal"),
    state_path: Path = typer.Option(Path(".ultron/project.json")),
) -> None:
    """Create a project state file with starter phases."""
    project = Project(
        name=name,
        goal=goal,
        phases=[
            Phase(id="phase-1", title="Architecture", objective="Define the system architecture"),
            Phase(id="phase-2", title="Implementation", objective="Implement the first functional slice"),
            Phase(id="phase-3", title="Validation", objective="Run tests and verify acceptance criteria"),
        ],
    )
    ProjectStateStore(state_path).save(project)
    typer.echo(f"Project initialized: {state_path}")


@app.command()
def next_phase(state_path: Path = typer.Option(Path(".ultron/project.json"))) -> None:
    """Activate and display the next pending phase in dry-run mode."""
    store = ProjectStateStore(state_path)
    project = store.load()
    phase = Orchestrator(project).start_next_phase()
    if phase is None:
        typer.echo("No pending phases remain.")
        return
    store.save(project)
    typer.echo(f"Active phase: {phase.id} — {phase.title}")
    typer.echo(f"Objective: {phase.objective}")


if __name__ == "__main__":
    app()
