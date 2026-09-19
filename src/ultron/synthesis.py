"""Deterministic next-prompt and action proposal synthesis for ULTRON CODE."""

from dataclasses import dataclass

from .correlation import ProgressAssessment, ProgressState
from .decision import Decision, DecisionKind
from .models import Phase
from .providers import ProviderKind, ProviderSnapshot
from .security import redact_secrets
from .workspace import WorkspaceSnapshot


@dataclass(frozen=True)
class PromptProposal:
    """Explainable provider-facing instruction proposal."""

    provider: ProviderKind
    prompt: str
    reason: str
    decision: DecisionKind
    phase_id: str | None
    requires_approval: bool = False


class PromptSynthesizer:
    """Build provider-neutral prompts from observed project evidence."""

    def synthesize(
        self,
        phase: Phase | None,
        provider: ProviderSnapshot,
        workspace: WorkspaceSnapshot,
        assessment: ProgressAssessment,
        decision: Decision,
        advisory: str | None = None,
    ) -> PromptProposal:
        phase_context = (
            f"Current phase: {phase.title} ({phase.id}). Objective: {redact_secrets(phase.objective)}"
            if phase is not None
            else "No active project phase is configured."
        )
        criteria = (
            "Acceptance criteria:\n- "
            + "\n- ".join(redact_secrets(item) for item in phase.acceptance_criteria)
            if phase is not None and phase.acceptance_criteria
            else "Acceptance criteria: not configured."
        )
        workspace_context = (
            f"Workspace branch: {redact_secrets(workspace.branch or 'unknown')}. "
            f"Changed files: {len(workspace.changed_files)}. "
            f"Untracked files: {len(workspace.untracked_files)}."
        )
        provider_summary = redact_secrets(provider.summary.strip() or "no summary")
        provider_context = f"Provider state: {provider_summary}."
        advisory_context = (
            f"Advisory reasoning:\n{redact_secrets(advisory.strip())}"
            if advisory is not None and advisory.strip()
            else "Advisory reasoning: unavailable."
        )
        evidence = (
            f"{phase_context}\n{criteria}\n{workspace_context}\n"
            f"{provider_context}\nProgress assessment: {assessment.state.value} "
            f"({redact_secrets(assessment.reason)})\n{advisory_context}"
        )

        instruction = self._instruction(decision.kind, assessment.state)
        prompt = (
            "You are the active coding agent in a controlled ULTRON CODE workflow.\n\n"
            f"{evidence}\n\n"
            f"Next step:\n{instruction}\n\n"
            "Work only within the configured repository/workspace. "
            "Report files changed, validation performed, blockers, and what remains."
        )
        return PromptProposal(
            provider=provider.provider,
            prompt=prompt,
            reason=decision.rationale,
            decision=decision.kind,
            phase_id=phase.id if phase is not None else None,
            requires_approval=decision.requires_approval,
        )

    @staticmethod
    def _instruction(decision: DecisionKind, state: ProgressState) -> str:
        if decision == DecisionKind.REQUEST_INPUT:
            return (
                "Stop making unrelated changes. Identify the exact blocker, the smallest "
                "information needed to resolve it, and ask the human for that information."
            )
        if decision == DecisionKind.ADVANCE_PHASE:
            return (
                "Summarize evidence that the current phase is complete and prepare the "
                "handoff to the next phase. Do not modify the phase state yourself."
            )
        if decision == DecisionKind.REVIEW:
            return (
                "Use the advisory reasoning as an input, then inspect the current repository "
                "state and your latest work. Determine the smallest concrete task needed to "
                "make measurable progress and validate it safely."
            )
        if state == ProgressState.PROGRESSING:
            return (
                "Continue the current implementation. Prefer the smallest coherent change, "
                "then validate it and report the resulting evidence."
            )
        return "Continue the active objective and report measurable progress or blockers."
