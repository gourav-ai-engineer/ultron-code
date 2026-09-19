from ultron.control import ControlState
from ultron.providers import MockProvider
from ultron.recovery import RecoveryManager
from ultron.run_store import RunStore
from ultron.workflow import WorkflowEngine
from ultron.workspace import WorkspaceObserver


def test_recovery_allows_resume_when_not_stopped(tmp_path) -> None:
    store = RunStore(tmp_path / "runs.jsonl")
    run = WorkflowEngine(WorkspaceObserver(tmp_path)).observe(
        MockProvider(summary="Working", progress=0.5),
        has_active_phase=True,
    )
    store.append(run)

    state = RecoveryManager(store).inspect(ControlState())

    assert state.can_resume is True
    assert state.last_run_id == run.run_id
