""""Command-line entry point for ULTRON CODE."""

from pathlib import Path

import typer

from .approval import ApprovalGateway, ApprovalStatus
from .models import Phase, Project
from .orchestrator import Orchestrator
from .planner import ProjectPlanner
from .safety import SafetyPolicy
from .state import ProjectStateStore

app = typer.Typer(help="ULTRON CODE development orchestrator")


@app.command()
def status() -> None:
    """Show the current orchestrator status."""
    typer.echo("ULTRON CODE v0.4.0")
    typer.echo("Mode: dry-run")
    typer.echo("Status: planning, orchestration, safety, and approvals available")


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
def plan(
    name: str = typer.Option(..., prompt="Project name"),
    goal: str = typer.Option(..., prompt="Project goal"),
    technologies: str = typer.Option("", help="Comma-separated technologies or keywords"),
    state_path: Path = typer.Option(Path(".ultron/project.json")),
) -> None:
    """Generate and save a deterministic project plan."""
    technology_list = [item.strip() for item in technologies.split(",") if item.strip()]
    project = ProjectPlanner().create_plan(name, goal, technology_list)
    ProjectStateStore(state_path).save(project)
    typer.echo(f"Plan created with {len(project.phases)} phases: {state_path}")


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


@app.command()
def approval_request(
    action: str = typer.Option(..., prompt="Action requiring approval"),
    rationale: str = typer.Option(..., prompt="Rationale"),
    approvals_path: Path = typer.Option(Path(".ultron/approvals.json")),
) -> None:
    """Create an approval request for a safety-classified action."""
    safety_decision = SafetyPolicy(dry_run=True).evaluate(action)
    if safety_decision.risk.value != "requires_approval":
        typer.echo(f"Approval request not created: {safety_decision.reason}")
        raise typer.Exit(code=1)

    request = ApprovalGateway(approvals_path).request(safety_decision, rationale)
    typer.echo(f"Approval request: {request.request_id}")
    typer.echo(f"Status: {request.status.value}")


@app.command()
def approval_list(
    approvals_path: Path = typer.Option(Path(".ultron/approvals.json")),
) -> None:
    """List pending approval requests."""
    requests = ApprovalGateway(approvals_path).pending()
    if not requests:
        typer.echo("No pending approval requests.")
        return
    for request in requests:
        typer.echo(f"{request.request_id} | {request.risk.value} | {request.action}")
        typer.echo(f"  Rationale: {request.rationale}")


@app.command()
def approval_resolve(
    request_id: str = typer.Option(..., prompt="Approval request ID"),
    status: str = typer.Option(..., prompt="Resolution (approved/rejected/deferred)"),
    note: str = typer.Option(""),
    approvals_path: Path = typer.Option(Path(".ultron/approvals.json")),
) -> None:
    """Resolve a pending approval request explicitly."""
    try:
        resolution = ApprovalStatus(status)
    except ValueError as exc:
        raise typer.BadParameter("Use approved, rejected, or deferred.") from exc

    request = ApprovalGateway(approvals_path).resolve(request_id, resolution, note)
    typer.echo(f"Request: {request.request_id}")
    typer.echo(f"Status: {request.status.value}")


if __name__ == "__main__":
    app()
