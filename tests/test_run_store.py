from ultron.correlation import ProgressAssessment, ProgressState
from ultron.decision import Decision, DecisionKind
from ultron.models import Phase
from ultron.providers import MockProvider, ProviderKind, ProviderSnapshot
from ultron.synthesis import PromptSynthesizer
from ultron.workflow import WorkflowEngine
from ultron.workspace import WorkspaceObserver
from ultron.run_store import RunStore


def test_run_store_persists_latest_run(tmp_path) -> None:
    run = WorkflowEngine(WorkspaceObserver(tmp_path)).observe(
        MockProvider(summary="Working", progress=0.5),
        has_active_phase=True,
    )
    store = RunStore(tmp_path / "runs.jsonl")
    store.append(run)

    latest = store.latest()

    assert latest is not None
    assert latest["run_id"] == run.run_id
    assert latest["stage"] == "decided"
