from pathlib import Path

from ultron.audit import AuditLogger
from ultron.safety import SafetyPolicy


def test_audit_logger_round_trip(tmp_path: Path) -> None:
    logger = AuditLogger(tmp_path / "audit.jsonl")
    decision = SafetyPolicy(dry_run=True).evaluate("echo hello")

    event = logger.record(decision, correlation_id="run-1")
    events = logger.read_all()

    assert event.correlation_id == "run-1"
    assert len(events) == 1
    assert events[0].action == "echo hello"
    assert events[0].allowed is False
