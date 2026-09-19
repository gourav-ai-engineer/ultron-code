from pathlib import Path

from ultron.audit import AuditLogger
from ultron.safety import SafetyPolicy


def test_audit_logger_round_trip(tmp_path: Path) -> None:
    logger = AuditLogger(tmp_path / "audit.jsonl")
    decision = SafetyPolicy(dry_run=True).evaluate("echo hello")

    event = logger.record(
        decision,
        correlation_id="run-1",
        return_code=1,
        error="Command exited with code 1.",
    )
    events = logger.read_all()

    assert event.correlation_id == "run-1"
    assert event.return_code == 1
    assert event.error == "Command exited with code 1."
    assert len(events) == 1
    assert events[0].action == "echo hello"
    assert events[0].allowed is False


def test_blocked_attempt_is_audited(tmp_path: Path) -> None:
    logger = AuditLogger(tmp_path / "audit.jsonl")

    event = logger.record_blocked("rm -rf build", "Blocked destructive operation.", "run-2")

    assert event.risk == "blocked"
    assert event.allowed is False
    assert event.status == "denied"
    assert event.correlation_id == "run-2"
