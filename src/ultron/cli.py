"""Command-line entry point for ULTRON CODE."""

from pathlib import Path

import typer

from .approval import ApprovalGateway, ApprovalStatus
from .audit import AuditLogger
from .autonomous import AutonomousLoopConfig, AutonomousRunner
from .control import ControlStore
from .desktop import DesktopInteractionConfig, DesktopProviderAdapter
from .doctor import Doctor
from .delivery import PromptDeliveryService
from .executor import ActionExecutor, ExecutionDeniedError
from .loop import LoopConfig, WorkflowLoop
from .models import Phase, Project
from .orchestrator import Orchestrator
from .planner import ProjectPlanner
from .provider_registry import ProviderRegistry
from .provider_runtime import ProviderRequestError
from .providers import ProviderAdapter, ProviderKind
from .run_store import RunStore
from .runtime import UltronRuntime
from .safety import ActionRisk, SafetyPolicy
from .screen_provider import ScreenProviderAdapter
from .settings import UltronSettings
from .state import ProjectStateStore
from .validator import Validator
from .workflow import WorkflowEngine
from .workspace import WorkspaceObserver

app = typer.Typer(help="ULTRON CODE development orchestrator")


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


def _is_screen_provider(provider: str) -> bool:
    return provider.strip().lower() in {
        "screen-chatgpt",
        "screen-claude",
        "screen-cursor",
    }


def _screen_kind(provider: str) -> ProviderKind:
    mapping = {
        "screen-chatgpt": ProviderKind.CHATGPT,
        "screen-claude": ProviderKind.CLAUDE,
        "screen-cursor": ProviderKind.CURSOR,
    }
    normalized = provider.strip().lower()
    try:
        return mapping[normalized]
    except KeyError as exc:
        raise typer.BadParameter(
            "Use screen-chatgpt, screen-claude, or screen-cursor."
        ) from exc


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
    raise typer.BadParameter(
        "Use mock, chatgpt, claude, cursor, or a screen-* provider."
    )


def _build_provider(
    registry: ProviderRegistry,
    provider: str,
    *,
    workspace: Path | None = None,
    screen_window_title: str | None = None,
    screen_path: Path | None = None,
    response_id: str | None = None,
    agent_id: str | None = None,
    provider_run_id: str | None = None,
    summary: str = "No activity recorded.",
    progress: float | None = None,
    session_id: str | None = None,
) -> ProviderAdapter:
    normalized = provider.strip().lower()

    if _is_screen_provider(normalized):
        if screen_window_title is None or not screen_window_title.strip():
            raise typer.BadParameter(
                "screen_window_title is required for screen-* providers."
            )

        root = workspace.resolve() if workspace is not None else Path(".").resolve()
        target = screen_path or Path(".ultron/screens/provider.png")
        resolved_screen_path = (
            (root / target).resolve()
            if not target.is_absolute()
            else target.resolve()
        )
        try:
            resolved_screen_path.relative_to(root)
        except ValueError as exc:
            raise typer.BadParameter(
                "screen_path must be inside the configured workspace."
            ) from exc

        return ScreenProviderAdapter(
            _screen_kind(normalized),
            screen_window_title,
            screenshot_path=resolved_screen_path,
        )

    kwargs = _provider_kwargs(
        normalized,
        response_id,
        agent_id,
        provider_run_id,
        summary,
        progress,
        session_id,
    )
    return registry.create(normalized, **kwargs)


@app.command()
def status() -> None:
    """Show the current runtime configuration."""
    settings = UltronSettings()
    settings.validate_paths()
    typer.echo("ULTRON CODE v1.0.0")
    typer.echo(f"Workspace: {settings.workspace.resolve()}")
    typer.echo(f"Dry-run: {settings.dry_run}")
    typer.echo(f"Automation enabled: {settings.automation_enabled}")
    typer.echo(f"Auto-prompt enabled: {settings.auto_prompt_enabled}")
    typer.echo(f"API: {settings.api_host}:{settings.api_port}")
    typer.echo("Runtime: ready")


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
            Phase(
                id="phase-1",
                title="Architecture",
                objective="Define the system architecture",
            ),
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
    technologies: str = typer.Option(
        "",
        help="Comma-separated technologies or keywords",
    ),
    state_path: Path = typer.Option(Path(".ultron/project.json")),
) -> None:
    """Generate and save a deterministic project plan."""
    technology_list = [item.strip() for item in technologies.split(",") if item.strip()]
    project = ProjectPlanner().create_plan(name, goal, technology_list)
    ProjectStateStore(state_path).save(project)
    typer.echo(f"Plan created with {len(project.phases)} phases: {state_path}")


@app.command()
def next_phase(
    state_path: Path = typer.Option(Path(".ultron/project.json")),
) -> None:
    """Activate and display the next pending phase."""
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
def complete_phase(
    state_path: Path = typer.Option(Path(".ultron/project.json")),
) -> None:
    """Complete the active phase and clear the active phase pointer."""
    store = ProjectStateStore(state_path)
    project = store.load()
    Orchestrator(project).complete_active_phase()
    store.save(project)
    typer.echo("Active phase completed.")


@app.command()
def provider_status(
    provider: str = typer.Option(
        ...,
        prompt="Provider (chatgpt/claude/cursor/mock/screen-*)",
    ),
    workspace: Path = typer.Option(Path(".")),
    response_id: str | None = typer.Option(None),
    agent_id: str | None = typer.Option(None),
    provider_run_id: str | None = typer.Option(None),
    screen_window_title: str | None = typer.Option(None),
    screen_path: Path | None = typer.Option(None),
) -> None:
    """Probe a provider through its read-only adapter."""
    registry = ProviderRegistry()
    try:
        adapter = _build_provider(
            registry,
            provider,
            workspace=workspace,
            screen_window_title=screen_window_title,
            screen_path=screen_path,
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
        typer.echo(
            f"Progress: {snapshot.progress if snapshot.progress is not None else 'n/a'}"
        )
    except ProviderRequestError as exc:
        typer.echo(f"Provider unavailable: {exc}")
        raise typer.Exit(code=1) from exc


@app.command()
def approval_request(
    action: str = typer.Option(..., prompt="Action requiring approval"),
    rationale: str = typer.Option(..., prompt="Rationale"),
    approvals_path: Path = typer.Option(Path(".ultron/approvals.json")),
    correlation_id: str | None = typer.Option(None),
) -> None:
    """Create an approval request for a safety-classified action."""
    safety_decision = SafetyPolicy(dry_run=True).evaluate(action)
    if safety_decision.risk != ActionRisk.REQUIRES_APPROVAL:
        typer.echo(
            f"Approval request not created: {safety_decision.reason}"
        )
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
        typer.echo(
            f"{request.request_id} | {request.risk.value} | {request.action}"
        )
        typer.echo(f"  Rationale: {request.rationale}")


@app.command()
def approval_resolve(
    request_id: str = typer.Option(..., prompt="Approval request ID"),
    status: str = typer.Option(
        ...,
        prompt="Resolution (approved/rejected/deferred)",
    ),
    note: str = typer.Option(""),
    approvals_path: Path = typer.Option(Path(".ultron/approvals.json")),
) -> None:
    """Resolve a pending approval request explicitly."""
    try:
        resolution = ApprovalStatus(status)
    except ValueError as exc:
        raise typer.BadParameter(
            "Use approved, rejected, or deferred."
        ) from exc
    request = ApprovalGateway(approvals_path).resolve(
        request_id,
        resolution,
        note,
    )
    typer.echo(f"Request: {request.request_id}")
    typer.echo(f"Status: {request.status.value}")


@app.command()
def execute(
    action: str = typer.Option(..., prompt="Allowlisted action"),
    workspace: Path = typer.Option(Path(".")),
    live: bool = typer.Option(
        False,
        "--live",
        help="Execute instead of dry-run evaluation.",
    ),
    approval_id: str | None = typer.Option(None, "--approval-id"),
    approvals_path: Path = typer.Option(Path(".ultron/approvals.json")),
) -> None:
    """Evaluate and optionally execute one allowlisted action."""
    approval = (
        ApprovalGateway(approvals_path).get(approval_id)
        if approval_id
        else None
    )
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
    runs_path: Path = typer.Option(Path(".ultron/runs.jsonl")),
    provider: str = typer.Option("mock"),
    provider_summary: str = typer.Option("No activity recorded."),
    progress: float | None = typer.Option(None, min=0.0, max=1.0),
    session_id: str | None = typer.Option(None),
    response_id: str | None = typer.Option(None),
    agent_id: str | None = typer.Option(None),
    provider_run_id: str | None = typer.Option(None),
    screen_window_title: str | None = typer.Option(None),
    screen_path: Path | None = typer.Option(None),
    action: str | None = typer.Option(None),
    live: bool = typer.Option(False, "--live"),
    approval_id: str | None = typer.Option(None, "--approval-id"),
    approvals_path: Path = typer.Option(Path(".ultron/approvals.json")),
) -> None:
    """Run one provider-backed workflow cycle and persist its trace."""
    project = _safe_load(ProjectStateStore(state_path))
    settings = UltronSettings(
        workspace=workspace,
        state_path=state_path,
        runs_path=runs_path,
    )
    settings.validate_paths()

    registry = ProviderRegistry()
    try:
        selected_provider = _build_provider(
            registry,
            provider,
            workspace=workspace,
            screen_window_title=screen_window_title,
            screen_path=screen_path,
            response_id=response_id,
            agent_id=agent_id,
            provider_run_id=provider_run_id,
            summary=provider_summary,
            progress=progress,
            session_id=session_id,
        )
        phase = (
            next(
                (item for item in project.phases if item.id == project.active_phase_id),
                None,
            )
            if project is not None and project.active_phase_id is not None
            else None
        )
        engine = WorkflowEngine(
            WorkspaceObserver(workspace),
            executor=(
                ActionExecutor(
                    workspace,
                    safety_policy=SafetyPolicy(dry_run=not live),
                )
                if action is not None
                else None
            ),
        )
        run = engine.observe(
            selected_provider,
            has_active_phase=(
                project is not None and project.active_phase_id is not None
            ),
            phase=phase,
        )
        run_store = RunStore(settings.resolve_path(runs_path))
        run_store.append(run)
    except (ProviderRequestError, ValueError) as exc:
        typer.echo(f"Workflow configuration error: {exc}")
        raise typer.Exit(code=1) from exc

    typer.echo(f"Run ID: {run.run_id}")
    typer.echo(f"Provider: {run.provider.provider.value}")
    typer.echo(f"Progress state: {run.assessment.state.value}")
    typer.echo(f"Decision: {run.decision.kind.value}")
    typer.echo("NEXT PROMPT:")
    typer.echo(run.prompt.prompt)

    if action is None:
        return

    approval = (
        ApprovalGateway(approvals_path).get(approval_id)
        if approval_id
        else None
    )
    try:
        completed = engine.execute(
            run,
            action,
            approval=approval,
        )
    except ExecutionDeniedError as exc:
        typer.echo(f"Execution denied: {exc}")
        raise typer.Exit(code=1) from exc

    run_store.append(completed)
    if completed.execution is not None:
        typer.echo(
            f"Execution correlation ID: {completed.execution.correlation_id}"
        )
        typer.echo(f"Exit code: {completed.execution.return_code}")
        typer.echo(f"Timed out: {completed.execution.timed_out}")


@app.command()
def prompt_send(
    run_id: str = typer.Option(..., prompt="Workflow run ID"),
    provider: str = typer.Option(..., prompt="Desktop provider name"),
    window_title: str = typer.Option(..., prompt="Window title contains"),
    approval_id: str = typer.Option(..., prompt="Approved request ID"),
    workspace: Path = typer.Option(Path(".")),
    runs_path: Path = typer.Option(Path(".ultron/runs.jsonl")),
    approvals_path: Path = typer.Option(Path(".ultron/approvals.json")),
    audit_path: Path = typer.Option(Path(".ultron/audit.jsonl")),
) -> None:
    """Deliver one persisted synthesized prompt after approval."""
    settings = UltronSettings(workspace=workspace)
    settings.validate_paths()
    if not settings.automation_enabled:
        typer.echo(
            "Automation is disabled. Set ULTRON_AUTOMATION_ENABLED=true first."
        )
        raise typer.Exit(code=1)

    run = RunStore(settings.resolve_path(runs_path)).get(run_id)
    if run.provider.provider.value != provider.strip().lower():
        typer.echo("Provider does not match the workflow run.")
        raise typer.Exit(code=1)

    approval = ApprovalGateway(
        settings.resolve_path(approvals_path)
    ).get(approval_id)
    adapter = DesktopProviderAdapter(
        provider.strip().lower(),
        DesktopInteractionConfig(
            window_title=window_title,
            enabled=True,
            trusted_automation=False,
        ),
    )
    delivery = PromptDeliveryService(
        audit_logger=AuditLogger(settings.resolve_path(audit_path)),
    )
    result = delivery.deliver(run, adapter, approval=approval)
    typer.echo(f"Run ID: {result.run_id}")
    typer.echo(f"Accepted: {result.interaction.accepted}")
    typer.echo(f"Message: {result.interaction.message}")


@app.command()
def control_status(
    control_path: Path = typer.Option(Path(".ultron/control.json")),
) -> None:
    """Show persistent runtime control state."""
    state = ControlStore(control_path).get()
    typer.echo(f"Emergency stop: {state.emergency_stop}")
    typer.echo(f"Paused: {state.paused}")
    typer.echo(f"Reason: {state.reason or 'n/a'}")


@app.command()
def control_stop(
    control_path: Path = typer.Option(Path(".ultron/control.json")),
    reason: str = typer.Option("Operator requested emergency stop."),
) -> None:
    """Enable the persistent emergency stop."""
    state = ControlStore(control_path).set(
        emergency_stop=True,
        reason=reason,
    )
    typer.echo(f"Emergency stop: {state.emergency_stop}")
    typer.echo(f"Reason: {state.reason}")


@app.command()
def control_clear(
    control_path: Path = typer.Option(Path(".ultron/control.json")),
) -> None:
    """Clear emergency stop and pause state."""
    state = ControlStore(control_path).set(
        emergency_stop=False,
        paused=False,
        reason="",
    )
    typer.echo(f"Emergency stop: {state.emergency_stop}")
    typer.echo(f"Paused: {state.paused}")


@app.command()
def control_pause(
    control_path: Path = typer.Option(Path(".ultron/control.json")),
    reason: str = typer.Option("Operator paused runtime."),
) -> None:
    """Pause future workflow-loop iterations."""
    state = ControlStore(control_path).set(
        paused=True,
        reason=reason,
    )
    typer.echo(f"Paused: {state.paused}")


@app.command()
def control_resume(
    control_path: Path = typer.Option(Path(".ultron/control.json")),
) -> None:
    """Resume future workflow-loop iterations."""
    current = ControlStore(control_path).get()
    if current.emergency_stop:
        typer.echo(
            "Emergency stop remains active; use control-clear first."
        )
        raise typer.Exit(code=1)
    state = ControlStore(control_path).set(
        paused=False,
        reason="",
    )
    typer.echo(f"Paused: {state.paused}")


@app.command()
def run_loop(
    provider: str = typer.Option("mock"),
    workspace: Path = typer.Option(Path(".")),
    state_path: Path = typer.Option(Path(".ultron/project.json")),
    runs_path: Path = typer.Option(Path(".ultron/runs.jsonl")),
    control_path: Path = typer.Option(Path(".ultron/control.json")),
    response_id: str | None = typer.Option(None),
    agent_id: str | None = typer.Option(None),
    provider_run_id: str | None = typer.Option(None),
    screen_window_title: str | None = typer.Option(None),
    screen_path: Path | None = typer.Option(None),
    interval_seconds: float = typer.Option(10.0, min=0.1),
    max_iterations: int = typer.Option(1, min=0),
    provider_summary: str = typer.Option("No activity recorded."),
    progress: float | None = typer.Option(None, min=0.0, max=1.0),
) -> None:
    """Run repeated provider observations until stopped or bounded."""
    settings = UltronSettings(
        workspace=workspace,
        state_path=state_path,
        runs_path=runs_path,
        control_path=control_path,
    )
    settings.validate_paths()
    registry = ProviderRegistry()
    try:
        selected_provider = _build_provider(
            registry,
            provider,
            workspace=workspace,
            screen_window_title=screen_window_title,
            screen_path=screen_path,
            response_id=response_id,
            agent_id=agent_id,
            provider_run_id=provider_run_id,
            summary=provider_summary,
            progress=progress,
        )
    except (ProviderRequestError, ValueError) as exc:
        typer.echo(f"Provider configuration error: {exc}")
        raise typer.Exit(code=1) from exc

    project_store = ProjectStateStore(settings.resolve_path(state_path))
    loop = WorkflowLoop(
        WorkflowEngine(WorkspaceObserver(workspace)),
        selected_provider,
        LoopConfig(
            interval_seconds=interval_seconds,
            max_iterations=max_iterations,
        ),
        run_store=RunStore(settings.resolve_path(runs_path)),
        control_store=ControlStore(settings.resolve_path(control_path)),
        phase_supplier=lambda: _active_phase(project_store),
    )
    runs = loop.run(
        lambda: (
            project := _safe_load(project_store)
        ) is not None
        and project.active_phase_id is not None,
        on_run=lambda run: typer.echo(
            f"{run.run_id} | {run.provider.provider.value} | "
            f"{run.assessment.state.value} | {run.decision.kind.value}"
        ),
    )
    typer.echo(f"Runs completed: {len(runs)}")


@app.command()
def auto_loop(
    provider: str = typer.Option("screen-chatgpt"),
    workspace: Path = typer.Option(Path(".")),
    state_path: Path = typer.Option(Path(".ultron/project.json")),
    runs_path: Path = typer.Option(Path(".ultron/runs.jsonl")),
    control_path: Path = typer.Option(Path(".ultron/control.json")),
    screen_window_title: str = typer.Option(
        ...,
        prompt="AI window title contains",
    ),
    screen_path: Path | None = typer.Option(None),
    interval_seconds: float = typer.Option(10.0, min=1.0),
    max_iterations: int = typer.Option(0, min=0),
) -> None:
    """Observe a desktop AI window and auto-send only safe prompts."""
    settings = UltronSettings(
        workspace=workspace,
        state_path=state_path,
        runs_path=runs_path,
        control_path=control_path,
    )
    settings.validate_paths()

    if settings.dry_run:
        typer.echo("Auto loop requires ULTRON_DRY_RUN=false.")
        raise typer.Exit(code=1)
    if not settings.automation_enabled:
        typer.echo(
            "Auto loop requires ULTRON_AUTOMATION_ENABLED=true."
        )
        raise typer.Exit(code=1)
    if not settings.auto_prompt_enabled:
        typer.echo(
            "Auto loop requires ULTRON_AUTO_PROMPT_ENABLED=true."
        )
        raise typer.Exit(code=1)
    if not _is_screen_provider(provider):
        typer.echo(
            "Auto loop currently uses the screen-backed interaction adapter. "
            "Use screen-chatgpt, screen-claude, or screen-cursor."
        )
        raise typer.Exit(code=1)

    registry = ProviderRegistry()
    observer = _build_provider(
        registry,
        provider,
        workspace=workspace,
        screen_window_title=screen_window_title,
        screen_path=screen_path,
    )
    desktop_provider = provider.strip().lower().removeprefix("screen-")
    interaction = DesktopProviderAdapter(
        desktop_provider,
        DesktopInteractionConfig(
            window_title=screen_window_title,
            enabled=True,
            trusted_automation=True,
        ),
    )
    project_store = ProjectStateStore(settings.resolve_path(state_path))
    audit_logger = AuditLogger(settings.resolve_path(settings.audit_path))
    runner = AutonomousRunner(
        WorkflowEngine(WorkspaceObserver(workspace)),
        observer,
        interaction=interaction,
        config=AutonomousLoopConfig(
            interval_seconds=interval_seconds,
            max_iterations=max_iterations,
            auto_prompt_enabled=True,
        ),
        run_store=RunStore(settings.resolve_path(runs_path)),
        control_store=ControlStore(settings.resolve_path(control_path)),
        delivery=PromptDeliveryService(audit_logger=audit_logger),
        phase_supplier=lambda: _active_phase(project_store),
    )

    cycles = runner.run(
        lambda: (
            project := _safe_load(project_store)
        ) is not None
        and project.active_phase_id is not None,
        on_cycle=lambda cycle: typer.echo(
            f"{cycle.run.run_id} | {cycle.run.decision.kind.value} | "
            f"sent={cycle.delivery.interaction.accepted if cycle.delivery else False}"
        ),
    )
    typer.echo(f"Cycles completed: {len(cycles)}")


@app.command()
def run_show(
    run_id: str = typer.Option(..., prompt="Workflow run ID"),
    workspace: Path = typer.Option(Path(".")),
    runs_path: Path = typer.Option(Path(".ultron/runs.jsonl")),
) -> None:
    """Display one persisted workflow run."""
    settings = UltronSettings(workspace=workspace)
    run = RunStore(settings.resolve_path(runs_path)).get(run_id)
    typer.echo(f"Run ID: {run.run_id}")
    typer.echo(f"Stage: {run.stage.value}")
    typer.echo(f"Provider: {run.provider.provider.value}")
    typer.echo(f"Progress: {run.assessment.state.value}")
    typer.echo(f"Decision: {run.decision.kind.value}")
    typer.echo(
        f"Prompt approval required: {run.prompt.requires_approval}"
    )
    if run.execution is not None:
        typer.echo(f"Exit code: {run.execution.return_code}")
        typer.echo(f"Timed out: {run.execution.timed_out}")


@app.command()
def validate(
    command: list[str] = typer.Argument(
        [],
        help="Validation command tokens; omit to run python -m pytest.",
    ),
    workspace: Path = typer.Option(Path(".")),
    live: bool = typer.Option(False, "--live"),
) -> None:
    """Run explicitly supplied allowlisted validation commands."""
    commands = (" ".join(command),) if command else ("python -m pytest",)

    executor = ActionExecutor(
        workspace,
        safety_policy=SafetyPolicy(dry_run=not live),
    )
    report = Validator(executor).validate(commands)
    typer.echo(f"Passed: {report.passed}")
    typer.echo(f"Commands evaluated: {len(report.results)}")
    for result in report.results:
        typer.echo(
            f"{result.action} -> exit={result.return_code}, "
            f"timed_out={result.timed_out}"
        )


@app.command()
def audit_list(
    audit_path: Path = typer.Option(Path(".ultron/audit.jsonl")),
) -> None:
    """Display persisted audit events."""
    events = AuditLogger(audit_path).read_all()
    if not events:
        typer.echo("No audit events recorded.")
        return
    for event in events:
        typer.echo(
            f"{event.timestamp} | {event.status} | "
            f"{event.risk} | {event.correlation_id} | {event.action}"
        )


@app.command()
def doctor(
    include_optional: bool = typer.Option(
        False,
        "--all",
        help="Also require optional API/desktop/OCR dependencies.",
    ),
) -> None:
    """Run non-mutating environment diagnostics."""
    diagnostics = Doctor().check()
    for item in diagnostics:
        state = "OK" if item.ok else "MISSING"
        typer.echo(f"{state:7} {item.name}: {item.detail}")

    if not Doctor().healthy(include_optional=include_optional):
        raise typer.Exit(code=1)


@app.command()
def serve() -> None:
    """Start the local FastAPI control plane."""
    try:
        import uvicorn
        from .api import create_app
    except ImportError as exc:
        raise typer.BadParameter(
            "Install the 'api' optional dependency to run the server."
        ) from exc

    settings = UltronSettings()
    settings.validate_paths()
    uvicorn.run(
        create_app(UltronRuntime(settings)),
        host=settings.api_host,
        port=settings.api_port,
    )


if __name__ == "__main__":
    app()
