from ultron.safety import ActionRisk, SafetyPolicy


def test_dry_run_does_not_allow_execution() -> None:
    decision = SafetyPolicy().evaluate("echo hello")
    assert decision.risk == ActionRisk.SAFE
    assert decision.allowed is False


def test_destructive_action_is_blocked() -> None:
    decision = SafetyPolicy(dry_run=False).evaluate("rm -rf ./project")
    assert decision.risk == ActionRisk.BLOCKED
    assert decision.allowed is False


def test_approval_action_requires_approval() -> None:
    policy = SafetyPolicy(dry_run=False)
    assert policy.evaluate("git push").risk == ActionRisk.REQUIRES_APPROVAL
    assert policy.evaluate("git push", approved=True).allowed is True


def test_emergency_stop_blocks_everything() -> None:
    decision = SafetyPolicy(dry_run=False, emergency_stop=True).evaluate("echo hello")
    assert decision.risk == ActionRisk.BLOCKED
    assert decision.allowed is False
