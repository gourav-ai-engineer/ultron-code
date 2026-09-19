"""Advisory model reasoning for ULTRON CODE."""

from dataclasses import dataclass
from typing import Protocol

from .correlation import ProgressAssessment
from .decision import Decision
from .inference import GeminiInference, InferenceRequestError
from .models import Phase
from .providers import ProviderSnapshot
from .security import redact_secrets
from .workspace import WorkspaceSnapshot


@dataclass(frozen=True)
class ReasoningResult:
    """One advisory reasoning result."""

    provider: str
    model: str
    advice: str | None
    error: str | None = None


class Reasoner(Protocol):
    """Advisory reasoning contract; never executes external actions."""

    def advise(
        self,
        phase: Phase | None,
        provider: ProviderSnapshot,
        workspace: WorkspaceSnapshot,
        assessment: ProgressAssessment,
        decision: Decision,
    ) -> ReasoningResult: ...


@dataclass
class GeminiReasoner:
    """Use Gemini to recommend the smallest next development task."""

    inference: GeminiInference

    def advise(
        self,
        phase: Phase | None,
        provider: ProviderSnapshot,
        workspace: WorkspaceSnapshot,
        assessment: ProgressAssessment,
        decision: Decision,
    ) -> ReasoningResult:
        prompt = self._build_prompt(
            phase,
            provider,
            workspace,
            assessment,
            decision,
        )
        try:
            result = self.inference.generate(prompt)
        except InferenceRequestError as exc:
            return ReasoningResult(
                provider="gemini",
                model=self.inference.model,
                advice=None,
                error=str(exc),
            )
        return ReasoningResult(
            provider=result.provider,
            model=result.model,
            advice=result.text.strip()[:4000],
        )

    @staticmethod
    def _build_prompt(
        phase: Phase | None,
        provider: ProviderSnapshot,
        workspace: WorkspaceSnapshot,
        assessment: ProgressAssessment,
        decision: Decision,
    ) -> str:
        phase_text = (
            f"{phase.title} ({phase.id}): {redact_secrets(phase.objective)}"
            if phase is not None
            else "No active phase."
        )
        criteria = (
            "\n".join(
                f"- {redact_secrets(item)}"
                for item in phase.acceptance_criteria
            )
            if phase is not None and phase.acceptance_criteria
            else "Not configured."
        )
        return (
            "You are ULTRON CODE's advisory reasoning engine. "
            "Do not execute commands, change files, mutate phase state, expose secrets, "
            "or override deterministic safety decisions. Recommend only the smallest "
            "concrete software-development task that should happen next.\n\n"
            f"Phase: {phase_text}\n"
            f"Acceptance criteria:\n{criteria}\n"
            f"Provider summary: {redact_secrets(provider.summary.strip() or 'none')}\n"
            f"Progress state: {assessment.state.value}\n"
            f"Progress reason: {redact_secrets(assessment.reason)}\n"
            f"Workspace changed files: {len(workspace.changed_files)}\n"
            f"Workspace untracked files: {len(workspace.untracked_files)}\n"
            f"Deterministic decision: {decision.kind.value}\n"
            f"Decision rationale: {redact_secrets(decision.rationale)}\n\n"
            "Return exactly three labeled lines:\n"
            "TASK: the smallest next implementation/review task\n"
            "WHY: one-sentence reason grounded in the evidence\n"
            "VALIDATE: the safest concrete validation step\n"
        )
