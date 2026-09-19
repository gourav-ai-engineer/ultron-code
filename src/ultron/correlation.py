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
        elif any(token in summary for token in ("blocked", "error", "failed", "waiting")):
            state = ProgressState.BLOCKED
            reason = "Provider summary contains a blocking signal."
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
