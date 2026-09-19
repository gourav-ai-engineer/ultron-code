from ultron.approval import ApprovalGateway, ApprovalStatus
from ultron.safety import ActionRisk, SafetyDecision


def make_decision() -> SafetyDecision:
    return SafetyDecision(
        action="git push origin main",
        risk=ActionRisk.REQUIRES_APPROVAL,
        allowed=False,
        reason="Explicit approval is required.",
        timestamp="2026-09-19T00:00:00+00:00",
    )


def test_request_is_persisted(tmp_path) -> None:
    gateway = ApprovalGateway(tmp_path / "approvals.json")
    request = gateway.request(make_decision(), "Publish the completed phase.")

    assert request.status == ApprovalStatus.PENDING
    assert gateway.get(request.request_id) == request
    assert gateway.pending() == [request]


def test_request_can_be_approved(tmp_path) -> None:
    gateway = ApprovalGateway(tmp_path / "approvals.json")
    request = gateway.request(make_decision(), "Publish the completed phase.")

    resolved = gateway.resolve(
        request.request_id,
        ApprovalStatus.APPROVED,
        "Approved after review.",
    )

    assert resolved.status == ApprovalStatus.APPROVED
    assert resolved.resolution_note == "Approved after review."
    assert gateway.pending() == []


def test_blocked_action_cannot_create_approval(tmp_path) -> None:
    gateway = ApprovalGateway(tmp_path / "approvals.json")
    decision = SafetyDecision(
        action="rm -rf build",
        risk=ActionRisk.BLOCKED,
        allowed=False,
        reason="Destructive operation is blocked.",
        timestamp="2026-09-19T00:00:00+00:00",
    )

    try:
        gateway.request(decision, "Cleanup build output.")
    except ValueError as exc:
        assert "only valid" in str(exc)
    else:
        raise AssertionError("Blocked actions must not create approval requests.")
