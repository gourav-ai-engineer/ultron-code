"""Correlate provider feedback with workspace activity."""

from dataclasses import dataclass
from enum import StrEnum

from .providers import ProviderSnapshot
from .workspace import WorkspaceSnapshot


class ProgressState(StrEnum):
    PROGRESSING = "progressing"
    IDLE = "idle"
    BLOCKED = "blocked"
    COMPLETE = "complete"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class ProgressAssessment:
    state: ProgressState
    reason: str
    provider: str
    changed_file_count: int
    reported_progress: float | None


class ProgressCorrelator:
    """Produce deterministic, read-only progress assessments."""

    def assess(
        self,
        provider: ProviderSnapshot,
        workspace: WorkspaceSnapshot,
    ) -> ProgressAssessment:
        progress = provider.progress
        summary = provider.summary.lower()
        changed_count = len(workspace.changed_files) + len(workspace.untracked_files)

        if progress is not None and progress >= 1.0:
            state = ProgressState.COMPLETE
            reason = "Provider reported 100% progress."
        elif self._is_blocked_summary(summary):
            state = ProgressState.BLOCKED
            reason = "Provider summary contains an explicit blocking signal."
        elif self._is_idle_summary(summary):
            state = ProgressState.IDLE
            reason = "Provider explicitly reported that it is waiting for work."
        elif changed_count > 0 or (progress is not None and progress > 0):
            state = ProgressState.PROGRESSING
            reason = "Workspace activity or reported progress was detected."
        elif provider.summary.strip() or provider.session_id:
            state = ProgressState.IDLE
            reason = "A provider session exists but no progress signal was detected."
        else:
            state = ProgressState.UNKNOWN
            reason = "Insufficient provider and workspace signals."

        return ProgressAssessment(
            state=state,
            reason=reason,
            provider=provider.provider.value,
            changed_file_count=changed_count,
            reported_progress=progress,
        )

    @staticmethod
    def _is_blocked_summary(summary: str) -> bool:
        """Detect explicit blockers without treating normal waiting as a blocker."""
        blocking_signals = (
            "blocked",
            "cannot proceed",
            "can't proceed",
            "unable to proceed",
            "unable to continue",
            "failed",
            "error",
            "dependency missing",
            "missing dependency",
            "missing credentials",
            "requires human input",
            "needs human input",
            "awaiting user input",
            "waiting for user input",
            "blocked by",
        )
        return any(token in summary for token in blocking_signals)

    @staticmethod
    def _is_idle_summary(summary: str) -> bool:
        """Detect explicit idle/waiting-for-task states."""
        idle_signals = (
            "waiting for next task",
            "awaiting next task",
            "ready for next task",
            "waiting for instructions",
            "awaiting instructions",
            "ready for instructions",
            "idle",
            "standing by",
        )
        return any(token in summary for token in idle_signals)
