from dataclasses import dataclass

from ultron.approval import ApprovalRequest, ApprovalStatus
from ultron.delivery import PromptDeliveryService
from ultron.interaction import InteractionResult
from ultron.models import Phase
from ultron.providers import MockProvider
from ultron.safety import ActionRisk
from ultron.workspace import WorkspaceObserver
from ultron.workflow import WorkflowEngine


@dataclass
class FakeInteraction:
    sent: list[str]

    @property
    def provider(self) -> str:
        return "mock"

    def send_prompt(
        self,
        prompt: str,
        correlation_id: str,
        approval: ApprovalRequest | None = None,
        requires_approval: bool = True,
    ) -> InteractionResult:
        self.sent.append(prompt)
        return InteractionResult("i-1", self.provider, True, "sent", correlation_id)


def approved() -> ApprovalRequest:
    return ApprovalRequest(
        request_id="req-1",
        action="send prompt",
        rationale="Continue",
        risk=ActionRisk.REQUIRES_APPROVAL,
        status=ApprovalStatus.APPROVED,
        requested_at="2026-09-19T00:00:00+00:00",
        resolved_at="2026-09-19T00:01:00+00:00",
        resolution_note="Approved",
        correlation_id="run-1",
    )


def test_delivery_uses_workflow_correlation_id(tmp_path) -> None:
    run = WorkflowEngine(WorkspaceObserver(tmp_path)).observe(
        MockProvider(summary="Working", progress=0.5),
        has_active_phase=True,
        phase=Phase(id="phase-1", title="Implementation", objective="Continue"),
    )
    adapter = FakeInteraction([])

    result = PromptDeliveryService().deliver(run, adapter, approved())

    assert result.run_id == run.run_id
    assert result.interaction.accepted is True
    assert result.interaction.correlation_id == run.run_id
    assert adapter.sent


def test_delivery_can_run_in_explicit_auto_mode(tmp_path) -> None:
    run = WorkflowEngine(WorkspaceObserver(tmp_path)).observe(
        MockProvider(summary="Working", progress=0.5),
        has_active_phase=True,
        phase=Phase(id="phase-1", title="Implementation", objective="Continue"),
    )
    adapter = FakeInteraction([])

    result = PromptDeliveryService().deliver(
        run,
        adapter,
        require_approval=False,
    )

    assert result.interaction.accepted is True
    assert result.run_id == run.run_id
