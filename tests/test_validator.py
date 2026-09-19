import subprocess

from ultron.executor import ActionExecutor
from ultron.safety import SafetyPolicy
from ultron.validator import Validator


def test_validator_stops_after_first_failure(tmp_path, monkeypatch) -> None:
    calls: list[list[str]] = []

    def fake_run(*args, **kwargs):
        calls.append(args[0])
        return subprocess.CompletedProcess(args=args[0], returncode=1, stdout="", stderr="failure")

    monkeypatch.setattr(subprocess, "run", fake_run)
    validator = Validator(
        ActionExecutor(
            tmp_path,
            safety_policy=SafetyPolicy(dry_run=False),
        )
    )

    report = validator.validate(("git status", "pytest"))

    assert report.passed is False
    assert len(report.results) == 1
    assert calls == [["git", "status"]]
