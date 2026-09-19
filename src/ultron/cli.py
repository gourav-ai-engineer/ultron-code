""""Command-line entry point for ULTRON CODE."""

from pathlib import Path

import typer

from .approval import ApprovalGateway, ApprovalStatus
from .executor import ActionExecutor, ExecutionDeniedError
from .models import Phase, Project
from .orchestrator import Orchestrator
from .planner import ProjectPlanner
from .provider_runtime import (
    AnthropicModelsAdapter,
    CursorCloudRunAdapter,
    OpenAIResponseAdapter,
    ProviderRequestError,
)
from .providers import MockProvider
from .safety import SafetyPolicy
from .state import ProjectStateStore
from .workflow import WorkflowEngine
from .workspace import WorkspaceObserver

app = typer.Typer(help="ULTRON CODE development orchestrator")


@app.command()
def status() -> None:
    """Show the current orchestrator status."""
    typer.echo("ULTRON CODE v0.7.0")
    typer.echo("Mode: dry-run by default")
    typer.echo(
        "Status: planning, orchestration, safety, approvals, workflow, and provider runtime available"
    )


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
def provider_status(
    provider: str = typer.Option(..., prompt="Provider (chatgpt/claude/cursor)"),
    response_id: str | None = typer.Option(None, help="OpenAI response ID"),
    agent_id: str | None = typer.Option(None, help="Cursor Cloud Agent ID"),
    run_id: str | None = typer.Option(None, help="Cursor Cloud Agent run ID"),
) -> None:
    """Probe one configured provider through its read-only runtime adapter."""
    normalized = provider.strip().lower()

    try:
        if normalized == "chatgpt":
            if response_id is None:
                raise typer.BadParameter("response_id is required for chatgpt.")
            adapter = OpenAIResponseAdapter(response_id)
        elif normalized == "claude":
            adapter = AnthropicModelsAdapter()
        elif normalized == "cursor":
            if agent_id is None or run_id is None:
                raise typer.BadParameter("agent_id and run_id are required for cursor.")
            adapter = CursorCloudRunAdapter(agent_id, run_id)
        else:
            raise typer.BadParameter("Use chatgpt, claude, or cursor.")

        health = adapter.health_check()
        typer.echo(f"Provider: {health.provider.value}")
        typer.echo(f"Health: {health.status.value}")
        typer.echo(f"Message: {health.message}")

        if health.status.value == "available":
            try:
                snapshot = adapter.snapshot()
            except ProviderRequestError as exc:
                typer.echo(f"Snapshot unavailable: {exc}")
                raise typer.Exit(code=1) from exc
            typer.echo(f"Session: {snapshot.session_id or 'n/a'}")
            typer.echo(f"Summary: {snapshot.summary}")
            typer.echo(f"Progress: {snapshot.progress if snapshot.progress is not None else 'n/a'}")
    except ProviderRequestError as exc:
        typer.echo(f"Provider unavailable: {exc}")
        raise typer.Exit(code=1) from exc


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


@app.command()
def execute(
    action: str = typer.Option(..., prompt="Allowlisted action"),
    workspace: Path = typer.Option(Path(".")),
    live: bool = typer.Option(
        False,
        "--live",
        help="Execute the allowlisted action. Without --live, dry-run blocks execution.",
    ),
    approval_id: str | None = typer.Option(None, "--approval-id"),
    approvals_path: Path = typer.Option(Path(".ultron/approvals.json")),
) -> None:
    """Evaluate and optionally execute one allowlisted action."""
    approval = None
    if approval_id is not None:
        approval = ApprovalGateway(approvals_path).get(approval_id)

    executor = ActionExecutor(
        workspace,
        safety_policy=SafetyPolicy(dry_run=not live),
    )

    try:
        result = executor.execute(action, approval=approval)
    except ExecutionDeniedError as exc:
        typer.echo(f"Execution denied: {exc}")
        raise typer.Exit(code=1) from exc

    typer.echo(f"Correlation ID: {result.correlation_id}")
    typer.echo(f"Exit code: {result.return_code}")
    typer.echo(f"Timed out: {result.timed_out}")
    if result.stdout:
        typer.echo("STDOUT:")
        typer.echo(result.stdout.rstrip())
    if result.stderr:
        typer.echo("STDERR:")
        typer.echo(result.stderr.rstrip())


@app.command()
def workflow_run(
    workspace: Path = typer.Option(Path(".")),
    state_path: Path = typer.Option(Path(".ultron/project.json")),
    provider_summary: str = typer.Option("No activity recorded."),
    progress: float | None = typer.Option(None, min=0.0, max=1.0),
    session_id: str | None = typer.Option(None),
    action: str | None = typer.Option(
        None,
        help="Optional explicitly supplied allowlisted action to execute after observation.",
    ),
    live: bool = typer.Option(
        False,
        "--live",
        help="Permit controlled execution of the supplied action.",
    ),
    approval_id: str | None = typer.Option(None, "--approval-id"),
    approvals_path: Path = typer.Option(Path(".ultron/approvals.json")),
) -> None:
    """Run one end-to-end observation cycle and optionally execute an explicit action."""
    try:
        project = ProjectStateStore(state_path).load()
        has_active_phase = project.active_phase_id is not None
    except FileNotFoundError:
        has_active_phase = False

    provider = MockProvider(
        summary=provider_summary,
        progress=progress,
        session_id=session_id,
    )
    executor = (
        ActionExecutor(
            workspace,
            safety_policy=SafetyPolicy(dry_run=not live),
        )
        if action is not None
        else None
    )
    engine = WorkflowEngine(WorkspaceObserver(workspace), executor=executor)
    run = engine.observe(provider, has_active_phase=has_active_phase)

    typer.echo(f"Run ID: {run.run_id}")
    typer.echo(f"Provider: {run.provider.provider.value}")
    typer.echo(f"Progress state: {run.assessment.state.value}")
    typer.echo(f"Decision: {run.decision.kind.value}")
    typer.echo(f"Rationale: {run.decision.rationale}")

    if action is None:
        return

    approval = None
    if approval_id is not None:
        approval = ApprovalGateway(approvals_path).get(approval_id)

    try:
        completed = engine.execute(run, action, approval=approval)
    except ExecutionDeniedError as exc:
        typer.echo(f"Execution denied: {exc}")
        raise typer.Exit(code=1) from exc

    if completed.execution is None:
        return
    typer.echo(f"Execution correlation ID: {completed.execution.correlation_id}")
    typer.echo(f"Exit code: {completed.execution.return_code}")
    typer.echo(f"Timed out: {completed.execution.timed_out}")


if __name__ == "__main__":
    app()
