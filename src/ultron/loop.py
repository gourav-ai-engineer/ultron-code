"""Bounded autonomous workflow loop for ULTRON CODE."""

from collections.abc import Callable
from dataclasses import dataclass
import threading
import time

from .providers import ProviderAdapter
from .run_store import RunStore
from .workflow import WorkflowEngine, WorkflowRun


@dataclass(frozen=True)
class LoopConfig:
    """Controls one bounded loop session."""

    interval_seconds: float = 10.0
    max_iterations: int = 1

    def __post_init__(self) -> None:
        if self.interval_seconds <= 0:
            raise ValueError("interval_seconds must be positive")
        if self.max_iterations < 0:
            raise ValueError("max_iterations cannot be negative")


class WorkflowLoop:
    """Repeatedly observe a provider until stopped or the limit is reached."""

    def __init__(
        self,
        engine: WorkflowEngine,
        provider: ProviderAdapter,
        config: LoopConfig | None = None,
        run_store: RunStore | None = None,
    ) -> None:
        self.engine = engine
        self.provider = provider
        self.config = config or LoopConfig()
        self.run_store = run_store
        self._stop_event = threading.Event()

    def stop(self) -> None:
        """Request a cooperative stop."""
        self._stop_event.set()

    def run(
        self,
        has_active_phase: Callable[[], bool],
        on_run: Callable[[WorkflowRun], None] | None = None,
    ) -> list[WorkflowRun]:
        """Run until stopped or max_iterations is reached; zero means unbounded."""
        runs: list[WorkflowRun] = []
        iteration = 0
        while not self._stop_event.is_set():
            run = self.engine.observe(
                self.provider,
                has_active_phase=has_active_phase(),
            )
            runs.append(run)
            if self.run_store is not None:
                self.run_store.append(run)
            if on_run is not None:
                on_run(run)

            iteration += 1
            if self.config.max_iterations and iteration >= self.config.max_iterations:
                break
            self._stop_event.wait(self.config.interval_seconds)
        return runs
