"""Autonomous prompt-dispatch loop for ULTRON CODE."""

from collections.abc import Callable
from dataclasses import dataclass
import hashlib
import threading

from .control import ControlStore
from .delivery import DeliveryResult, PromptDeliveryService
from .interaction import ProviderInteractionAdapter
from .models import Phase
from .providers import ProviderAdapter
from .run_store import RunStore
from .workflow import WorkflowEngine, WorkflowRun


@dataclass(frozen=True)
class AutonomousLoopConfig:
    """Controls autonomous observation and safe prompt dispatch."""

    interval_seconds: float = 10.0
    max_iterations: int = 1
    auto_prompt_enabled: bool = False
    suppress_duplicate_prompts: bool = True

    def __post_init__(self) -> None:
        if self.interval_seconds <= 0:
            raise ValueError("interval_seconds must be positive")
        if self.max_iterations < 0:
            raise ValueError("max_iterations cannot be negative")


@dataclass(frozen=True)
class AutonomousCycle:
    """One autonomous observation cycle and optional prompt delivery."""

    run: WorkflowRun
    delivery: DeliveryResult | None = None


class AutonomousRunner:
    """Observe, synthesize, and optionally dispatch safe prompts."""

    def __init__(
        self,
        engine: WorkflowEngine,
        provider: ProviderAdapter,
        interaction: ProviderInteractionAdapter | None = None,
        config: AutonomousLoopConfig | None = None,
        run_store: RunStore | None = None,
        control_store: ControlStore | None = None,
        delivery: PromptDeliveryService | None = None,
        phase_supplier: Callable[[], Phase | None] | None = None,
    ) -> None:
        self.engine = engine
        self.provider = provider
        self.interaction = interaction
        self.config = config or AutonomousLoopConfig()
        self.run_store = run_store
        self.control_store = control_store
        self.delivery = delivery or PromptDeliveryService()
        self.phase_supplier = phase_supplier
        self._stop_event = threading.Event()
        self._last_prompt_fingerprint: str | None = None

    def stop(self) -> None:
        """Request a cooperative stop."""
        self._stop_event.set()

    def run(
        self,
        has_active_phase: Callable[[], bool],
        on_cycle: Callable[[AutonomousCycle], None] | None = None,
    ) -> list[AutonomousCycle]:
        """Run bounded cycles and dispatch only changed, non-blocked prompts."""
        cycles: list[AutonomousCycle] = []
        iteration = 0

        while not self._stop_event.is_set():
            if self.control_store is not None:
                controls = self.control_store.get()
                if controls.emergency_stop or controls.paused:
                    break

            phase = self.phase_supplier() if self.phase_supplier is not None else None
            active = phase is not None if self.phase_supplier is not None else has_active_phase()

            run = self.engine.observe(
                self.provider,
                has_active_phase=active,
                phase=phase,
            )

            if self.run_store is not None:
                self.run_store.append(run)

            result = None
            fingerprint = self._fingerprint(run)
            should_dispatch = (
                self.config.auto_prompt_enabled
                and self.interaction is not None
                and not run.prompt.requires_approval
                and (
                    not self.config.suppress_duplicate_prompts
                    or fingerprint != self._last_prompt_fingerprint
                )
            )
            if should_dispatch:
                result = self.delivery.deliver(
                    run,
                    self.interaction,
                    approval=None,
                    require_approval=False,
                )
                if result.interaction.accepted:
                    self._last_prompt_fingerprint = fingerprint

            cycle = AutonomousCycle(run=run, delivery=result)
            cycles.append(cycle)

            if self.run_store is not None and result is not None and result.interaction.accepted:
                updated = self._with_interaction_note(run)
                self.run_store.append(updated)

            if on_cycle is not None:
                on_cycle(cycle)

            iteration += 1
            if self.config.max_iterations and iteration >= self.config.max_iterations:
                break
            self._stop_event.wait(self.config.interval_seconds)

        return cycles

    @staticmethod
    def _fingerprint(run: WorkflowRun) -> str:
        digest = hashlib.sha256()
        digest.update(run.provider.provider.value.encode("utf-8"))
        digest.update((run.provider.session_id or "").encode("utf-8"))
        digest.update(run.prompt.prompt.encode("utf-8"))
        return digest.hexdigest()

    @staticmethod
    def _with_interaction_note(run: WorkflowRun) -> WorkflowRun:
        return WorkflowRun(
            run_id=run.run_id,
            started_at=run.started_at,
            stage=run.stage,
            provider=run.provider,
            workspace=run.workspace,
            assessment=run.assessment,
            decision=run.decision,
            prompt=run.prompt,
            execution=run.execution,
            notes=run.notes + (
                "Synthesized prompt delivered through trusted automation.",
            ),
        )
