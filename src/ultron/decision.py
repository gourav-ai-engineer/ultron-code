"""Explainable next-action recommendations for ULTRON CODE."""

from dataclasses import dataclass
from enum import StrEnum

from .correlation import ProgressState


class DecisionKind(StrEnum):
    WAIT = "wait"
    REVIEW = "review"
    REQUEST_INPUT = "request_input"
    ADVANCE_PHASE = "advance_phase"


@dataclass(frozen=True)
class Decision:
    kind: DecisionKind
    rationale: str
    requires_approval: bool = False


class DecisionEngine:
    """Recommend a next step without executing external actions."""

    def decide(
        self,
        state: ProgressState,
        has_active_phase: bool,
        acceptance_criteria_met: bool = False,
    ) -> Decision:
        if state == ProgressState.BLOCKED:
            return Decision(
                DecisionKind.REQUEST_INPUT,
                "The workflow is blocked; human input is required.",
                True,
            )
        if state == ProgressState.COMPLETE and has_active_phase and acceptance_criteria_met:
            return Decision(
                DecisionKind.ADVANCE_PHASE,
                "The active phase appears complete and its criteria are met.",
                True,
            )
        if state == ProgressState.IDLE:
            return Decision(
                DecisionKind.REVIEW,
                "No active progress signal was detected; review the workspace and provider output.",
            )
        if state == ProgressState.PROGRESSING:
            return Decision(DecisionKind.WAIT, "Progress is being detected; wait for the next observation.")
        return Decision(DecisionKind.REVIEW, "The current state is inconclusive; review available evidence.")
