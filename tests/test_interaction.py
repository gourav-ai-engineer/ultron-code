from dataclasses import dataclass

from ultron.approval import ApprovalRequest, ApprovalStatus
from ultron.interaction import InteractionGateway, InteractionResult
from ultron.safety import ActionRisk


@dataclass
class FakeAdapter:
    sent: list[str]

    @property
    def provider(self) -> str:
        return "fake"

    def send_prompt(self, prompt: str, correlation_id: str) -> InteractionResult:
        self.sent.append(prompt)
        return InteractionResult("interaction-1", self.provider, True, "sent", correlation_id)


def test_interaction_requires_approval() -> None:
    adapter = FakeAdapter([])
    result = InteractionGateway().send(adapter, "continue", requires_approval=True)

    assert result.accepted is False
    assert adapter.sent == []


def test_interaction_sends_after_approval() -> None:
    adapter = FakeAdapter([])
    approval = ApprovalRequest(
        request_id="req-1",
        action="send prompt",
        rationale="Continue implementation",
        risk=ActionRisk.REQUIRES_APPROVAL,
        status=ApprovalStatus.APPROVED,
        requested_at="2026-09-19T00:00:00+00:00",
        resolved_at="2026-09-19T00:01:00+00:00",
        resolution_note="Approved",
        correlation_id="run-1",
    )

    result = InteractionGateway().send(adapter, "continue", approval=approval)

    assert result.accepted is True
    assert adapter.sent == ["continue"]
