from ultron.providers import MockProvider
from ultron.run_store import RunStore
from ultron.workflow import WorkflowEngine
from ultron.workspace import WorkspaceObserver


def test_run_store_persists_and_rehydrates_latest_run(tmp_path) -> None:
    run = WorkflowEngine(WorkspaceObserver(tmp_path)).observe(
        MockProvider(summary="Working", progress=0.5),
        has_active_phase=True,
    )
    store = RunStore(tmp_path / "runs.jsonl")
    store.append(run)

    latest = store.latest()
    restored = store.latest_typed()

    assert latest is not None
    assert latest["run_id"] == run.run_id
    assert latest["stage"] == "decided"
    assert restored is not None
    assert restored.run_id == run.run_id
    assert restored.prompt.prompt == run.prompt.prompt
