import subprocess

import pytest

from ultron.executor import ActionExecutor
from ultron.models import Phase
from ultron.providers import MockProvider
from ultron.safety import SafetyPolicy
from ultron.workspace import WorkspaceObserver
from ultron.workflow import WorkflowEngine, WorkflowStage


def test_workflow_observe_creates_prompt_proposal(tmp_path) -> None:
    provider = MockProvider(summary="Working", progress=0.5, session_id="session-1")
    phase = Phase(
        id="phase-1",
        title="Implementation",
        objective="Implement the feature",
        acceptance_criteria=["Tests pass"],
    )
    engine = WorkflowEngine(WorkspaceObserver(tmp_path))

    run = engine.observe(provider, has_active_phase=True, phase=phase)

    assert run.run_id
    assert run.stage == WorkflowStage.DECIDED
    assert run.prompt.phase_id == "phase-1"
    assert "Implement the feature" in run.prompt.prompt
    assert run.assessment.state.value == "progressing"
    assert run.decision.kind.value == "wait"


def test_workflow_execute_reuses_run_id(tmp_path, monkeypatch) -> None:
    def fake_run(*args, **kwargs):
        return subprocess.CompletedProcess(
            args=["git", "status"],
            returncode=0,
            stdout="clean",
            stderr="",
        )

    monkeypatch.setattr(subprocess, "run", fake_run)
    executor = ActionExecutor(
        tmp_path,
        safety_policy=SafetyPolicy(dry_run=False),
    )
    engine = WorkflowEngine(
        WorkspaceObserver(tmp_path),
        executor=executor,
    )
    run = engine.observe(
        MockProvider(summary="Working", progress=0.5),
        has_active_phase=True,
    )

    completed = engine.execute(run, "git status")

    assert completed.stage == WorkflowStage.EXECUTED
    assert completed.execution is not None
    assert completed.execution.correlation_id == run.run_id
    assert completed.prompt == run.prompt


def test_workflow_requires_executor_for_execution(tmp_path) -> None:
    engine = WorkflowEngine(WorkspaceObserver(tmp_path))
    run = engine.observe(MockProvider(), has_active_phase=False)

    with pytest.raises(RuntimeError, match="no ActionExecutor"):
        engine.execute(run, "git status")
