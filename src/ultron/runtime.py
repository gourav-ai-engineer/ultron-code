"""High-level ULTRON runtime facade."""

from typing import Any

from .models import Phase, Project
from .provider_registry import ProviderRegistry
from .providers import ProviderAdapter
from .run_store import RunStore
from .settings import UltronSettings
from .workflow import WorkflowEngine, WorkflowRun
from .workspace import WorkspaceObserver


class UltronRuntime:
    """Compose configuration, provider selection, workflow, and persistence."""

    def __init__(
        self,
        settings: UltronSettings | None = None,
        registry: ProviderRegistry | None = None,
    ) -> None:
        self.settings = settings or UltronSettings()
        self.settings.validate_paths()
        self.registry = registry or ProviderRegistry()
        self.run_store = RunStore(self.settings.resolve_path(self.settings.runs_path))

    def provider(self, kind: str, **kwargs: Any) -> ProviderAdapter:
        """Create a provider from the central registry."""
        return self.registry.create(kind, **kwargs)

    def observe(
        self,
        provider: ProviderAdapter,
        project: Project | None = None,
    ) -> WorkflowRun:
        """Run one provider/workspace observation and persist it."""
        active_phase = self._active_phase(project)
        engine = WorkflowEngine(
            WorkspaceObserver(self.settings.workspace),
        )
        run = engine.observe(
            provider,
            has_active_phase=active_phase is not None,
            phase=active_phase,
        )
        self.run_store.append(run)
        return run

    def project(self) -> Project | None:
        """Load the configured project state when it exists."""
        from .state import ProjectStateStore

        path = self.settings.resolve_path(self.settings.state_path)
        try:
            return ProjectStateStore(path).load()
        except FileNotFoundError:
            return None

    @staticmethod
    def _active_phase(project: Project | None) -> Phase | None:
        if project is None or project.active_phase_id is None:
            return None
        return next(
            (phase for phase in project.phases if phase.id == project.active_phase_id),
            None,
        )

    @property
    def run_count(self) -> int:
        return len(self.run_store.all())
