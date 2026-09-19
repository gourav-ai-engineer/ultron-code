from ultron.correlation import ProgressAssessment, ProgressState
from ultron.decision import Decision, DecisionKind
from ultron.models import Phase
from ultron.providers import ProviderKind, ProviderSnapshot
from ultron.synthesis import PromptSynthesizer
from ultron.workspace import WorkspaceSnapshot


def test_synthesizer_builds_provider_prompt() -> None:
    phase = Phase(
        id="phase-1",
        title="Implementation",
        objective="Implement the feature",
        acceptance_criteria=["Tests pass"],
    )
    provider = ProviderSnapshot(
        provider=ProviderKind.MOCK,
        session_id="session-1",
        summary="Working",
        progress=0.5,
    )
    workspace = WorkspaceSnapshot(
        root="/repo",
        branch="main",
        changed_files=("src/app.py",),
        untracked_files=(),
        git_available=True,
    )
    assessment = ProgressAssessment(
        state=ProgressState.PROGRESSING,
        reason="Workspace activity detected.",
        provider="mock",
        changed_file_count=1,
        reported_progress=0.5,
    )
    decision = Decision(DecisionKind.WAIT, "Progress is being detected.")

    proposal = PromptSynthesizer().synthesize(
        phase,
        provider,
        workspace,
        assessment,
        decision,
    )

    assert proposal.provider == ProviderKind.MOCK
    assert proposal.phase_id == "phase-1"
    assert "Implement the feature" in proposal.prompt
    assert "Tests pass" in proposal.prompt
    assert "src/app.py" not in proposal.prompt
    assert "Continue the current implementation" in proposal.prompt
