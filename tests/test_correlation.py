from ultron.correlation import ProgressCorrelator, ProgressState
from ultron.providers import MockProvider
from ultron.workspace import WorkspaceSnapshot


def workspace(changed: tuple[str, ...] = ()) -> WorkspaceSnapshot:
    return WorkspaceSnapshot(
        root=".",
        branch="main",
        changed_files=changed,
        untracked_files=(),
        git_available=True,
    )


def test_progress_is_detected_from_workspace_changes() -> None:
    assessment = ProgressCorrelator().assess(
        MockProvider(summary="Working", progress=0.0).snapshot(),
        workspace(("src/app.py",)),
    )
    assert assessment.state == ProgressState.PROGRESSING
    assert assessment.changed_file_count == 1


def test_complete_provider_is_complete() -> None:
    assessment = ProgressCorrelator().assess(
        MockProvider(summary="Done", progress=1.0).snapshot(),
        workspace(),
    )
    assert assessment.state == ProgressState.COMPLETE


def test_blocking_summary_is_blocked() -> None:
    assessment = ProgressCorrelator().assess(
        MockProvider(summary="Blocked by missing credentials").snapshot(),
        workspace(),
    )
    assert assessment.state == ProgressState.BLOCKED
