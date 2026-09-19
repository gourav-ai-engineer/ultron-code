import subprocess

import pytest

from ultron.audit import AuditLogger
from ultron.executor import ActionExecutor, ExecutionDeniedError
from ultron.safety import SafetyPolicy


def test_executor_rejects_unallowlisted_commands(tmp_path) -> None:
    logger = AuditLogger(tmp_path / "audit.jsonl")
    executor = ActionExecutor(tmp_path, audit_logger=logger)

    with pytest.raises(ExecutionDeniedError, match="allowlist"):
        executor.execute("python -c print('unsafe')")

    events = logger.read_all()
    assert len(events) == 1
    assert events[0].status == "denied"
    assert events[0].correlation_id


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

    logger = AuditLogger(tmp_path / "audit.jsonl")
    monkeypatch.setattr(subprocess, "run", fake_run)
    executor = ActionExecutor(
        tmp_path,
        safety_policy=SafetyPolicy(dry_run=False),
        audit_logger=logger,
    )

    result = executor.execute("git status")

    assert result.return_code == 0
    assert result.stdout == "clean"
    assert result.timed_out is False
    assert result.correlation_id
    assert calls[0]["kwargs"]["cwd"] == tmp_path.resolve()
    assert calls[0]["kwargs"]["shell"] is False

    events = logger.read_all()
    assert [event.status for event in events] == ["approved", "completed"]
    assert events[0].correlation_id == result.correlation_id
    assert events[1].return_code == 0


def test_executor_respects_dry_run(tmp_path) -> None:
    logger = AuditLogger(tmp_path / "audit.jsonl")
    executor = ActionExecutor(
        tmp_path,
        safety_policy=SafetyPolicy(dry_run=True),
        audit_logger=logger,
    )

    with pytest.raises(ExecutionDeniedError, match="Dry-run"):
        executor.execute("git status")

    events = logger.read_all()
    assert len(events) == 1
    assert events[0].status == "denied"
    assert events[0].correlation_id


def test_executor_records_failed_commands(tmp_path, monkeypatch) -> None:
    def fake_run(*args, **kwargs):
        return subprocess.CompletedProcess(
            args=["git", "status"],
            returncode=2,
            stdout="",
            stderr="fatal",
        )

    logger = AuditLogger(tmp_path / "audit.jsonl")
    monkeypatch.setattr(subprocess, "run", fake_run)
    executor = ActionExecutor(
        tmp_path,
        safety_policy=SafetyPolicy(dry_run=False),
        audit_logger=logger,
    )

    result = executor.execute("git status")

    assert result.return_code == 2
    events = logger.read_all()
    assert events[-1].status == "failed"
    assert events[-1].return_code == 2
    assert "code 2" in events[-1].error
