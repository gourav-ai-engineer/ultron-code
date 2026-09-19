from ultron.correlation import ProgressState
from ultron.decision import DecisionEngine, DecisionKind


def test_blocked_state_requests_input() -> None:
    decision = DecisionEngine().decide(ProgressState.BLOCKED, has_active_phase=True)
    assert decision.kind == DecisionKind.REQUEST_INPUT
    assert decision.requires_approval is True


def test_complete_state_can_advance() -> None:
    decision = DecisionEngine().decide(
        ProgressState.COMPLETE,
        has_active_phase=True,
        acceptance_criteria_met=True,
    )
    assert decision.kind == DecisionKind.ADVANCE_PHASE


def test_progressing_state_waits() -> None:
    decision = DecisionEngine().decide(ProgressState.PROGRESSING, has_active_phase=True)
    assert decision.kind == DecisionKind.WAIT
