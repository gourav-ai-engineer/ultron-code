from ultron.loop import LoopConfig, WorkflowLoop
from ultron.providers import MockProvider
from ultron.workflow import WorkflowEngine
from ultron.workspace import WorkspaceObserver


def test_loop_respects_iteration_limit(tmp_path) -> None:
    loop = WorkflowLoop(
        WorkflowEngine(WorkspaceObserver(tmp_path)),
        MockProvider(summary="Working", progress=0.5),
        LoopConfig(interval_seconds=0.01, max_iterations=3),
    )

    runs = loop.run(lambda: True)

    assert len(runs) == 3
    assert len({run.run_id for run in runs}) == 3
