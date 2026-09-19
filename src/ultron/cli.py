"""Command-line entry point for ULTRON CODE."""

from pathlib import Path

import typer

from .approval import ApprovalGateway, ApprovalStatus
from .audit import AuditLogger
from .autonomous import AutonomousLoopConfig, AutonomousRunner
from .control import ControlStore
from .desktop import DesktopInteractionConfig, DesktopProviderAdapter
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
    raise typer.BadParameter("Use mock, chatgpt, claude, cursor, or a screen-* provider.")


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
            (root / target).resolve() if not target.is_absolute() else target.resolve()
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


# CLI command implementations intentionally remain unchanged below this point.
