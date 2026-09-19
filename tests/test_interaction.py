from dataclasses import dataclass

from ultron.approval import ApprovalRequest, ApprovalStatus
from ultron.interaction import InteractionGateway, InteractionResult
from ultron.safety import ActionRisk


@dataclass
class FakeAdapter:
    sent: list[str]
    received_approval: bool = False
    received_correlation_id: str | None = None

    @property
    def provider(self) -> str:
        return "fake"

    def send_prompt(
        self,
        prompt: str,
        correlation_id: str,
        approval: ApprovalRequest | None = None,
    ) -> InteractionResult:
        self.sent.append(prompt)
        self.received_approval = approval is not None
        self.received_correlation_id = correlation_id
        return InteractionResult("interaction-1", self.provider, True, "sent", correlation_id)


def approved() -> ApprovalRequest:
    return ApprovalRequest(
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


def test_interaction_requires_approval() -> None:
    adapter = FakeAdapter([])
    result = InteractionGateway().send(adapter, "continue", requires_approval=True)

    assert result.accepted is False
    assert adapter.sent == []


def test_interaction_sends_after_approval() -> None:
    adapter = FakeAdapter([])

    result = InteractionGateway().send(
        adapter,
        "continue",
        approval=approved(),
        correlation_id="run-1",
    )

    assert result.accepted is True
    assert result.correlation_id == "run-1"
    assert adapter.received_correlation_id == "run-1"
    assert adapter.sent == ["continue"]
    assert adapter.received_approval is True
