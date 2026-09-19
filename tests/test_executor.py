import subprocess

import pytest

from ultron.executor import ActionExecutor, ExecutionDeniedError
from ultron.safety import SafetyPolicy


def test_executor_rejects_unallowlisted_commands(tmp_path) -> None:
    executor = ActionExecutor(tmp_path)

    with pytest.raises(ExecutionDeniedError, match="allowlist"):
        executor.execute("python -c print('unsafe')")


def test_executor_runs_allowlisted_git_command(tmp_path, monkeypatch) -> None:
    calls: list[dict[str, object]] = []

    def fake_run(*args, **kwargs):
        calls.append({"args": args, "kwargs": kwargs})
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

    result = executor.execute("git status")

    assert result.return_code == 0
    assert result.stdout == "clean"
    assert result.timed_out is False
    assert calls[0]["kwargs"]["cwd"] == tmp_path.resolve()
    assert calls[0]["kwargs"]["shell"] is False


def test_executor_respects_dry_run(tmp_path) -> None:
    executor = ActionExecutor(tmp_path, safety_policy=SafetyPolicy(dry_run=True))

    with pytest.raises(ExecutionDeniedError, match="Dry-run"):
        executor.execute("git status")
