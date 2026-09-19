"""End-to-end workflow coordination for ULTRON CODE."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from uuid import uuid4

from .correlation import ProgressAssessment, ProgressCorrelator
from .decision import Decision, DecisionEngine
from .executor import ActionExecutor, ExecutionResult
from .providers import ProviderAdapter, ProviderSnapshot
from .workspace import WorkspaceObserver, WorkspaceSnapshot


class WorkflowStage(StrEnum):
    OBSERVED = "observed"
    DECIDED = "decided"
    EXECUTED = "executed"


@dataclass(frozen=True)
class WorkflowRun:
    """Complete trace for one observe/decide/execute cycle."""

    run_id: str
    started_at: str
    stage: WorkflowStage
    provider: ProviderSnapshot
    workspace: WorkspaceSnapshot
    assessment: ProgressAssessment
    decision: Decision
    execution: ExecutionResult | None = None
    notes: tuple[str, ...] = field(default_factory=tuple)


class WorkflowEngine:
    """Coordinate existing ULTRON components without bypassing their boundaries."""

    def __init__(
        self,
        workspace: WorkspaceObserver,
        correlator: ProgressCorrelator | None = None,
        decision_engine: DecisionEngine | None = None,
        executor: ActionExecutor | None = None,
    ) -> None:
        self.workspace = workspace
        self.correlator = correlator or ProgressCorrelator()
        self.decision_engine = decision_engine or DecisionEngine()
        self.executor = executor

    def observe(
        self,
        provider: ProviderAdapter,
        has_active_phase: bool,
        acceptance_criteria_met: bool = False,
    ) -> WorkflowRun:
        """Collect provider/workspace evidence and produce one decision."""
        run_id = str(uuid4())
        provider_snapshot = provider.snapshot()
        workspace_snapshot = self.workspace.snapshot()
        assessment = self.correlator.assess(provider_snapshot, workspace_snapshot)
        decision = self.decision_engine.decide(
            state=assessment.state,
            has_active_phase=has_active_phase,
            acceptance_criteria_met=acceptance_criteria_met,
        )
        return WorkflowRun(
            run_id=run_id,
            started_at=datetime.now(timezone.utc).isoformat(),
            stage=WorkflowStage.DECIDED,
            provider=provider_snapshot,
            workspace=workspace_snapshot,
            assessment=assessment,
            decision=decision,
        )

    def execute(
        self,
        run: WorkflowRun,
        action: str,
        approval=None,
    ) -> WorkflowRun:
        """Execute one explicitly supplied action within an existing run."""
        if self.executor is None:
            raise RuntimeError("WorkflowEngine has no ActionExecutor configured.")

        result = self.executor.execute(action, approval=approval, correlation_id=run.run_id)
        return WorkflowRun(
            run_id=run.run_id,
            started_at=run.started_at,
            stage=WorkflowStage.EXECUTED,
            provider=run.provider,
            workspace=run.workspace,
            assessment=run.assessment,
            decision=run.decision,
            execution=result,
            notes=run.notes + ("Execution completed through the controlled executor.",),
        )
