"""Command-line entry point for ULTRON CODE."""

from pathlib import Path

import typer

from .approval import ApprovalGateway, ApprovalStatus
from .control import ControlStore
from .executor import ActionExecutor, ExecutionDeniedError
from .loop import LoopConfig, WorkflowLoop
from .models import Phase, Project
from .orchestrator import Orchestrator
from .planner import ProjectPlanner
from .provider_registry import ProviderRegistry
from .provider_runtime import ProviderRequestError
from .providers import ProviderAdapter
from .runtime import UltronRuntime
from .safety import SafetyPolicy
from .settings import UltronSettings
from .state import ProjectStateStore
from .workflow import WorkflowEngine
from .workspace import WorkspaceObserver

app = typer.Typer(help="ULTRON CODE development orchestrator")


def _provider_kwargs(
    provider: str,
    response_id: str | None,
    agent_id: str | None,
    provider_run_id: str | None,
    summary: str,
    progress: float | None,
    session_id: str | None,
) -> dict[str, object]:
    normalized = provider.strip().lower()
    if normalized == "mock":
        return {
            "summary": summary,
            "progress": progress,
            "session_id": session_id,
        }
    if normalized == "chatgpt":
        if response_id is None:
            raise typer.BadParameter("response_id is required for chatgpt.")
        return {"response_id": response_id}
    if normalized == "claude":
        return {}
    if normalized == "cursor":
        if agent_id is None or provider_run_id is None:
            raise typer.BadParameter(
                "agent_id and provider_run_id are required for cursor."
            )
        return {"agent_id": agent_id, "run_id": provider_run_id}
    raise typer.BadParameter("Use mock, chatgpt, claude, or cursor.")


def _build_provider(
    registry: ProviderRegistry,
    provider: str,
    response_id: str | None = None,
    agent_id: str | None = None,
    provider_run_id: str | None = None,
    summary: str = "No activity recorded.",
    progress: float | None = None,
    session_id: str | None = None,
) -> ProviderAdapter:
    kwargs = _provider_kwargs(
        provider,
        response_id,
        agent_id,
        provider_run_id,
        summary,
        progress,
        session_id,
    )
    return registry.create(provider.strip().lower(), **kwargs)


@app.command()
def status() -> None:
    """Show the current orchestrator status."""
    typer.echo("ULTRON CODE v0.9.0")
    typer.echo("Mode: dry-run by default")
    typer.echo(
        "Status: planning, workflow, provider registry, approvals, controls, "
        "automation, API, and controlled execution available"
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
            Phase(
                id="phase-2",
                title="Implementation",
                objective="Implement the first functional slice",
            ),
            Phase(
                id="phase-3",
                title="Validation",
                objective="Run tests and verify acceptance criteria",
            ),
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
    provider: str = typer.Option(..., prompt="Provider (chatgpt/claude/cursor/mock)"),
    response_id: str | None = typer.Option(None, help="OpenAI response ID"),
    agent_id: str | None = typer.Option(None, help="Cursor Cloud Agent ID"),
    provider_run_id: str | None = typer.Option(None, help="Cursor Cloud Agent run ID"),
) -> None:
    """Probe one registered provider through its read-only runtime adapter."""
    registry = ProviderRegistry()
    try:
        adapter = _build_provider(
            registry,
            provider,
            response_id=response_id,
            agent_id=agent_id,
            provider_run_id=provider_run_id,
        )
        health = adapter.health_check()
        typer.echo(f"Provider: {health.provider.value}")
        typer.echo(f"Health: {health.status.value}")
        typer.echo(f"Message: {health.message}")

        if health.status.value != "available":
            return

        snapshot = adapter.snapshot()
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
    correlation_id: str | None = typer.Option(None, help="Workflow run correlation ID"),
) -> None:
    """Create an approval request for a safety-classified action."""
    safety_decision = SafetyPolicy(dry_run=True).evaluate(action)
    if safety_decision.risk.value != "requires_approval":
        typer.echo(f"Approval request not created: {safety_decision.reason}")
        raise typer.Exit(code=1)

    request = ApprovalGateway(approvals_path).request(
        safety_decision,
        rationale,
        correlation_id=correlation_id,
    )
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
    provider: str = typer.Option("mock", help="Provider: mock, chatgpt, claude, or cursor"),
    provider_summary: str = typer.Option("No activity recorded."),
    progress: float | None = typer.Option(None, min=0.0, max=1.0),
    session_id: str | None = typer.Option(None, help="Mock provider session ID"),
    response_id: str | None = typer.Option(None, help="OpenAI response ID"),
    agent_id: str | None = typer.Option(None, help="Cursor Cloud Agent ID"),
    provider_run_id: str | None = typer.Option(None, help="Cursor Cloud Agent run ID"),
    action: str | None = typer.Option(
        None,
        help="Optional explicitly supplied allowlisted action to execute after observation.",
    ),
    live: bool = typer.Option(False, "--live", help="Permit controlled execution."),
    approval_id: str | None = typer.Option(None, "--approval-id"),
    approvals_path: Path = typer.Option(Path(".ultron/approvals.json")),
) -> None:
    """Run one provider-backed observation cycle and optionally execute an explicit action."""
    try:
        project = ProjectStateStore(state_path).load()
    except FileNotFoundError:
        project = None

    has_active_phase = project is not None and project.active_phase_id is not None

    registry = ProviderRegistry()
    try:
        selected_provider = _build_provider(
            registry,
            provider,
            response_id=response_id,
            agent_id=agent_id,
            provider_run_id=provider_run_id,
            summary=provider_summary,
            progress=progress,
            session_id=session_id,
        )
    except (ProviderRequestError, ValueError) as exc:
        typer.echo(f"Provider configuration error: {exc}")
        raise typer.Exit(code=1) from exc

    executor = (
        ActionExecutor(workspace, safety_policy=SafetyPolicy(dry_run=not live))
        if action is not None
        else None
    )
    engine = WorkflowEngine(WorkspaceObserver(workspace), executor=executor)
    phase = None
    if project is not None and project.active_phase_id is not None:
        phase = next(
            (item for item in project.phases if item.id == project.active_phase_id),
            None,
        )

    try:
        run = engine.observe(
            selected_provider,
            has_active_phase=has_active_phase,
            phase=phase,
        )
    except ProviderRequestError as exc:
        typer.echo(f"Provider observation failed: {exc}")
        raise typer.Exit(code=1) from exc

    typer.echo(f"Run ID: {run.run_id}")
    typer.echo(f"Provider: {run.provider.provider.value}")
    typer.echo(f"Progress state: {run.assessment.state.value}")
    typer.echo(f"Decision: {run.decision.kind.value}")
    typer.echo(f"Rationale: {run.decision.rationale}")
    typer.echo("NEXT PROMPT:")
    typer.echo(run.prompt.prompt)

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


@app.command()
def control_stop(
    control_path: Path = typer.Option(Path(".ultron/control.json")),
    reason: str = typer.Option("Operator requested emergency stop."),
) -> None:
    """Enable the persistent emergency stop."""
    state = ControlStore(control_path).set(emergency_stop=True, reason=reason)
    typer.echo(f"Emergency stop: {state.emergency_stop}")
    typer.echo(f"Reason: {state.reason}")


@app.command()
def control_clear(
    control_path: Path = typer.Option(Path(".ultron/control.json")),
) -> None:
    """Clear the persistent emergency stop and pause state."""
    state = ControlStore(control_path).set(emergency_stop=False, paused=False, reason="")
    typer.echo(f"Emergency stop: {state.emergency_stop}")
    typer.echo(f"Paused: {state.paused}")


@app.command()
def control_pause(
    control_path: Path = typer.Option(Path(".ultron/control.json")),
    reason: str = typer.Option("Operator paused runtime."),
) -> None:
    """Pause future workflow-loop iterations."""
    state = ControlStore(control_path).set(paused=True, reason=reason)
    typer.echo(f"Paused: {state.paused}")


@app.command()
def control_resume(
    control_path: Path = typer.Option(Path(".ultron/control.json")),
) -> None:
    """Resume workflow-loop iterations without changing emergency-stop state."""
    current = ControlStore(control_path).get()
    if current.emergency_stop:
        typer.echo("Emergency stop remains active; use control-clear first.")
        raise typer.Exit(code=1)
    state = ControlStore(control_path).set(paused=False, reason="")
    typer.echo(f"Paused: {state.paused}")


@app.command()
def run_loop(
    provider: str = typer.Option("mock"),
    workspace: Path = typer.Option(Path(".")),
    state_path: Path = typer.Option(Path(".ultron/project.json")),
    control_path: Path = typer.Option(Path(".ultron/control.json")),
    runs_path: Path = typer.Option(Path(".ultron/runs.jsonl")),
    interval_seconds: float = typer.Option(10.0, min=0.1),
    max_iterations: int = typer.Option(1, min=0),
    provider_summary: str = typer.Option("No activity recorded."),
    progress: float | None = typer.Option(None, min=0.0, max=1.0),
) -> None:
    """Run repeated provider observations until stopped, paused, or bounded limit."""
    registry = ProviderRegistry()
    selected_provider = _build_provider(
        registry,
        provider,
        summary=provider_summary,
        progress=progress,
    )
    runtime = UltronRuntime(
        UltronSettings(
            workspace=workspace,
            state_path=state_path,
            runs_path=runs_path,
        )
    )
    store = ProjectStateStore(runtime.settings.resolve_path(state_path))
    run_store = runtime.run_store
    controls = ControlStore(control_path)

    loop = WorkflowLoop(
        WorkflowEngine(WorkspaceObserver(workspace)),
        selected_provider,
        LoopConfig(interval_seconds=interval_seconds, max_iterations=max_iterations),
        run_store=run_store,
        control_store=controls,
        phase_supplier=lambda: _active_phase(store),
    )
    runs = loop.run(
        lambda: (project := _safe_load(store)) is not None
        and project.active_phase_id is not None,
        on_run=lambda run: typer.echo(
            f"{run.run_id} | {run.provider.provider.value} | "
            f"{run.assessment.state.value} | {run.decision.kind.value}"
        ),
    )
    typer.echo(f"Runs completed: {len(runs)}")


@app.command()
def serve() -> None:
    """Start the local FastAPI control plane."""
    try:
        import uvicorn
        from .api import create_app
    except ImportError as exc:
        raise typer.BadParameter("Install the 'api' optional dependency to run the server.") from exc

    settings = UltronSettings()
    settings.validate_paths()
    uvicorn.run(create_app(UltronRuntime(settings)), host=settings.api_host, port=settings.api_port)


def _safe_load(store: ProjectStateStore) -> Project | None:
    try:
        return store.load()
    except FileNotFoundError:
        return None


def _active_phase(store: ProjectStateStore) -> Phase | None:
    project = _safe_load(store)
    if project is None or project.active_phase_id is None:
        return None
    return next(
        (phase for phase in project.phases if phase.id == project.active_phase_id),
        None,
    )


if __name__ == "__main__":
    app()
