from ultron.correlation import ProgressAssessment, ProgressState
from ultron.decision import Decision, DecisionKind
from ultron.inference import GeminiInference, InferenceRequestError
from ultron.models import Phase
from ultron.providers import MockProvider
from ultron.reasoning import GeminiReasoner, ReasoningResult
from ultron.workspace import WorkspaceSnapshot


def workspace() -> WorkspaceSnapshot:
    return WorkspaceSnapshot(
        root=".",
        branch="main",
        changed_files=(),
        untracked_files=(),
        git_available=True,
    )


def test_gemini_reasoner_builds_advisory() -> None:
    def poster(url, headers, payload):
        assert url.endswith("/models/gemini-test:generateContent")
        prompt = payload["contents"][0]["parts"][0]["text"]
        assert "Requirements and Architecture" in prompt
        assert "waiting for work" in prompt
        return {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {"text": "TASK: Review architecture\nWHY: Evidence supports review\nVALIDATE: run checks"}
                        ]
                    }
                }
            ]
        }

    reasoner = GeminiReasoner(
        GeminiInference(
            model="gemini-test",
            api_key="test-key",
            poster=poster,
        )
    )
    result = reasoner.advise(
        Phase(
            id="phase-1",
            title="Requirements and Architecture",
            objective="Clarify architecture",
            acceptance_criteria=["Architecture reviewed"],
        ),
        MockProvider(summary="Waiting for next task", progress=0.0).snapshot(),
        workspace(),
        assessment=ProgressAssessment(
            state=ProgressState.IDLE,
            reason="Provider explicitly reported that it is waiting for work.",
            provider="mock",
            changed_file_count=0,
            reported_progress=0.0,
        ),
        decision=Decision(
            DecisionKind.REVIEW,
            "Review current evidence.",
        ),
    )

    assert isinstance(result, ReasoningResult)
    assert result.provider == "gemini"
    assert result.model == "gemini-test"
    assert result.advice is not None
    assert result.advice.startswith("TASK:")


def test_reasoner_failure_is_non_fatal() -> None:
    def poster(url, headers, payload):
        raise InferenceRequestError("temporary provider failure")

    reasoner = GeminiReasoner(
        GeminiInference(
            model="gemini-test",
            api_key="test-key",
            poster=poster,
        )
    )
    result = reasoner.advise(
        None,
        MockProvider(summary="Waiting for next task", progress=0.0).snapshot(),
        workspace(),
        assessment=ProgressAssessment(
            state=ProgressState.IDLE,
            reason="idle",
            provider="mock",
            changed_file_count=0,
            reported_progress=0.0,
        ),
        decision=Decision(DecisionKind.REVIEW, "Review."),
    )

    assert result.advice is None
    assert result.error is not None
